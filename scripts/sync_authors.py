#!/usr/bin/env python3
"""Create missing author records referenced by work entries.

When the CMS saves a work with a new author, admin/index.html stores the
generated author id in `author` and the human-readable name in `author_name`.
This script turns that metadata into a normal _authors entry.

Existing author files are never overwritten.
"""

from pathlib import Path

import yaml

from new_work import slugify, yaml_quote

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "_works"
AUTHORS = ROOT / "_authors"


def read_front_matter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        _, raw, _ = text.split("---", 2)
    except ValueError:
        return {}
    data = yaml.safe_load(raw) or {}
    return data if isinstance(data, dict) else {}


def sort_name(full_name):
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    return "%s, %s" % (parts[-1], " ".join(parts[:-1]))


def create_author(author_id, name):
    path = AUTHORS / ("%s.md" % author_id)
    if path.exists():
        return False

    lines = [
        "---",
        "layout: author",
        "id: %s" % yaml_quote(author_id),
        "archive_id: %s" % yaml_quote(author_id),
        "permalink: /autori/%s/" % author_id,
        "name: %s" % yaml_quote(name),
        'birth_year: ""',
        'death_year: ""',
        "sort_name: %s" % yaml_quote(sort_name(name)),
        'photo: ""',
        "---",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("Created %s" % path.relative_to(ROOT))
    return True


def main():
    AUTHORS.mkdir(parents=True, exist_ok=True)
    unresolved = []

    for work_path in sorted(WORKS.glob("*.md")):
        data = read_front_matter(work_path)
        author_id = str(data.get("author") or "").strip()
        if not author_id:
            unresolved.append("%s: missing author id" % work_path.name)
            continue

        author_path = AUTHORS / ("%s.md" % author_id)
        if author_path.exists():
            continue

        author_name = str(data.get("author_name") or "").strip()
        if not author_name:
            unresolved.append(
                "%s: author %s does not exist and author_name is empty"
                % (work_path.name, author_id)
            )
            continue

        expected_id = slugify(author_name)
        if expected_id != author_id:
            unresolved.append(
                "%s: author id %s does not match generated id %s"
                % (work_path.name, author_id, expected_id)
            )
            continue

        create_author(author_id, author_name)

    if unresolved:
        print("\nUnresolved author references:")
        for issue in unresolved:
            print("- %s" % issue)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
