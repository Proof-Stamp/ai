# Release process

ProofStamp AI uses tagged GitHub releases as immutable public release boundaries. Do not create a tag until the exact target commit has passed the required tests and release smoke checks.

This file is intentionally version-neutral so it does not become stale after every release.

## Before the release PR

Choose the next version and confirm the intended scope.

For a release that changes the canonical Agent Skill, update every version-bearing public entry point that is expected to stay in sync, including:

- `proofstamp/SKILL.md` metadata;
- the immutable workflow reference in `PROMPT.md`;
- README version text and badges where applicable;
- release/package documentation affected by the change.

Do not mix unrelated feature work into a release-only version bump.

## Required checks

Before tagging:

- [ ] Run the deterministic unit and security test suite locally when the change can be tested locally.
- [ ] Open a focused pull request.
- [ ] Confirm the GitHub Actions `tests` workflow passes on the PR head.
- [ ] Perform any model- or host-dependent smoke tests required by the changed surface.
- [ ] Merge the release PR.
- [ ] Confirm the GitHub Actions `tests` workflow passes on the exact final `main` commit that will be tagged.
- [ ] Confirm the version-bearing public files agree with one another.

For changes to capture, hashing, receipts, conversation coverage, privacy, email handoff, or host adapters, add focused regression coverage before release rather than relying only on manual testing.

## Tag and publish

1. Create the release tag from the exact tested `main` commit.
2. Publish a GitHub release for that tag.
3. Summarize user-visible changes and important trust/security changes in the release notes.
4. Include a changelog link from the previous release when one exists.
5. Do not describe experimental integrations as supported unless their documented support gate has actually been met.

Tags should use the existing version format:

```text
v<major>.<minor>.<patch>
```

ProofStamp is currently pre-1.0, so compatibility should not be assumed across releases unless the relevant contract says otherwise.

## Claude package

Publishing a GitHub release triggers `.github/workflows/package-claude.yml`.

That workflow:

1. checks out the canonical `proofstamp/` source from the release tag;
2. builds the Claude-compatible ZIP;
3. validates the ZIP layout;
4. uploads the ZIP as a workflow artifact; and
5. attaches `proofstamp.zip` to the GitHub release.

For a manual package run, provide the release tag explicitly. The workflow should not rely on a hard-coded default release tag.

## Post-release verification

After publication:

- [ ] Confirm the release points to the intended tested commit.
- [ ] Confirm `proofstamp.zip` is attached when the Claude package is expected.
- [ ] Run a clean install or fresh-host smoke test from the published tag.
- [ ] Verify the README install path and prompt-only path still resolve.
- [ ] Verify any release-specific external links used in the workflow.
- [ ] Open a small housekeeping PR only if a public pointer could not be updated before the tag was created.

## Release notes

Release notes should distinguish clearly between:

- product or workflow changes;
- security or trust-model changes;
- documentation-only changes;
- experimental integrations;
- compatibility or migration notes.

Do not imply that SHA-256 proves truth, authorship, provider authenticity, session completeness, or original creation time. Do not claim provider signing or stronger capture coverage without the evidence required by the trust model.

## Abort conditions

Do not tag or publish if:

- required CI is failing or has not run on the target commit;
- version-bearing files disagree;
- exact-byte verification or receipt tests fail;
- a known security regression is unresolved;
- a required host smoke test fails;
- the release notes overstate provenance, completeness, authenticity, or support status.
