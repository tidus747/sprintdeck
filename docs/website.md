# Documentation website

The public website contains a project homepage, a six-scene screenshot gallery, and searchable documentation generated from repository Markdown. GitHub Pages hosts static HTML only. The live SprintDeck server and session data are never deployed.

## Build locally

The application still has no third-party runtime dependencies. Building the website uses one optional dependency, Python-Markdown, pinned with a package hash in `website/requirements.txt`.

```sh
python -m venv .venv
```

Activate the environment using `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on Linux, then run:

```sh
python -m pip install --require-hashes --only-binary=:all: -r website/requirements.txt
python scripts/build_site.py --base ""
python -m http.server 8080 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8080/`. Stop the preview with Ctrl+C. For the actual repository deployment, build with `python scripts/build_site.py --base /sprintdeck`. The output is the ignored `_site/` directory. Existing nonempty directories are replaced only if they carry the generator's ownership marker.

With the `/sprintdeck` build, run `python scripts/check_site_browser.py --browser "PATH_TO_BROWSER_EXECUTABLE"` for optional real-browser checks of the gallery, search, and mobile layout. Run `python -m unittest discover -s tests -v` in the documentation environment to include all website build tests.

## Content and design

Edit repository Markdown under `docs/` and the root contribution files. The generator includes all documentation pages, the README, contribution notes, changelog, agent guidelines, and license. Relative Markdown links are rewritten to the correct website paths. Search uses a local JSON index and makes no external service calls.

Homepage copy is in `website/templates/home.html`; the documentation shell is in `website/templates/page.html`. Shared styling and small browser interactions live in `website/assets/`. The homepage explains the practical meeting problem: goals, review order, timeboxes, decisions, and next steps often live outside the task board. Claims describe implemented behavior rather than unmeasured productivity gains.

The visual direction takes the linked [Varsha theme](https://astro.build/themes/details/varsha/) as a reference for a landing page and documentation experience. This is an original HTML/CSS implementation; no Varsha code, branding, or assets are copied. The site does not require Astro or change the application's vanilla frontend.

## Screenshots

Generate screenshots with an installed Chromium browser:

```sh
python scripts/capture_docs.py --browser "PATH_TO_BROWSER_EXECUTABLE"
```

The script creates a temporary fictional session and isolated browser profiles, then captures the actual SprintDeck overlays. The board and roadmap beneath them are clearly labeled illustrative content from `website/demo/`. It does not capture the desktop, connect to OBS, inspect a real session, or read an existing browser profile. Review every image before committing. These documentation compositions are not evidence of actual OBS operation.

Only approved screenshots in `website/assets/screenshots/` are copied into the site. The build never copies `.session/`, exports, imports, browser profiles, or user data. If adding real OBS captures later, use a clean fictional scene and inspect them for private windows, file paths, account names, and meeting content.

## GitHub Pages

The Pages workflow builds and checks the site, uploads only `_site/`, and deploys it on pushes to `main`. Pull requests build and check without deploying. The workflow uses GitHub's standard Pages artifact and deployment actions, with no user-provided secrets. Application checks remain separate.

An administrator must select **Settings, Pages, Build and deployment, Source: GitHub Actions** once. If Pages is not enabled, configure-pages can fail even when the site build is correct. Enable it and rerun the Pages workflow. The GitHub connection used by an agent may support repository writes without exposing Pages administration tools.

Expected site URL: `https://tidus747.github.io/sprintdeck/`. A workflow success and an HTTP response from that URL are required before claiming publication. Do not publish the workspace root as a Pages artifact.
