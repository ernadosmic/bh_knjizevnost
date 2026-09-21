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
bundle exec jekyll serve
```

Open `http://localhost:4000/`. The GitHub Actions workflow injects the repository base path automatically for project Pages.

## Adding a work

The Markdown files in `_works/` and `_authors/` are the source of truth. There
is no account to create and no service to sign into. Two ways to add content,
both ending in a file you commit yourself.

**Scaffold the file, then paste the text.** This fills in the identifiers,
permalink and controlled vocabularies so they do not have to be copied by hand:

```powershell
python scripts/new_work.py author --name "Isak Samokovlija" --born 1889 --died 1955
python scripts/new_work.py work --title "Jablan" --author petar-kocic --year 1902 --type short-story
```

The work command allocates the next free archive id for that author, derives the
slug from the title, and refuses to create a second work at a URL already in
use. Open the new file and replace the placeholder body with the literary text.
Run `python scripts/new_work.py work --help` for the full list of fields.

**Or copy an existing file.** Duplicate any file in `_works/`, change the front
matter, and replace the body. `ARCHIVE_FORMAT.md` documents every field.

Either way, check it locally with `bundle exec jekyll serve`, then commit and
push. The deploy workflow rebuilds the site.

### Optional: the Decap editing UI, locally

Decap CMS gives the same files a form interface. It runs entirely on your
machine against your working copy, with no account and no hosted backend. From
two terminals:

```powershell
bundle exec jekyll serve
npx decap-server
```

Then open `/admin/` on the local Jekyll server. Edits are written straight to
the Markdown files, which you then commit and push as usual. The deployed copy
of `/admin/` is inert: no OAuth provider is configured, so nobody can log in
there.

To rebuild only the generated downloads and manifest:

```powershell
python scripts/generate_downloads.py
```

To rebuild Pagefind locally, install its CLI and run it after Jekyll:

```powershell
npx pagefind --site _site
```

The production build is reproduced by `.github/workflows/pages.yml`.

To check paragraph spacing, verse preservation, and Markdown formatting in both
renderers, run `python scripts/check_work_rendering.py` with Bundler and Pandoc
on your PATH.

To check the generated PDF's actual spacing and line numbers across pages, run
`python scripts/check_pdf_rendering.py` with Pandoc, XeLaTeX, and `pdftotext`
(Poppler) on your PATH. Both rendering checks run in the deployment workflow.

## GitHub Pages setup

1. Create an empty GitHub repository under your account and add it as `origin`.
2. Set `url` and `repository` in `_config.yml` to your account and repository.
3. Leave `baseurl: ""`. The workflow passes the correct project path to `jekyll build` via `--baseurl`, so it must not be hard-coded here. For a custom domain, set `url` to the domain.
4. Commit and push the project to the `main` branch.
5. In repository Settings > Pages, set **Source** to **GitHub Actions**. This is required: with the default "Deploy from a branch", GitHub runs its own builder in parallel, which ignores this workflow, builds without the project `--baseurl`, and serves the site without CSS.

## Decap Turbo

Create a site at Decap Turbo, copy its site ID, and replace `REPLACE_WITH_DECAP_TURBO_SITE_ID` in `admin/config.yml`. Do not put a GitHub token or secret in this repository. Commit that public site ID, push to `main`, then open `/admin/` on the deployed site and complete the Turbo GitHub authorization flow.

## Durable archive principle

The site can be reconstructed without Jekyll or Decap: parse the YAML front matter in `_works/*.md` and `_authors/*.md`, render the Markdown body, and use the `url` and metadata in `archive-manifest.json`. Generated PDFs and EPUBs are reproducible with `scripts/generate_downloads.py` and must not be edited by hand.
