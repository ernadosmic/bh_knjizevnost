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

The Markdown files in `_works/` and `_authors/` are the source of truth. Once
online login is connected (see below), use the `/admin/` dashboard to add and
edit works and authors. Publishing saves a commit to `main`; GitHub Actions
then rebuilds the website and PDF/EPUB downloads.

You can also edit locally without an account:

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
the Markdown files, which you then commit and push as usual. Online editing uses
the separate Turbo login described below.

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

## Online admin dashboard

Inside **ZBIRKE**, open a saved collection and use **Djela u zbirci**:

- **Napiši novo djelo** opens a new work with its collection and author selected.
- **Dodaj postojeće djelo** searches existing works; **Otvori i dodaj u zbirku**
  opens the selected work with this collection selected.

The work editor opens in a new tab. Save/publish the work to apply its membership;
opening it alone does not change anything. Set its optional order within the
collection only when a specific position is needed; otherwise new works are
appended automatically during normalization. Moving a work clears its old
position. Save a new collection before adding works to it.

The dashboard is at https://ernadosmic.github.io/bh_knjizevnost/admin/.
`admin/config.yml` contains the connected site's public Site ID. Online login
becomes available after the admin configuration is deployed. The following
steps document the setup if the site ever needs to be reconnected.

1. Create an account at https://turbo.decapcms.org and an organization on the
   Free plan (one site and one editor).
2. In **Git connection**, install the Turbo GitHub App with access to only
   `ernadosmic/bh_knjizevnost`.
3. Create a site with repository `ernadosmic/bh_knjizevnost`, branch `main`,
   config path `admin/config.yml`, and admin interface URL
   `https://ernadosmic.github.io/bh_knjizevnost/admin/`.
4. Copy the **Site ID** from the site's Overview tab into `turbo_site_id` in
   `admin/config.yml`. This ID is public; no password or GitHub secret belongs
   in the repository.
5. Commit and push the configuration, wait for the Pages deployment to finish,
   then open the dashboard and select **Login with Turbo**.

Choose **DJELA** to create or edit a work, and **AUTORI** to manage biographies.
For a new work, enter the title, choose an author (or use **Dodaj autora**),
and write the text. The editor generates its permanent ID and public URL;
there is no author-specific counter to maintain. Existing and imported IDs
are preserved. New works with identical titles receive distinct URLs.
Correcting a title or author name preserves established IDs and links.

Markdown import fills the form immediately so imported values can be reviewed
and edited before saving. Files without front matter can use their first H1
heading or filename as the title. Latin/Cyrillic script is detected automatically
unless explicitly selected. Language and rights remain editorial choices;
rights default to unknown. Additional metadata follows the text editor.

For precise literary line breaks, use the Markdown editor's **Raw** mode.
Save stores the draft; **OBJAVI STRANICU** releases saved changes together.
Author records and collection positions are normalized during the build;
the public pages and downloads update when that build finishes.

Turbo currently requires the beta CMS release. `admin/index.html` pins
`3.17.0-beta.0` rather than following a moving beta tag. Setup references:
[getting started](https://decapcms.org/docs/turbo-getting-started/) and
[connecting a site](https://decapcms.org/docs/turbo-connecting-a-site/).

### Editor regression checks

Node.js 22+ is needed only for editor tests, not for the static site build:

```powershell
npm ci
npx playwright install chromium
npm test
python scripts/test_editor_sync.py
npm run test:editor
```

The browser check loads the pinned CMS and YAML libraries from their CDN and
uses Decap's in-memory test backend. It does not access or publish to GitHub.
To use an existing Chromium installation, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE`.

## Durable archive principle

The site can be reconstructed without Jekyll or Decap: parse the YAML front matter in `_works/*.md` and `_authors/*.md`, render the Markdown body, and use the `url` and metadata in `archive-manifest.json`. Generated PDFs and EPUBs are reproducible with `scripts/generate_downloads.py` and must not be edited by hand.
