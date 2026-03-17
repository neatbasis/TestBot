# Open PR assessment report (2026-03-17)

## Scope

Reviewed open pull requests:

- https://github.com/neatbasis/TestBot/pull/516
- https://github.com/neatbasis/TestBot/pull/518
- https://github.com/neatbasis/TestBot/pull/519

Assessment goal: determine compatibility with current `main` state in this repository snapshot and identify which contributions should be merged.

## Method

1. Retrieved PR metadata (state, mergeability, head/base SHA, changed files) from the GitHub API.
2. Downloaded each PR patch and ran `git apply --check` against current `main`-equivalent working tree.
3. Compared candidate PR content against current repository files where relevant.
4. Evaluated overlap/duplication between PRs.

## Findings summary

| PR | Current GitHub mergeability | Applies cleanly to current tree (`git apply --check`) | Overlap/duplication | Recommendation |
| --- | --- | --- | --- | --- |
| #516 | `mergeable: true`, `mergeable_state: clean` | **No** (conflicts / already-present files) | Mostly already integrated; one shared checklist file has diverged since PR branch point | **Do not merge as-is** |
| #518 | `mergeable: true`, `mergeable_state: clean` | **Yes** | Duplicate of #519 (content-equivalent changeset) | **Merge one of {#518, #519}** |
| #519 | `mergeable: true`, `mergeable_state: clean` | **Yes** | Duplicate of #518 (content-equivalent changeset) | **Merge one of {#518, #519}** |

## Detailed analysis

### PR #516

- Changed files:
  - `docs/issues/evidence/governance-craap-analysis-main-alignment.md` (added in PR)
  - `docs/issues/evidence/governance-stabilization-checklist.md` (modified)
  - `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` (added in PR)
- `git apply --check /tmp/prpatch/516.patch` fails with:
  - existing-file collisions for both added evidence files, and
  - hunk failure in `governance-stabilization-checklist.md`.
- Direct content comparison against PR head commit confirms:
  - `governance-craap-analysis-main-alignment.md` is already identical on current tree,
  - `issue-0022-pass-seven-verification-log.md` is already identical on current tree,
  - `governance-stabilization-checklist.md` has advanced/diverged beyond PR snapshot.

Interpretation: #516 is stale relative to current state. Attempting to merge it now would require conflict resolution and risks regressing newer checklist content.

### PR #518

- Changed files:
  - `docs/issues.md`
  - `docs/issues/evidence/governance-stabilization-checklist.md`
  - `docs/issues/governance-control-surface-contract-freeze.md`
- `git apply --check /tmp/prpatch/518.patch` succeeds on current tree.
- Introduces governance-freeze ownership matrix clarifications and links that are not yet present in current files.

Interpretation: #518 is compatible and appears merge-ready.

### PR #519

- Same changed files and line-level edits as #518.
- `git apply --check /tmp/prpatch/519.patch` succeeds on current tree.
- Patch diff between #518 and #519 differs only in commit metadata (commit SHA/date), not repository content.

Interpretation: #519 is also compatible but functionally redundant with #518.

## Recommended merge action

1. **Close or supersede PR #516** (stale/conflicting with already-landed content).
2. **Merge exactly one of PR #518 or PR #519** (equivalent contributions).
3. Close the other duplicate after one merges.

## Command evidence used

```bash
python - <<'PY'
import json,urllib.request
for n in [516,518,519]:
    req=urllib.request.Request(f'https://api.github.com/repos/neatbasis/TestBot/pulls/{n}',headers={'User-Agent':'codex'})
    with urllib.request.urlopen(req) as r:
        j=json.load(r)
    print(n,j['state'],j.get('mergeable'),j.get('mergeable_state'),j['head']['sha'],j['base']['sha'])
PY

python - <<'PY'
import json,urllib.request
for n in [516,518,519]:
    req=urllib.request.Request(f'https://api.github.com/repos/neatbasis/TestBot/pulls/{n}/files?per_page=100',headers={'User-Agent':'codex'})
    with urllib.request.urlopen(req) as r:
        files=json.load(r)
    print('PR',n,[f['filename'] for f in files])
PY

for n in 516 518 519; do
  curl -sL https://github.com/neatbasis/TestBot/pull/$n.patch -o /tmp/prpatch/$n.patch
  git apply --check /tmp/prpatch/$n.patch
done

python - <<'PY'
import urllib.request, pathlib
sha='0ea225135f71c18541ce31ad60594886afd66253'  # PR 516 head
for f in [
  'docs/issues/evidence/governance-craap-analysis-main-alignment.md',
  'docs/issues/evidence/governance-stabilization-checklist.md',
  'docs/issues/evidence/issue-0022-pass-seven-verification-log.md',
]:
  url=f'https://raw.githubusercontent.com/neatbasis/TestBot/{sha}/{f}'
  remote=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'codex'})).read()
  local=pathlib.Path(f).read_bytes()
  print(f, 'same' if remote==local else 'DIFF')
PY

diff -u /tmp/prpatch/518.patch /tmp/prpatch/519.patch
```
