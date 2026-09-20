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

Single newlines within a paragraph are preserved as visible line breaks on the
website and in PDF/EPUB downloads. Use a blank line to start a new paragraph or
separate stanzas. Let the editor visually wrap long lines instead of inserting
newlines solely to fit the editing window. Keep the work's title and author in
front matter; the page and download templates display them automatically.

## Author files

Author files use `id`, `name`, `birth_year`, `death_year`, `sort_name`, `photo`, and a Markdown biography body. Works refer to the author by `id`; author pages calculate their work list from that relationship, so the list is never duplicated in author files.

## URLs and identifiers

Jekyll uses each work file's explicit `permalink`, normally `/djela/{author}/{slug}/`, and author URLs at `/autori/{id}/`. Jekyll does not interpolate arbitrary front-matter fields in collection permalink templates, so the explicit field keeps URL changes visible and reviewable. URLs can change later without changing a work's permanent `id`. Download names use `{id}-{slug}`.

## Generated formats

`scripts/generate_downloads.py` reads the Markdown master files, resolves author metadata, and invokes Pandoc once per work. PDFs use XeLaTeX, A4 geometry, and DejaVu Serif. EPUBs receive title, author, and language metadata. The script appends an archival note to generated downloads without changing the canonical Markdown source.

## Reconstructing the site

A future developer can ignore Decap CMS, install any Markdown/YAML parser, read the two collections, and create a new frontend or static generator. The manifest provides stable IDs, metadata, canonical relative URLs, and generated download paths. No database, API, account, proprietary content format, or analytics service is required.
