# Release preparation

Target: **`v0.1.3` pre-release**

This is a small post-release hardening release. It makes the user-controlled email handoff part of every successful exact-byte-verified ProofStamp delivery and prepares the public repository for skill-directory discovery.

## Release blockers

Do not tag or publish the release until all unchecked items below are complete.

- [x] Skill metadata is `0.1.3` on `main`.
- [x] PR #7 is merged: required email handoff after successful exact-byte verification.
- [x] PR #8 is merged: directory-ready README and one-command `skills` CLI install instructions.
- [x] GitHub Actions `tests` passed on the PR #8 head.
- [ ] GitHub Actions `tests` passes on the final `main` commit selected for the tag.
- [ ] Run one fresh-host delivery smoke test and confirm a successful verified delivery includes either the clickable `Email this ProofStamp` link or the pre-filled email text fallback.
- [ ] Create tag `v0.1.3` from the exact tested `main` commit.
- [ ] Publish the GitHub pre-release.
- [ ] Run a post-release install smoke test from the public repository/tag with the `skills` CLI.
- [ ] After the tag exists, pin the short prompt in `PROMPT.md` from `v0.1.2` to `v0.1.3` in a separate post-release housekeeping PR.

## Proposed tag

```text
v0.1.3
```

The Agent Skill metadata in `proofstamp/SKILL.md` is `0.1.3` and must remain so at the tagged commit.

## Proposed release title

```text
ProofStamp AI v0.1.3 — required email handoff
```

## Proposed release notes

ProofStamp AI v0.1.3 is a focused delivery-contract hardening release.

### What changed

After a ProofStamp artifact is successfully exact-byte verified, the delivery must now include all of the following:

- downloadable `.proofstamp.json` artifact;
- downloadable detached `.proofstamp.receipt.json` receipt;
- artifact filename;
- SHA-256;
- byte size;
- hash verification status;
- capture completeness: `complete`, `partial`, or `unknown`;
- user-controlled email handoff.

The preferred handoff is a clickable **Email this ProofStamp** `mailto:` link. If the host cannot render a clickable mailto link, it must provide the pre-filled email text instead. A successful verified delivery must never silently omit both.

The email handoff contains the artifact filename, SHA-256, byte size, `Hash verified locally: yes`, capture completeness, `https://email.proofstamp.org/verify`, and concise limitation language. The recipient remains blank.

`proofstamp/scripts/create_mailto.py` now supports `--text` to generate the fallback email text and rejects handoff creation if the artifact does not contain a valid capture-completeness status.

### Safety boundaries retained

- ProofStamp never claims that files were attached automatically.
- ProofStamp never sends email automatically.
- The SHA-256 claim is about exact-byte integrity, not truth, authenticity, authorship, provider certification, or original creation time.
- Capture completeness remains an independent evidence dimension and is not upgraded by the email handoff.

### Compatibility

There is no schema redesign and no receipt-format, hashing-algorithm, provenance-vocabulary, or completeness-semantics change.

The existing command remains compatible:

```bash
python proofstamp/scripts/create_mailto.py <artifact> <receipt>
```

It still returns a `mailto:` URI. The new `--text` option is additive.

The intentional behavior change is contractual: after successful exact-byte verification, the host must provide either the mailto link or fallback email text.

### Directory discovery

The README now includes the public install command:

```bash
npx skills add https://github.com/Proof-Stamp/ai --skill proofstamp
```

Current skills.sh documentation states that leaderboard/directory discovery is driven automatically by observed `skills` CLI installs rather than by a separate submission pull request.

## Tagging procedure

1. Confirm the final `main` GitHub Actions `tests` run is green.
2. Run one fresh-host delivery smoke test for the required email handoff.
3. Create tag `v0.1.3` from that exact `main` commit.
4. Publish a GitHub **pre-release** using the release notes above.
5. Run the public `skills` CLI install smoke test.
6. Open the small post-release housekeeping PR that pins `PROMPT.md` to the immutable `v0.1.3` tag.

## Directory submission after release

- **skills.sh:** no separate submission PR is required. Run/install the public repository through the `skills` CLI so it can enter install-driven discovery.
- **Agent Skill Exchange:** submit a catalog PR under `skills/proofstamp/SKILL.md`, category `Security & Verification`, framework `Multi-Framework`, verification `listed`, source `https://github.com/Proof-Stamp/ai`.

The Agent Skill Exchange submission is a catalog wrapper. The canonical runtime skill remains `proofstamp/SKILL.md` in this repository.
