# Development rules

- Use English for code, UI, examples, documentation, and tests. Never author Unicode U+2014.
- This repository is public. Never add credentials, private configuration, company data, real identities, customer records, or real session exports. Use generic fictional examples.
- Keep SprintDeck independent of personal and proprietary projects.
- Prefer Python standard library, vanilla JavaScript, small modules, and local-first server state.
- Bind the unauthenticated server to loopback. Render user text safely and validate imported state.
- Keep local session files ignored. Preserve the existing GPL-3.0 license.
- Run relevant tests after changes and all checks before handoff: `py -3.11 -m unittest discover -s tests -v` (Windows) or `python3 -m unittest discover -s tests -v`, plus `python scripts/check_style.py`.
- Update documentation, roadmap, and changelog to match implemented behavior.
- Disclose AI assistance. Human review and maintenance remain necessary. Never fabricate authors or email addresses.
- Do not commit, push, publish, or release unless the user explicitly requests it.
- The static documentation website builds from repository Markdown with `python scripts/build_site.py`. Install only its optional pinned dependency from `website/requirements.txt`; the application remains dependency-free. Never publish session data or unreviewed screenshots.
