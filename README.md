# Biblioteka književnosti

Static literary archive built with Jekyll. The canonical copy of every work is a UTF-8 Markdown file with YAML front matter in `_works/`; authors live in `_authors/`. Decap CMS is an optional editing interface over those files, not the source of truth.

## Requirements

- Ruby 3.1+ and Bundler
- Python 3 and `PyYAML`
- Pandoc
- XeLaTeX (the TeX Live `texlive-xetex` package on GitHub Actions)
- Pagefind, only when rebuilding the local search index

On Windows, the simplest Ruby route is RubyInstaller with the MSYS2 toolchain. Install Pandoc from its official Windows installer and a TeX distribution such as MiKTeX with XeLaTeX enabled. Docker is optional and not required.

## Local development

```powershell
bundle install
python -m pip install -r requirements-build.txt
python scripts/generate_downloads.py
bundle exec jekyll serve --baseurl /bhknjizevnost
```

Open `http://localhost:4000/bhknjizevnost/`. To use a root URL locally, run Jekyll with `--baseurl ""`.

The Decap local backend can be started from a second terminal with the Decap proxy package:

```powershell
npx decap-server
```

Then open `/admin/` on the local Jekyll server. The browser must be allowed to load the Decap admin script; the public archive itself has no remote runtime dependency.

To rebuild only the generated downloads and manifest:

```powershell
python scripts/generate_downloads.py
```

To rebuild Pagefind locally, install its CLI and run it after Jekyll:

```powershell
npx pagefind --site _site
```

The production build is reproduced by `.github/workflows/pages.yml`.

## GitHub Pages setup

1. Create an empty GitHub repository named `bhknjizevnost` under your account and add it as `origin`.
2. Replace `USERNAME` in `_config.yml` (`url` and `repository`) with your GitHub username.
3. Keep `baseurl: "/bhknjizevnost"` for project Pages. For a custom domain, set `url` to the domain and `baseurl: ""`.
4. Commit and push the project to the `main` branch.
5. In repository Settings > Pages, choose **GitHub Actions** as the source. The workflow deploys the generated site.

## Decap Turbo

Create a site at Decap Turbo, copy its site ID, and replace `REPLACE_WITH_DECAP_TURBO_SITE_ID` in `admin/config.yml`. Do not put a GitHub token or secret in this repository. Commit that public site ID, push to `main`, then open `/admin/` on the deployed site and complete the Turbo GitHub authorization flow.

## Durable archive principle

The site can be reconstructed without Jekyll or Decap: parse the YAML front matter in `_works/*.md` and `_authors/*.md`, render the Markdown body, and use the `url` and metadata in `archive-manifest.json`. Generated PDFs and EPUBs are reproducible with `scripts/generate_downloads.py` and must not be edited by hand.
