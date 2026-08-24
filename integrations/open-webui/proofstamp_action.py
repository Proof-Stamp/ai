"""
title: ProofStamp
author: ProofStamp.org
author_url: https://proofstamp.org/
version: 0.1.1
license: Apache-2.0
description: Create a local ProofStamp artifact and verified detached receipt from Open WebUI chat context.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


VERIFY_URL = "https://email.proofstamp.org/verify"
ACTION_VERSION = "0.1.1"
ARTIFACT_SUFFIX = ".proofstamp.json"
RECEIPT_SUFFIX = ".proofstamp.receipt.json"
REDACTION_MARKER = "[REDACTED BY USER CHOICE]"

# Deliberately narrow, high-confidence patterns. This is a warning aid, not a
# general secret scanner.
_SECRET_PATTERNS = [
    re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
]

_PROTECTED_ROLES = {"system", "developer"}
_TEXT_PART_TYPES = {"text", "input_text", "output_text"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _safe_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _evidence(value: Any, provenance: str, *, note: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"value": value, "provenance": provenance}
    if note:
        result["note"] = note
    return result


def _unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "provenance": "unavailable", "reason": reason}


def _excluded(reason: str) -> dict[str, str]:
    return {"status": "excluded", "provenance": "excluded", "reason": reason}


def _extract_text_content(content: Any) -> tuple[str, int]:
    """Return textual message content and count omitted non-text parts."""
    if isinstance(content, str):
        return content, 0

    if isinstance(content, list):
        parts: list[str] = []
        omitted = 0
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                item_type = item.get("type")
                text_value = item.get("text")
                if item_type in _TEXT_PART_TYPES and isinstance(text_value, str):
                    parts.append(text_value)
                elif item_type is None and isinstance(text_value, str):
                    parts.append(text_value)
                else:
                    omitted += 1
                continue
            omitted += 1
        return "\n".join(parts), omitted

    if isinstance(content, dict):
        text_value = content.get("text")
        if isinstance(text_value, str):
            return text_value, 0
        return "", 1

    if content is None:
        return "", 0

    return str(content), 0


def _has_sensitive_material(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _redact_sensitive_material(text: str) -> tuple[str, int]:
    redacted = text
    count = 0
    for pattern in _SECRET_PATTERNS:
        redacted, substitutions = pattern.subn(REDACTION_MARKER, redacted)
        count += substitutions
    return redacted, count


def _selected_messages(body: dict[str, Any]) -> list[Any]:
    """Return only messages through the message whose Action button was clicked."""
    raw_messages = body.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("Open WebUI did not supply any conversation messages to the Action")

    selected_id = _safe_string(body.get("id"))
    if not selected_id:
        raise ValueError("Open WebUI did not supply the selected message id")

    matches: list[int] = []
    for index, raw in enumerate(raw_messages):
        if isinstance(raw, dict) and _safe_string(raw.get("id")) == selected_id:
            matches.append(index)

    if not matches:
        raise ValueError("Selected Open WebUI message id was not present in the supplied message list")
    if len(matches) != 1:
        raise ValueError("Selected Open WebUI message id was ambiguous in the supplied message list")

    return raw_messages[: matches[0] + 1]


def _ensure_input_within_limit(value: Any, limit_chars: int) -> int:
    """Bound additional processing without serializing/copying the whole request."""
    total = 0
    stack = [value]
    seen: set[int] = set()

    while stack:
        current = stack.pop()
        if isinstance(current, str):
            total += len(current)
        elif isinstance(current, (bytes, bytearray)):
            total += len(current)
        elif isinstance(current, dict):
            identity = id(current)
            if identity in seen:
                continue
            seen.add(identity)
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (list, tuple, set)):
            identity = id(current)
            if identity in seen:
                continue
            seen.add(identity)
            stack.extend(current)
        else:
            total += 16

        if total > limit_chars:
            raise ValueError(
                f"Open WebUI Action input exceeds the configured {limit_chars}-character processing limit"
            )

    return total


def _model_value(body: dict[str, Any]) -> str | None:
    model = body.get("model")
    if isinstance(model, str) and model.strip():
        return model
    if isinstance(model, dict):
        for key in ("id", "name"):
            value = _safe_string(model.get(key))
            if value:
                return value
    return None


def _provider_value(model_context: Any) -> str | None:
    if isinstance(model_context, dict):
        return _safe_string(model_context.get("provider"))
    return None


def _message_timestamp(message: dict[str, Any]) -> dict[str, Any] | None:
    if "timestamp" not in message or message.get("timestamp") is None:
        return None
    return _evidence(message.get("timestamp"), "host_exposed")


def _build_session_artifact(
    body: dict[str, Any],
    *,
    model_context: Any = None,
    redact_sensitive: bool = False,
    included_sensitive_unchanged: bool = False,
) -> tuple[dict[str, Any], dict[str, int]]:
    raw_messages = _selected_messages(body)

    messages: list[dict[str, Any]] = []
    redactions: list[dict[str, str]] = []
    protected_count = 0
    non_text_parts = 0
    sensitive_redaction_count = 0

    for raw in raw_messages:
        if not isinstance(raw, dict):
            non_text_parts += 1
            continue

        role = _safe_string(raw.get("role")) or "unknown"
        if role.lower() in _PROTECTED_ROLES:
            protected_count += 1
            continue

        content, omitted_parts = _extract_text_content(raw.get("content"))
        non_text_parts += omitted_parts

        sequence = len(messages) + 1
        if redact_sensitive:
            content, replacements = _redact_sensitive_material(content)
            if replacements:
                sensitive_redaction_count += replacements
                redactions.append(
                    {
                        "location": f"session.messages[{sequence - 1}].content",
                        "reason": "user_requested_secret_redaction",
                    }
                )

        message: dict[str, Any] = {
            "sequence": sequence,
            "role": role,
            "content": content,
            "provenance": "host_exposed",
        }
        message_id = _safe_string(raw.get("id"))
        if message_id:
            message["message_id"] = message_id
        timestamp = _message_timestamp(raw)
        if timestamp:
            message["timestamp"] = timestamp
        messages.append(message)

    if not messages:
        raise ValueError("No exportable conversation messages remained after protected-role exclusions")

    generated_at = utc_now()
    chat_id = _safe_string(body.get("chat_id"))
    host_session_id = _safe_string(body.get("session_id"))
    selected_message_id = _safe_string(body.get("id"))
    model = _model_value(body)
    provider = _provider_value(model_context)

    extra_metadata: list[dict[str, Any]] = []
    if host_session_id:
        extra_metadata.append(
            {
                "name": "open_webui_session_id",
                "evidence": _evidence(host_session_id, "host_exposed"),
            }
        )
    if selected_message_id:
        extra_metadata.append(
            {
                "name": "selected_message_id",
                "evidence": _evidence(selected_message_id, "host_exposed"),
            }
        )

    omissions: list[dict[str, str]] = []
    if protected_count:
        omissions.append(
            {
                "category": "protected_instructions",
                "reason": f"Excluded {protected_count} system/developer message(s) from the exported conversation by design.",
            }
        )
    if non_text_parts:
        omissions.append(
            {
                "category": "non_text_message_content",
                "reason": f"Excluded {non_text_parts} non-text/binary/media message part(s); v1 exports textual conversation content only.",
            }
        )

    warnings: list[str] = []
    if included_sensitive_unchanged:
        warnings.append(
            "Sensitive-looking credential or private-key content was included unchanged after explicit user confirmation."
        )

    if redactions:
        completeness = {
            "status": "partial",
            "basis": "The user chose to redact sensitive-looking material before export, so the artifact is not a complete capture of the original visible text within the selected-message scope.",
            "provenance": "derived",
        }
    else:
        completeness = {
            "status": "unknown",
            "basis": "Open WebUI supplied conversation context through the selected message, but the adapter received no affirmative signal that this represented every stored item within that scope.",
            "provenance": "derived",
        }

    artifact: dict[str, Any] = {
        "proofstamp": {
            "format": "proofstamp-session",
            "format_version": "1.0",
            "generator": f"ProofStamp Open WebUI Action {ACTION_VERSION}",
            "capture_method": "api_capture",
        },
        "session": {
            "platform": _evidence(
                "Open WebUI",
                "derived",
                note="Captured by the ProofStamp Open WebUI Action adapter.",
            ),
            "messages": messages,
        },
        "environment": {
            "provider": (
                _evidence(provider, "host_exposed")
                if provider
                else _unavailable("provider_not_explicitly_exposed_to_action")
            ),
            "model": (
                _evidence(model, "host_exposed")
                if model
                else _unavailable("model_not_exposed_to_action")
            ),
            "client": _evidence("Open WebUI", "derived"),
            "harness": _evidence("Open WebUI Action Function", "derived"),
            "ui_settings": [],
            "accessible_instructions": [],
            "system_prompt": _excluded("system_and_developer_instructions_not_exported_by_adapter"),
            "private_reasoning": _excluded("not_part_of_proofstamp_capture"),
            "extra_metadata": extra_metadata,
        },
        "sources": [],
        "attachments": [],
        "capture": {
            "generated_at": _evidence(generated_at, "derived"),
            "scope": [
                "Textual Open WebUI conversation messages supplied to this Action, up to and including the message whose ProofStamp button was clicked, excluding system/developer instructions and binary/media payloads.",
                "Open WebUI chat, message, and model identifiers explicitly supplied to this Action.",
            ],
            "completeness": completeness,
            "omissions": omissions,
            "redactions": redactions,
        },
        "limitations": [
            "Conversation coverage is not independently confirmed unless a recorded redaction makes the selected-message scope known to be partial.",
            "Messages after the selected message are outside this capture scope even if the host supplied them to the Action.",
            "System/developer instructions and private reasoning are not exported.",
            "Attachments, file bytes, images, and source/citation objects are not exported by this Action version.",
            "Model and provider metadata are recorded only when Open WebUI explicitly supplies them; they are not provider-signed evidence.",
            "A matching SHA-256 identifies the exact artifact bytes; it does not prove truth, authorship, provider authenticity, or when the underlying conversation originally occurred.",
        ],
    }

    if chat_id:
        artifact["session"]["session_id"] = _evidence(chat_id, "host_exposed")

    if warnings:
        artifact["capture"]["warnings"] = warnings

    return artifact, {
        "protected_count": protected_count,
        "non_text_parts": non_text_parts,
        "sensitive_redaction_count": sensitive_redaction_count,
    }


def _verify_exact_saved_bytes(artifact_bytes: bytes) -> tuple[bytes, str, int]:
    """Return the exact verified read-back bytes, digest, and byte size."""
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", delete=False, prefix="proofstamp-", suffix=".json"
        ) as handle:
            handle.write(artifact_bytes)
            handle.flush()
            os.fsync(handle.fileno())
            temp_name = handle.name

        path = Path(temp_name)
        first_bytes = path.read_bytes()
        first_hash = hashlib.sha256(first_bytes).hexdigest()
        first_size = len(first_bytes)

        parsed = json.loads(first_bytes.decode("utf-8"))
        if parsed.get("proofstamp", {}).get("format") != "proofstamp-session":
            raise ValueError("saved artifact does not have ProofStamp session format metadata")
        if parsed.get("proofstamp", {}).get("format_version") != "1.0":
            raise ValueError("saved artifact does not have ProofStamp session format version 1.0")

        second_bytes = path.read_bytes()
        second_hash = hashlib.sha256(second_bytes).hexdigest()
        second_size = len(second_bytes)

        if (
            first_hash != second_hash
            or first_size != second_size
            or first_bytes != second_bytes
        ):
            raise RuntimeError("independent exact-byte verification failed")

        return second_bytes, second_hash, second_size
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass


def _receipt(artifact_filename: str, sha256: str, size_bytes: int) -> dict[str, Any]:
    return {
        "proofstamp": {"format": "proofstamp-receipt", "format_version": "1.0"},
        "artifact": {
            "filename": artifact_filename,
            "size_bytes": size_bytes,
            "format": "proofstamp-session",
            "format_version": "1.0",
        },
        "fingerprint": {"algorithm": "SHA-256", "sha256": sha256},
        "verification": {
            "verified": True,
            "recalculated_sha256": sha256,
            "method": "Wrote the final artifact bytes to local temporary storage, read the saved bytes twice, parsed the saved JSON between reads, compared both SHA-256 calculations, and delivered the verified read-back bytes.",
        },
        "created_at": {"value": utc_now(), "provenance": "derived"},
        "limitations": [
            "This receipt identifies the exact bytes of the referenced session artifact. It does not authenticate the AI provider or prove session completeness.",
            "The receipt creation time is a local generation time and is not external timestamp evidence.",
        ],
    }


def _coverage_label(artifact: dict[str, Any]) -> str:
    status = artifact["capture"]["completeness"]["status"]
    return {
        "complete": "confirmed for recorded scope",
        "partial": "partial",
        "unknown": "not independently confirmed",
    }[status]


def _mailto(artifact_filename: str, sha256: str, size_bytes: int, coverage: str) -> str:
    body = "\n".join(
        [
            f"Filename: {artifact_filename}",
            f"SHA-256: {sha256}",
            f"Byte size: {size_bytes}",
            "Hash verified locally: yes",
            f"Conversation coverage: {coverage}",
            "Keep the original artifact and detached receipt.",
            "A matching SHA-256 later shows exact-byte identity but does not prove when the underlying AI conversation originally occurred.",
            VERIFY_URL,
        ]
    )
    query = urlencode(
        {"subject": f"ProofStamp: {artifact_filename}", "body": body},
        quote_via=quote,
        safe="",
    )
    return f"mailto:?{query}"


def _fallback_email_text(
    artifact_filename: str, sha256: str, size_bytes: int, coverage: str
) -> str:
    return "\n".join(
        [
            "To: ",
            f"Subject: ProofStamp: {artifact_filename}",
            "",
            f"Filename: {artifact_filename}",
            f"SHA-256: {sha256}",
            f"Byte size: {size_bytes}",
            "Hash verified locally: yes",
            f"Conversation coverage: {coverage}",
            "Keep the original artifact and detached receipt.",
            "A matching SHA-256 later shows exact-byte identity but does not prove when the underlying AI conversation originally occurred.",
            VERIFY_URL,
        ]
    )


def _safe_filename(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    stamp = current.strftime("%Y-%m-%d-%H%M%S")
    return f"open-webui-session-{stamp}{ARTIFACT_SUFFIX}"


def _receipt_filename(artifact_filename: str) -> str:
    if not artifact_filename.endswith(ARTIFACT_SUFFIX):
        raise ValueError("artifact filename must end with .proofstamp.json")
    return artifact_filename[: -len(ARTIFACT_SUFFIX)] + RECEIPT_SUFFIX


def _data_uri(payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:application/json;base64,{encoded}"


def _render_result_html(
    *,
    artifact_filename: str,
    artifact_bytes: bytes,
    receipt_filename: str,
    receipt_bytes: bytes,
    sha256: str,
    size_bytes: int,
    coverage: str,
    mailto: str,
    fallback_email: str,
) -> str:
    artifact_href = html.escape(_data_uri(artifact_bytes), quote=True)
    receipt_href = html.escape(_data_uri(receipt_bytes), quote=True)
    mailto_href = html.escape(mailto, quote=True)
    artifact_name = html.escape(artifact_filename)
    receipt_name = html.escape(receipt_filename)
    digest = html.escape(sha256)
    coverage_html = html.escape(coverage)
    fallback_html = html.escape(fallback_email)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 14px; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .card {{ border: 1px solid rgba(127,127,127,.28); border-radius: 14px; padding: 16px; max-width: 760px; }}
  h3 {{ margin: 0 0 8px; font-size: 18px; }}
  p {{ margin: 6px 0; line-height: 1.4; }}
  .meta {{ margin-top: 10px; font-size: 13px; opacity: .88; }}
  code {{ overflow-wrap: anywhere; }}
  .actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 8px; }}
  a.btn {{ display: inline-block; text-decoration: none; border: 1px solid currentColor; border-radius: 9px; padding: 8px 11px; font-weight: 650; }}
  details {{ margin-top: 10px; font-size: 13px; }}
  pre {{ white-space: pre-wrap; overflow-wrap: anywhere; padding: 10px; border-radius: 8px; background: rgba(127,127,127,.10); }}
  .small {{ font-size: 12px; opacity: .75; }}
</style>
</head>
<body>
<div class="card">
  <h3>ProofStamp created</h3>
  <p><strong>Hash verified: yes</strong></p>
  <div class="meta">
    <p>Artifact: <code>{artifact_name}</code></p>
    <p>SHA-256: <code>{digest}</code></p>
    <p>Bytes: {size_bytes}</p>
    <p>Conversation coverage: {coverage_html}</p>
  </div>
  <div class="actions">
    <a class="btn" href="{artifact_href}" download="{artifact_name}">Download ProofStamp</a>
    <a class="btn" href="{receipt_href}" download="{receipt_name}">Download detached receipt</a>
    <a class="btn" href="{mailto_href}">Email this ProofStamp</a>
  </div>
  <p class="small">Keep both files. The email link does not attach them automatically.</p>
  <p class="small">This embedded result is stored with the Open WebUI chat and contains encoded copies of both download files.</p>
  <details>
    <summary>If the email button does not open</summary>
    <pre>{fallback_html}</pre>
  </details>
  <p class="small">A matching SHA-256 shows exact-byte identity. It does not prove truth, provider authentication, completeness beyond the recorded assessment, or when the underlying conversation originally occurred.</p>
</div>
<script>
function reportHeight() {{
  const h = document.documentElement.scrollHeight;
  parent.postMessage({{ type: 'iframe:height', height: h }}, '*');
}}
window.addEventListener('load', reportHeight);
if (window.ResizeObserver) new ResizeObserver(reportHeight).observe(document.body);
</script>
</body>
</html>"""


def _sensitive_in_body(body: dict[str, Any]) -> bool:
    for raw in _selected_messages(body):
        if not isinstance(raw, dict):
            continue
        role = _safe_string(raw.get("role")) or "unknown"
        if role.lower() in _PROTECTED_ROLES:
            continue
        text, _ = _extract_text_content(raw.get("content"))
        if _has_sensitive_material(text):
            return True
    return False


def _interpret_sensitive_confirmation(result: Any) -> str:
    """Return include/redact only for explicit boolean user responses."""
    if result is True:
        return "include"
    if result is False:
        return "redact"
    raise ValueError(
        "Sensitive-content confirmation did not complete with an explicit user choice"
    )


class Action:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Button order; lower appears earlier.")
        max_input_chars: int = Field(
            default=10_000_000,
            ge=10_000,
            le=50_000_000,
            description="Maximum approximate Action input size processed by ProofStamp.",
        )
        max_artifact_bytes: int = Field(
            default=5_000_000,
            ge=10_000,
            le=25_000_000,
            description="Maximum ProofStamp artifact size before the Action fails narrowly.",
        )
        confirmation_timeout_seconds: int = Field(
            default=60,
            ge=5,
            le=600,
            description="Maximum wait for explicit confirmation when sensitive-looking content is detected.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
        __model__=None,
        **kwargs,
    ):
        async def emit_status(description: str, *, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": description, "done": done}}
                )

        async def emit_error(message: str) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "notification", "data": {"type": "error", "content": message}}
                )

        try:
            await emit_status("Creating ProofStamp…")
            _ensure_input_within_limit(body, self.valves.max_input_chars)

            redact_sensitive = False
            included_sensitive_unchanged = False
            if _sensitive_in_body(body):
                if not __event_call__:
                    raise ValueError(
                        "Sensitive-looking material was detected, but this host did not expose an interactive confirmation channel. No ProofStamp was created."
                    )
                try:
                    response = await asyncio.wait_for(
                        __event_call__(
                            {
                                "type": "confirmation",
                                "data": {
                                    "title": "Sensitive-looking content detected",
                                    "message": (
                                        "This conversation appears to contain a credential, token, or private key. "
                                        "Continue to include it unchanged? Choose Cancel to create a redacted ProofStamp instead."
                                    ),
                                },
                            }
                        ),
                        timeout=self.valves.confirmation_timeout_seconds,
                    )
                except asyncio.TimeoutError as exc:
                    raise ValueError(
                        "Sensitive-content confirmation timed out. No ProofStamp was created."
                    ) from exc

                choice = _interpret_sensitive_confirmation(response)
                if choice == "include":
                    included_sensitive_unchanged = True
                else:
                    redact_sensitive = True

            artifact, _stats = _build_session_artifact(
                body,
                model_context=__model__,
                redact_sensitive=redact_sensitive,
                included_sensitive_unchanged=included_sensitive_unchanged,
            )
            artifact_bytes = _json_bytes(artifact)
            if len(artifact_bytes) > self.valves.max_artifact_bytes:
                raise ValueError(
                    f"ProofStamp artifact is {len(artifact_bytes)} bytes, above the configured {self.valves.max_artifact_bytes}-byte limit"
                )

            artifact_filename = _safe_filename()
            verified_artifact_bytes, sha256, size_bytes = _verify_exact_saved_bytes(
                artifact_bytes
            )

            receipt = _receipt(artifact_filename, sha256, size_bytes)
            receipt_bytes = _json_bytes(receipt)
            receipt_filename = _receipt_filename(artifact_filename)
            coverage = _coverage_label(artifact)
            mailto = _mailto(artifact_filename, sha256, size_bytes, coverage)
            fallback_email = _fallback_email_text(
                artifact_filename, sha256, size_bytes, coverage
            )

            result_html = _render_result_html(
                artifact_filename=artifact_filename,
                artifact_bytes=verified_artifact_bytes,
                receipt_filename=receipt_filename,
                receipt_bytes=receipt_bytes,
                sha256=sha256,
                size_bytes=size_bytes,
                coverage=coverage,
                mailto=mailto,
                fallback_email=fallback_email,
            )
            await emit_status("ProofStamp created and exact bytes verified.", done=True)
            return HTMLResponse(
                content=result_html,
                headers={"Content-Disposition": "inline"},
            )
        except Exception as exc:
            await emit_error(f"ProofStamp could not be created: {exc}")
            await emit_status("ProofStamp failed.", done=True)
            return None
