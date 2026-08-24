# ChatGPT platform profile

Status: verified platform profile
Last verified: 2026-08-24

This profile describes ProofStamp behavior for the consumer ChatGPT product. It supplements `../PLATFORM-CAPABILITIES.md`; the generic ProofStamp trust model, schemas, privacy rules, and capability checks remain authoritative.

## Recommended user flow

For occasional use, use the pinned ProofStamp prompt from `PROMPT.md` and ask:

`ProofStamp this session.`

For repeated use, a private ChatGPT Project may hold ProofStamp-specific project instructions. Projects are available across free and paid ChatGPT subscription types and support project instructions, files, chats, and ChatGPT tools.

Source: https://help.openai.com/en/articles/10169521

## Capture method

Default consumer-chat capture should use:

`capture_method: "ai_generated"`

unless ProofStamp is operating from a stronger host/API/export mechanism that independently exposes the conversation record.

The model seeing messages in its current context is not, by itself, host-authenticated evidence that the visible conversation is complete.

## Conversation visibility and completeness

Default:

`capture.completeness.status: "unknown"`

Use `complete` only when affirmative host/API/export/capture evidence establishes that every item inside the declared capture scope was available and included.

Use `partial` when the host or capture process makes it known that in-scope history is missing, truncated, summarized, failed to load, or otherwise omitted.

Do not upgrade completeness merely because ChatGPT appears able to recall or display the whole conversation.

### Optional shared-link evidence

ChatGPT shared links created from the chat-level Share control include a snapshot of the conversation up to the point the link is shared. If a response is still generating, the snapshot may stop at the latest completed visible message. A share action on an individual assistant response may be scoped only to that response.

A chat-level shared link can therefore be recorded as optional supporting host evidence about the shared snapshot. It is not provider-signed evidence, does not prove the truth of the content, and does not prove when the underlying conversation originally occurred.

Privacy warning: anyone with the shared link can view the linked conversation. ProofStamp must never create or publish a shared link automatically. The user must choose to create it.

Source: https://help.openai.com/en/articles/7925741-chatgpt-shared-links-faq

## File creation and persistence

ChatGPT supports uploaded and created files. Where Library is available, files uploaded to or created in ChatGPT are saved to Library and can be downloaded later.

This supports the artifact-delivery part of ProofStamp when the current ChatGPT surface can create a downloadable `.proofstamp.json` file.

Library availability or persistence does not itself establish that ProofStamp hashed the exact saved bytes. Exact-byte readback and hashing must still be verified separately in the active environment.

Temporary Chat is a special case: uploaded files are not saved to the user's account or Library. Treat persistence conservatively in Temporary Chat.

Source: https://help.openai.com/en/articles/20001052-library-for-chatgpt

## Exact-byte hashing

For some data-analysis tasks, ChatGPT runs Python in a stateful Jupyter notebook environment and can use files made available to the session.

When the active ChatGPT environment provides Python/file access that allows ProofStamp to:

1. write the final artifact;
2. read back the exact saved bytes;
3. compute SHA-256;
4. independently recalculate SHA-256 from the saved file;

then ProofStamp may complete the normal verified detached-receipt workflow.

If any of those capabilities is unavailable on the current surface, plan, model, or workspace, downgrade according to `../PLATFORM-CAPABILITIES.md`. Do not infer exact-byte verification merely from the presence of a Python tool.

Source: https://help.openai.com/en/articles/8437071/data-analysis-with-chatgpt

## Sources and web results

Record only sources actually consulted during the session. When ChatGPT exposes citations, URLs, document references, or tool results, preserve only the fields legitimately available to the capture process and assign provenance according to the generic platform-capability rules.

Do not browse additional sources during capture merely to make the ProofStamp source list more complete.

## Attachments

If the active environment exposes exact attachment bytes through an authorized file capability, ProofStamp may hash them and record the attachment SHA-256.

If only filename or metadata is exposed, record only that metadata and mark the attachment hash unavailable or unverified as appropriate.

Library presence does not authorize ProofStamp to retrieve unrelated files. Only use files legitimately made available for the current task.

## Provider, model, and session metadata

Do not treat ChatGPT's own textual self-identification as provider-authenticated metadata.

Use:

- `host_exposed` only for values independently exposed by the host to the capture process;
- `model_reported` for the model's own claim about model/provider identity;
- `user_provided` for values asserted by the user;
- `tool_result` for values returned by an authorized tool or connector.

Do not invent a stable ChatGPT session ID, message ID, timestamp, model identifier, UI setting, or plan name when the host does not expose it.

## Provider authentication

Default consumer ChatGPT ProofStamp evidence is not provider-signed.

A ChatGPT shared link is supporting host evidence for the linked snapshot, not a cryptographic provider signature over the ProofStamp artifact.

Do not claim OpenAI or ChatGPT certified, notarized, authenticated, or signed the captured transcript unless a separate authenticated mechanism actually supports that claim.

## Email handoff

After successful exact-byte verification, follow the normal ProofStamp requirement to provide `Email this ProofStamp` or the pre-filled email-text fallback.

Do not send email automatically. Do not claim a `mailto:` link attaches the artifact or receipt.

## Capability summary

| Capability | ChatGPT guidance |
| --- | --- |
| Conversation capture | Available to the model for currently exposed context; default capture is `ai_generated` |
| Completeness evidence | Default `unknown`; chat-level shared snapshot can provide optional supporting evidence for the shared scope |
| Downloadable file creation | Supported on capable ChatGPT surfaces |
| Exact saved-byte readback | Capability-dependent; must be verified at runtime |
| SHA-256 | Available when the active environment provides suitable Python/file access or another trustworthy exact-byte hashing path |
| Generated-file persistence | Library supports saved created files where available |
| Source/citation access | Capture only citations and source metadata actually exposed in the session |
| Attachment bytes | Capability-dependent and permission-bound |
| Provider-signed transcript | Not established by normal consumer ChatGPT capture |
| Email handoff | User-controlled `mailto:` or text fallback after verification |

## Evidence-strength ordering for ChatGPT

From weaker to stronger capture provenance:

1. AI-generated capture of currently available conversation context.
2. AI-generated capture plus optional chat-level shared-link snapshot reference.
3. A future host/API/export integration that supplies the conversation record directly to the capture process.
4. Provider-signed evidence, if OpenAI ever exposes such a mechanism and ProofStamp separately verifies it.

Do not collapse these levels into a single `verified` authenticity claim. SHA-256 verification establishes integrity of the saved ProofStamp artifact, not provider authentication of the conversation.
