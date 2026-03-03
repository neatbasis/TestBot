# Contributing

Thanks for contributing to TestBot.

## Docs QA checklist

When updating docs, complete this lightweight checklist before opening a PR:

- [ ] File tree examples match the current repository layout.
- [ ] Commands are runnable as written from the documented context.
- [ ] Required terms match the canonical glossary in `docs/directives/terms.md`.

Optional validation for markdown links/paths:

```bash
python scripts/validate_markdown_paths.py
```
