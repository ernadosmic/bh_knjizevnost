# Archive format

This document describes the durable data format. The CMS and Jekyll are conveniences; neither is required to read or edit the archive.

## Directory structure

- `_works/{author}/index.md`: author metadata and Markdown biography.
- `_works/{author}/{filename}.md`: a standalone literary work.
- `_works/{author}/{collection}/index.md`: collection metadata and introduction.
- `_works/{author}/{collection}/{filename}.md`: a work in that collection.
- `assets/downloads/`: generated PDF and EPUB files; do not edit these by hand.
- `archive-manifest.json`: generated machine-readable catalog of every work. The starter file documents the sample record before the first download build.
- `scripts/generate_downloads.py`: reproducible Pandoc and manifest generation.
- `admin/`: optional Decap CMS configuration.
- `_layouts/`, `_includes/`, `assets/`: Jekyll presentation layer.

## Work files

A work file starts with YAML front matter between two `---` lines. To add a work
by hand, only its title and body need to be supplied:

```markdown
---
title: Opomena
type: poetry
---
The literary text goes here.
```

Place it in the author's folder, or in a collection folder beneath that author.
The build fills in permanent identity and derived metadata. Filenames can be
changed freely; `index.md` is reserved for profiles. Author and collection folder
names match their permanent profile IDs and are allocated automatically by the
editor. Changing a display name or title does not rename its folder.

Folder location is authoritative: moving a work changes its author/collection,
moving it out of a collection clears membership and order, and moving an entire
collection changes the author of the collection and its works. Existing IDs and
public URLs are preserved. YAML `author`, `author_name`, `zbirka`, and the CMS's
optional `source_folder` are synchronized from placement. `record_type` is
derived from the file's role (`work`, `author`, or `collection`). Duplicate IDs
and work URLs are rejected instead of silently overwriting another record.

The normalized fields are:

- `id`: permanent archive identifier, such as `PK0001`.
- `title`: published title.
- `slug`: URL-safe title segment used in download filenames.
- `permalink`: explicit public URL, normally `/djela/{author-id}/{slug}/`. It can change without changing `id`.
- `author`: containing author's `id` from its `index.md`.
- `zbirka`: containing collection's `id`, or empty for a standalone work.
- `zbirka_order`: position within the collection; missing positions append automatically.
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

An author's `index.md` uses `id`, `name`, `birth_year`, `death_year`, `sort_name`,
`photo`, and a Markdown biography body. Works refer to the author by `id`; author
pages calculate their work list from that relationship. A missing author index
is scaffolded automatically when a work is added to a new author folder.

## Collection files

A collection's `index.md` uses `id`, `title`, `author`, `year`, `type`, `description`,
and a Markdown introduction. Its author comes from the parent folder. Works are
discovered from sibling Markdown files and ordered by `zbirka_order`. A missing
collection index is scaffolded when a work is placed in a new collection folder.

## Synchronization

`python scripts/prepare_archive.py` validates the tree, fills missing IDs and
profiles, and synchronizes metadata. Jekyll and download builds invoke it
automatically. Repeated runs leave unchanged files untouched. GitHub's archive
sync and publication workflows save generated metadata back into the repository
so the CMS sees it on its next load.

For older checkouts, `python scripts/prepare_archive.py --migrate` moves legacy
flat works and separate profile folders into this hierarchy, without replacing
existing files. The Jekyll `authors` and `zbirke` collections are virtual views
of this tree; they have no separate source folders.

## URLs and identifiers

Jekyll uses each work file's explicit `permalink`, normally `/djela/{author}/{slug}/`, and author URLs at `/autori/{id}/`. Jekyll does not interpolate arbitrary front-matter fields in collection permalink templates, so the explicit field keeps URL changes visible and reviewable. URLs can change later without changing a work's permanent `id`. Download names use `{id}-{slug}`.

## Generated formats

`scripts/generate_downloads.py` reads the Markdown master files, resolves author metadata, and invokes Pandoc once per work. PDFs use XeLaTeX, A4 geometry, and DejaVu Serif. EPUBs receive title, author, and language metadata. The script appends an archival note to generated downloads without changing the canonical Markdown source.

## Reconstructing the site

A future developer can ignore Decap CMS, install any Markdown/YAML parser, walk
the single `_works/` tree, and create a new frontend or static generator. The
manifest provides source paths, stable IDs, metadata, canonical relative URLs,
and generated download paths. No database, API, account, proprietary content
format, or analytics service is required.
