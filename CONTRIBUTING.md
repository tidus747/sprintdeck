# Contributing

Use Python 3.11 or newer. No dependencies need installing. Run `python -m sprintdeck --data .session/session.json` from the repository root so development data stays ignored.

Keep changes small, use the standard library and vanilla JavaScript where practical, and separate controller editing from audience presentation. Explain user-visible behavior in your pull request and include the tests actually run.

Run `python -m unittest discover -s tests -v` and `python scripts/check_style.py`. For JavaScript changes, run the `node --check` commands in README.md. The optional `scripts/check_browser.py` check uses an installed Chromium browser and a temporary session. Timer tests must use injected time rather than sleeping. For layout changes, check 1920 x 1080 and 1280 x 720, keyboard focus, and OBS transparency.

Write code, comments, documentation, tests, UI copy, and examples in English. Unicode U+2014 is forbidden. Use a comma, colon, parentheses, or full stop instead. The repository style checker enforces this for UTF-8 text files.

This repository is public. Never submit real company, employee, customer, project, or meeting information, credentials, or private configuration. Use generic fictional examples such as Engineer A and Automated testing. Keep the project independent of personal or proprietary applications. Do not attach real session exports to public issues.

Update documentation, CHANGELOG.md, and docs/roadmap.md when behavior changes. Disclose substantial AI assistance and review generated contributions carefully. Never fabricate contributors or Git identities. Maintainers retain responsibility for review and maintenance.

The documentation website uses an optional pinned Markdown build dependency. See [website development](docs/website.md) for local preview, screenshot generation, and the GitHub Pages workflow. Review every image and use fictional data only. Do not confuse composed documentation screenshots with actual OBS validation.

Contributions use the existing GPL-3.0 license. Agents must not commit, push, release, or deploy unless explicitly requested by the user.
