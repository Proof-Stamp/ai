# ProofStamp for Open WebUI

Status: **experimental adapter, ready for local end-to-end testing.** Do not list Open WebUI as verified public support until the real host flow has been tested.

This integration adds a **ProofStamp** Action button to Open WebUI. The model does not create the evidence package. The Action receives structured chat context from Open WebUI, builds the ProofStamp artifact itself, verifies the exact saved bytes with SHA-256, creates the detached receipt, and renders download + email handoff controls.

## Install for experimental testing

Open WebUI Functions execute server-side Python code with the privileges of the Open WebUI process. Review the source before installing it.

For testing, install an **immutable commit**, not mutable `main`:

1. Open **Admin Panel → Functions**.
2. Choose **Import From Link**.
3. Paste:

   `https://github.com/Proof-Stamp/ai/blob/1c8ae423e16e83c181eb4c6bf34063633fbdfcda/integrations/open-webui/proofstamp_action.py`

4. Review the Python source before saving.
5. Save the Function and enable it globally or for selected models.

After the integration has passed a real Open WebUI end-to-end test and is included in a tagged ProofStamp release, use the tagged release URL instead of a branch or `main` URL.

After installation, a **ProofStamp** Action appears in the message toolbar for chats where the Action is enabled.

## What the Action does

When the user clicks **ProofStamp** on a message, the adapter:

1. reads the structured `body["messages"]` context supplied by Open WebUI;
2. uses `body["id"]` as the capture boundary and includes only messages up to and including the message whose button was clicked;
3. records textual user/assistant/tool-style messages inside that selected-message scope;
4. excludes system/developer messages, private reasoning, binary/media message parts, attachments, and source/citation objects from this adapter version;
5. creates a schema-compatible `.proofstamp.json` session artifact;
6. writes the final artifact bytes to local temporary storage;
7. reads the saved bytes twice and compares two SHA-256 calculations;
8. uses those verified read-back bytes as the downloadable ProofStamp artifact;
9. creates the detached `.proofstamp.receipt.json` only after the exact-byte verification succeeds;
10. renders a persistent Rich UI result with **Download ProofStamp**, **Download detached receipt**, and **Email this ProofStamp**;
11. keeps the email recipient blank and never sends or uploads anything automatically.

The temporary server-side artifact is deleted after verification.

## Exact-byte delivery rule

The bytes offered through **Download ProofStamp** are the same bytes that were read back from temporary storage and independently verified before the receipt was created.

A regression test decodes the generated download data URL and confirms that its SHA-256 equals the detached receipt fingerprint.

## Trust classification

The adapter currently records:

`proofstamp.capture_method: "api_capture"`

This is the closest existing v1 capture-method classification because the admin-installed Action runs server-side and receives structured chat/model/session context from the authenticated Open WebUI host invocation. It does **not** mean the underlying model provider signed or authenticated the conversation.

Message IDs, timestamps, chat identifiers, and model identifiers are recorded only when Open WebUI explicitly supplies them. Provider metadata is recorded only when Open WebUI explicitly exposes a `provider` value to the Action.

Conversation coverage defaults to:

`not independently confirmed`

The Action receives the conversation context through the selected message, but it currently has no affirmative signal that the supplied message list represents every stored item in that declared scope. If the user chooses secret redaction, coverage becomes `partial` because known visible text was intentionally removed.

Messages after the selected message are outside the declared capture scope even if the host happened to include them in the Action payload.

## Sensitive-content handling

The conversation itself may contain sensitive information. The adapter performs a deliberately narrow high-confidence check for common API-token/private-key patterns.

If sensitive-looking material is detected, the Action asks whether to include it unchanged or create a redacted ProofStamp.

The confirmation is fail-closed:

- explicit `True` means include unchanged;
- explicit `False` means create the redacted ProofStamp;
- timeout, disconnect, error objects, or any unexpected response abort the capture and create no ProofStamp.

The Action applies its own bounded confirmation timeout rather than relying on Open WebUI's default indefinite event-call wait.

User-chosen redactions are recorded in `capture.redactions` and make conversation coverage `partial`.

This detector is only a warning aid, not a general secret scanner. Users remain responsible for reviewing what they preserve or share.

## Privacy and persistence

The Action does not access environment variables, browser storage, unrelated local files, the Open WebUI database, connectors, or external services.

Open WebUI Rich UI embeds are persistent. To keep the download controls available, this adapter embeds base64-encoded copies of the ProofStamp artifact and detached receipt in the Rich UI result. That means the ProofStamp result is stored with the Open WebUI chat in addition to the original conversation.

This is local to the Open WebUI installation unless that installation is separately backed up, exported, shared, or synchronized. The adapter does not send the session to ProofStamp.org or another external service.

## Files, images, and sources

Open WebUI's Action payload supplies conversation messages but does not directly include chat attachment bytes. Open WebUI documents separate chat/file APIs for reaching those files.

This first adapter intentionally does **not** call those APIs. It also does not export image/binary payloads or source/citation objects that may be attached to richer message structures. Those exclusions are recorded in the artifact limitations/omissions where applicable.

This keeps the first integration narrow and avoids silently expanding host access beyond the Action context needed for the ProofStamp.

## Resource limits

The Action applies configurable limits before expensive processing:

- approximate Action input size: 10,000,000 characters by default;
- generated ProofStamp artifact: 5,000,000 bytes by default;
- sensitive-content confirmation wait: 60 seconds by default.

If a limit is exceeded, the Action fails narrowly and does not fabricate a receipt.

## No external ProofStamp service

The core Action requires no ProofStamp account, API, database, blockchain, or upload.

The only external handoff it prepares is a user-controlled `mailto:` link containing the already verified filename, SHA-256, byte size, conversation-coverage wording, verification URL, and claim limitation. The Action does not send the email and does not claim the files are attached automatically.

## End-to-end test checklist

Before calling the integration verified, test it in a real Open WebUI instance and confirm:

- the ProofStamp Action button appears and runs;
- clicking an older message captures through that message and does not include later messages;
- the artifact download works and is valid UTF-8 JSON;
- the detached receipt download works;
- the SHA-256 in the receipt matches the exact downloaded artifact bytes;
- the byte size matches the downloaded artifact;
- conversation coverage is `not independently confirmed` for an ordinary unredacted chat;
- system/developer instructions and non-text binary/media payloads are not leaked into the artifact;
- a prompt-injection message cannot change `capture_method`, provenance, completeness, hashing, or delivery behavior;
- a disconnected or timed-out sensitive-content confirmation creates no ProofStamp;
- explicit redaction removes the detected test secret, records the redaction, and reports partial conversation coverage;
- the `Email this ProofStamp` link opens with a blank recipient and correct verified values;
- the fallback email text is present if the mailto link cannot be used;
- the Rich UI persistence disclosure is visible;
- no network request, upload, automatic email send, or provider-signed claim occurs.

After that passes, add Open WebUI to `proofstamp/references/PLATFORM-CAPABILITIES.md` and the public `/ai/` page as a verified integration.

## References

Open WebUI's official documentation describes Actions as admin-managed server-side Python Functions that add clickable buttons to chat messages. The Action method receives the conversation `messages`, `model`, `chat_id`, `session_id`, selected message `id`, and optional host context such as `__model__`, `__event_emitter__`, and `__event_call__`. Inline `HTMLResponse` results can be persisted as Rich UI embeds.

Open WebUI also documents that `__event_call__` waits indefinitely by default unless a timeout is configured, and that a disconnected client can return an error object. ProofStamp therefore treats only explicit boolean confirmation values as valid and applies its own timeout.

See:

- https://docs.openwebui.com/features/extensibility/plugin/functions/action/
- https://docs.openwebui.com/features/extensibility/plugin/functions/
- https://docs.openwebui.com/features/extensibility/plugin/development/events/
- https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/
