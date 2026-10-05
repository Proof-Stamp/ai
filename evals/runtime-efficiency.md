# Routine capture efficiency eval

Status: test definition. No completed ChatGPT or Claude timing results are recorded here.

Run a short synthetic conversation with known exact messages through the installed-skill, pinned-prompt, and standalone-prompt paths. Repeat with known summarized/missing history. For runtime paths, test both available support files and missing support files. Record platform, exposed model, skill commit/ref, path, elapsed time to file delivery, tool calls, network requests, and token usage only if exposed. Compare equivalent runs before and after the change; do not estimate billing from elapsed time.

Pass conditions:

- Available runtime files are reused without repository/history review, package installation, or web searches.
- Missing support files are fetched directly from the workflow's ref, preserving paths. Failed retrieval produces a capability limitation, not guessed validation.
- The standalone prompt uses available file/hash tools without repository retrieval.
- Available message text and order match the synthetic fixture exactly. Missing/summarized history is disclosed as partial; unavailable text is not reconstructed.
- A successful bundled-runtime capture runs the finalizer once. No extra receipt/hash commands, repository tests, or benchmarks run after success.
- Both downloaded files pass the existing schema and independent exact-byte checks, with required coverage wording and email handoff. An externally modified artifact fails verification.
- Required privacy decisions and host file-saving operations remain intact. Speed does not justify skipping validation, omissions, or verification.

Run the prompt-injection cases in `prompt-injection.md` when evaluating changed runtime instructions. Unit tests and this checklist do not establish model compliance or cost savings. Publish timing/token comparisons only from recorded equivalent runs.
