#!/usr/bin/env python3
"""Normalize author records and work references.

An author's ID is permanent once allocated. Correcting a name updates display
metadata without changing references or public URLs. Profiles live in each
author folder's index.md; folder location determines work membership.

It also creates a missing author record when a work was saved with `author_name`.
Existing unrelated author records are never overwritten.
"""

import re
from pathlib import Path

import yaml

from new_work import slugify, yaml_quote
from work_tree import work_paths

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "_works"
AUTHORS = WORKS
ZBIRKE = WORKS


def safe_identifier(value):
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value))


def split_document(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A\ufeff?---[^\S\n]*\n(.*?)^---[^\S\n]*(?=\n|\Z)", text, re.S | re.M)
    if not match:
        return {}, "", text
    raw, body = match.group(1), text[match.end():]
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML front matter must be a mapping")
    return data, raw, body


def read_front_matter(path):
    return split_document(path)[0]


def sort_name(full_name):
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    return "%s, %s" % (parts[-1], " ".join(parts[:-1]))


def rewrite_front_matter(path, updates):
    data, raw, body = split_document(path)
    if not raw:
        raise ValueError("No YAML front matter in %s" % path.relative_to(ROOT))
    updates = {key: value for key, value in updates.items() if data.get(key) != value}
    if not updates:
        return
    rendered = {
        key: str(value) if isinstance(value, int) and not isinstance(value, bool) else yaml_quote(value)
        for key, value in updates.items()
    }
    # YAML node boundaries also handle block scalars and multiline values.
    # Keep untouched metadata and the literary body in their original form.
    nodes = yaml.compose(raw).value
    changes = []
    seen = set()
    for index, (key, value) in enumerate(nodes):
        if key.value not in rendered:
            continue
        end = nodes[index + 1][0].start_mark.index if index + 1 < len(nodes) else len(raw)
        changes.append((key.start_mark.index, end, f"{key.value}: {rendered[key.value]}\n"))
        seen.add(key.value)
    for start, end, replacement in reversed(changes):
        raw = raw[:start] + replacement + raw[end:]
    for key, value in rendered.items():
        if key not in seen:
            raw = raw.rstrip("\n") + f"\n{key}: {value}\n"
    rendered_document = "---\n" + raw + "---" + body
    if path.read_text(encoding="utf-8") != rendered_document:
        path.write_text(rendered_document, encoding="utf-8", newline="\n")


def create_author(author_id, name):
    if not safe_identifier(author_id):
        raise ValueError("Invalid author identifier")
    path = AUTHORS / author_id / "index.md"
    if path.exists():
        return path

    lines = [
        "---",
        "layout: author",
        "record_type: author",
        "id: %s" % yaml_quote(author_id),
        "archive_id: %s" % yaml_quote(author_id),
        "permalink: %s" % yaml_quote("/autori/%s/" % author_id),
        "name: %s" % yaml_quote(name),
        'birth_year: ""',
        'death_year: ""',
        "sort_name: %s" % yaml_quote(sort_name(name)),
        'photo: ""',
        "---",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("Created %s" % path.relative_to(ROOT))
    return path


def normalize_authors():
    aliases = {}
    canonical_names = {}
    problems = []

    for original_path in sorted(AUTHORS.glob("*/index.md")):
        data = read_front_matter(original_path)
        name = str(data.get("name") or "").strip()
        if not name:
            problems.append("%s: missing author name" % original_path.name)
            continue

        desired_id = str(data.get("id") or data.get("archive_id") or original_path.parent.name).strip()
        if not safe_identifier(desired_id):
            problems.append("%s: invalid author ID" % original_path.name)
            continue

        old_ids = {
            original_path.parent.name,
            str(data.get("id") or "").strip(),
            str(data.get("archive_id") or "").strip(),
        }
        old_ids.discard("")

        rewrite_front_matter(
            original_path,
            {
                "record_type": "author",
                "id": desired_id,
                "archive_id": desired_id,
                "permalink": data.get("permalink") or "/autori/%s/" % desired_id,
                "sort_name": sort_name(name),
            },
        )

        for old_id in old_ids | {desired_id}:
            aliases[old_id] = desired_id
        canonical_names[desired_id] = name

    return aliases, canonical_names, problems


def normalize_works(aliases, canonical_names):
    problems = []

    for work_path in work_paths(WORKS):
        data = read_front_matter(work_path)
        author_id = str(data.get("author") or "").strip()
        author_name = str(data.get("author_name") or "").strip()

        if author_id in aliases:
            desired_id = aliases[author_id]
            canonical_name = canonical_names.get(desired_id, author_name)
        elif safe_identifier(author_id) and (AUTHORS / author_id / "index.md").exists():
            desired_id = author_id
            author_data = read_front_matter(AUTHORS / author_id / "index.md")
            canonical_name = str(author_data.get("name") or author_name).strip()
        elif author_name:
            # A corrected display name may no longer resemble its permanent ID.
            # Reuse an exact known name before creating another author record.
            matches = [key for key, name in canonical_names.items()
                       if name.casefold().strip() == author_name.casefold().strip()]
            if len(matches) > 1:
                problems.append("%s: choose an existing author; this name is ambiguous" % work_path.name)
                continue
            desired_id = matches[0] if matches else (
                author_id if safe_identifier(author_id) else slugify(author_name)
            )
            if not desired_id:
                problems.append("%s: could not derive author slug" % work_path.name)
                continue
            create_author(desired_id, author_name)
            aliases[author_id or desired_id] = desired_id
            aliases[desired_id] = desired_id
            canonical_names[desired_id] = author_name
            canonical_name = author_name
        else:
            problems.append("%s: missing resolvable author" % work_path.name)
            continue

        slug = str(data.get("slug") or "").strip()
        if not slug:
            slug = slugify(str(data.get("title") or ""))
        if not slug:
            problems.append("%s: missing work slug" % work_path.name)
            continue

        updates = {
            "author": desired_id,
            "author_name": canonical_name,
            "permalink": str(data.get("permalink") or "/djela/%s/%s/" % (desired_id, slug)),
        }

        if (
            author_id != desired_id
            or author_name != canonical_name
            or str(data.get("permalink") or "").strip() != updates["permalink"]
        ):
            rewrite_front_matter(work_path, updates)
            print("Updated %s" % work_path.relative_to(ROOT))

    return problems


def main():
    from prepare_archive import prepare
    prepare(ROOT)


if __name__ == "__main__":
    main()
