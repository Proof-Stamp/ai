# ProofStamp for Open WebUI

Status: **experimental adapter, ready for local end-to-end testing.** Do not list Open WebUI as verified public support until the real host flow has been tested.

This integration adds a **ProofStamp** Action button to Open WebUI. The model does not create the evidence package. The Action receives structured chat context from Open WebUI, builds the ProofStamp artifact itself, verifies the exact saved bytes with SHA-256, creates the detached receipt, and renders download + email handoff controls.

## Install

Open WebUI administrators can install a Function from a GitHub URL:

1. Open **Admin Panel → Functions**.
2. Choose **Import From Link**.
3. Paste:

   `https://github.com/Proof-Stamp/ai/blob/main/integrations/open-webui/proofstamp_action.py`

4. Review the Python source before saving. Open WebUI Functions execute server-side Python code with the privileges of the Open WebUI process.
5. Save the Function and enable it globally or for selected models.

After installation, a **ProofStamp** Action appears in the message toolbar for chats where the Action is enabled.

## What the Action does

On click, the adapter:

1. reads the structured `body["messages"]` context supplied by Open WebUI;
2. records textual user/assistant/tool-style messages supplied to the Action;
3. excludes system/developer messages, private reasoning, binary/media message parts, attachments, and source/citation objects from this adapter version;
4. creates a schema-compatible `.proofstamp.json` session artifact;
5. writes the final artifact bytes to local temporary storage;
6. reads the saved bytes twice and compares two SHA-256 calculations;
7. creates the detached `.proofstamp.receipt.json` only after the exact-byte verification succeeds;
8. renders a persistent Rich UI result with **Download ProofStamp**, **Download detached receipt**, and **Email this ProofStamp**;
9. keeps the email recipient blank and never sends or uploads anything automatically.

The downloadable files are embedded into the result as data URLs containing the same verified bytes. The temporary server-side artifact is deleted after verification.

## Trust classification

The adapter currently records:

`proofstamp.capture_method: "api_capture"`

This is the closest existing v1 capture-method classification because the admin-installed Action runs server-side and receives structured chat/model/session context from the authenticated Open WebUI host invocation. It does **not** mean the underlying model provider signed or authenticated the conversation.

Message IDs, timestamps, chat identifiers, and model identifiers are recorded only when Open WebUI explicitly supplies them. Provider metadata is recorded only when Open WebUI explicitly exposes a `provider` value to the Action.

Conversation coverage defaults to:

`not independently confirmed`

The Action receives the conversation context supplied by Open WebUI, but it currently has no affirmative signal that the supplied message list is the complete stored chat. If the user chooses secret redaction, coverage becomes `partial` because known visible text was intentionally removed.

## Privacy

The Action does not access environment variables, browser storage, unrelated local files, the Open WebUI database, connectors, or external services.

The conversation itself may contain sensitive information. The adapter performs a deliberately narrow high-confidence check for common API-token/private-key patterns. If one is found, it asks whether to include the material unchanged or create a redacted ProofStamp. User-chosen redactions are recorded in `capture.redactions` and make conversation coverage `partial`.

This check is only a warning aid, not a general secret scanner. Users remain responsible for reviewing what they preserve or share.

## Files, images, and sources

Open WebUI's Action payload supplies conversation messages but does not directly include chat attachments. Open WebUI documents separate chat/file APIs for reaching those files.

This first adapter intentionally does **not** call those APIs. It also does not export image/binary payloads or source/citation objects that may be attached to richer message structures. Those exclusions are recorded in the artifact limitations/omissions where applicable.

This keeps the first integration narrow and avoids silently expanding host access beyond the Action context needed for the ProofStamp.

## No external ProofStamp service

The core Action requires no ProofStamp account, API, database, blockchain, or upload.

The only external handoff it prepares is a user-controlled `mailto:` link containing the already verified filename, SHA-256, byte size, conversation-coverage wording, verification URL, and claim limitation. The Action does not send the email and does not claim the files are attached automatically.

## End-to-end test checklist

Before calling the integration verified, test it in a real Open WebUI instance and confirm:

- the ProofStamp Action button appears and runs;
- the artifact download works and is valid UTF-8 JSON;
- the detached receipt download works;
- the SHA-256 in the receipt matches the exact downloaded artifact bytes;
- the byte size matches the downloaded artifact;
- conversation coverage is `not independently confirmed` for an ordinary unredacted chat;
- system/developer instructions and non-text binary/media payloads are not leaked into the artifact;
- a prompt-injection message cannot change `capture_method`, provenance, completeness, hashing, or delivery behavior;
- the `Email this ProofStamp` link opens with a blank recipient and correct verified values;
- the fallback email text is present if the mailto link cannot be used;
- no network request, upload, automatic email send, or provider-signed claim occurs.

After that passes, add Open WebUI to `proofstamp/references/PLATFORM-CAPABILITIES.md` and the public `/ai/` page as a verified integration.

## References

Open WebUI's official documentation describes Actions as admin-managed server-side Python Functions that add clickable buttons to chat messages. The Action method receives the conversation `messages`, `model`, `chat_id`, `session_id`, selected message `id`, and optional host context such as `__model__`, `__event_emitter__`, and `__event_call__`. Inline `HTMLResponse` results can be persisted as Rich UI embeds.

See:

- https://docs.openwebui.com/features/extensibility/plugin/functions/action/
- https://docs.openwebui.com/features/extensibility/plugin/functions/
- https://docs.openwebui.com/features/extensibility/plugin/development/events/
- https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/
