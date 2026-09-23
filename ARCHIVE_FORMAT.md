# Archive format

This document describes the durable data format. The CMS and Jekyll are conveniences; neither is required to read or edit the archive.

## Directory structure

- `_works/`: one UTF-8 Markdown file per literary work.
- `_authors/`: one UTF-8 Markdown file per author.
- `assets/downloads/`: generated PDF and EPUB files; do not edit these by hand.
- `archive-manifest.json`: generated machine-readable catalog of every work. The starter file documents the sample record before the first download build.
- `scripts/generate_downloads.py`: reproducible Pandoc and manifest generation.
- `admin/`: optional Decap CMS configuration.
- `_layouts/`, `_includes/`, `assets/`: Jekyll presentation layer.

## Work files

A work file starts with YAML front matter between two `---` lines. Required fields are:

- `id`: permanent archive identifier, such as `PK0001`.
- `title`: published title.
- `slug`: URL-safe title segment used in download filenames.
- `permalink`: explicit public URL, normally `/djela/{author-id}/{slug}/`. It can change without changing `id`.
- `author`: author `id` from `_authors/`.
- `year`: original publication year when known.
- `language`: language code such as `bs`, `hr`, or `sr`.
- `script`: `latin` or `cyrillic`.
- `type`: `short-story`, `novella`, `novel`, `poetry`, `essay`, `drama`, or `other`.
- `genres`: list of genre labels.
- `period`: literary period, if known.
- `source`, `edition`, `source_pages`: provenance fields.
- `rights`: `public-domain`, `permission`, `restricted`, or `unknown`.
- `rights_note`: additional legal or provenance context.
- `featured`: boolean used for the home page.
- `description`: short catalog description.

The Markdown body after the front matter is the complete canonical literary text. Corrections should be committed there so Git preserves the history.

The CMS automatically assigns new works a `D-` prefixed UUID. Legacy and imported
identifiers such as `PK0001` remain valid. IDs are not derived again when titles
or author names change. `created_at`, when present, records initial creation in
UTC and provides a stable ordering for new works appended to a collection.
Missing collection positions are assigned after the highest explicit position.
Author and collection IDs likewise remain stable after display-name corrections.

In literary works, a single newline between prose passages starts a new paragraph
on the website and a line break in PDF/EPUB downloads. On the website, one newline gives a small
paragraph gap (0.45 em), while two newlines (a blank line) give a larger gap
(1.3 em). Website paragraphs have no first-line indentation. In PDFs, a single
source newline starts a new line with a 1.5 em indent and no extra vertical gap.
Automatically wrapped continuation lines stay flush left. A blank source line
starts a new paragraph with a 1.3 em gap and a 1.5 em first-line indent. The opening
paragraph and paragraphs after headings stay flush left. Printed lines are numbered
in the left margin at 5, 10, 15, and so on, continuously across pages.
Let the editor visually wrap long lines; insert a newline only where you want a new
passage. Headings, lists, quotations, and code keep Markdown syntax.

For verse inside prose, use a fenced `verse` block to preserve its line breaks.
PDFs indent each verse line just like prose source lines, including across pages:

````markdown
First prose passage.
Second prose passage.

```verse
First verse line
Second verse line
```

Next prose passage.
````

Works with `type: poetry` preserve line breaks and blank lines between stanzas
automatically. Keep the title and author in front matter; templates display them.

## Author files

Author files use `id`, `name`, `birth_year`, `death_year`, `sort_name`, `photo`, and a Markdown biography body. Works refer to the author by `id`; author pages calculate their work list from that relationship, so the list is never duplicated in author files.

## URLs and identifiers

Jekyll uses each work file's explicit `permalink`, normally `/djela/{author}/{slug}/`, and author URLs at `/autori/{id}/`. Jekyll does not interpolate arbitrary front-matter fields in collection permalink templates, so the explicit field keeps URL changes visible and reviewable. URLs can change later without changing a work's permanent `id`. Download names use `{id}-{slug}`.

## Generated formats

`scripts/generate_downloads.py` reads the Markdown master files, resolves author metadata, and invokes Pandoc once per work. PDFs use XeLaTeX, A4 geometry, and DejaVu Serif. EPUBs receive title, author, and language metadata. The script appends an archival note to generated downloads without changing the canonical Markdown source.

## Reconstructing the site

A future developer can ignore Decap CMS, install any Markdown/YAML parser, read the two collections, and create a new frontend or static generator. The manifest provides stable IDs, metadata, canonical relative URLs, and generated download paths. No database, API, account, proprietary content format, or analytics service is required.
