#!/usr/bin/env python3
"""Scaffold a work or author file for the archive.

The Markdown files in _works/ and _authors/ are the source of truth. This
script only writes a correct, empty skeleton so the identifiers, permalink and
controlled vocabularies do not have to be copied by hand. Paste the literary
text into the file afterwards with any editor.

    python scripts/new_work.py work --title "Jablan" --author petar-kocic \
        --year 1902 --type short-story

    python scripts/new_work.py author --name "Petar Kocic" \
        --born 1877 --died 1916

Run with --help for every option.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "_works"
AUTHORS = ROOT / "_authors"

# Kept in step with admin/config.yml and the label maps in _config.yml.
TYPES = ["short-story", "novella", "novel", "poetry", "essay", "drama", "other"]
LANGUAGES = ["bs", "hr", "sr", "de", "other"]
SCRIPTS = ["latin", "cyrillic", "other"]
RIGHTS = ["public-domain", "permission", "restricted", "unknown"]

# Transliterate the local alphabet before slugifying, so "Kročić" -> "krocic"
# rather than losing the characters entirely.
TRANSLITERATE = {
    "č": "c", "ć": "c", "đ": "d", "š": "s", "ž": "z",
    "Č": "C", "Ć": "C", "Đ": "D", "Š": "S", "Ž": "Z",
    "dž": "dz", "Dž": "Dz", "DŽ": "DZ", "lj": "lj", "nj": "nj",
}


def slugify(value):
    for source, target in TRANSLITERATE.items():
        value = value.replace(source, target)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def yaml_quote(value):
    """Double-quoted YAML scalar. Only these two characters need escaping."""
    return '"%s"' % str(value).replace("\\", "\\\\").replace('"', '\\"')


def author_initials(author_id):
    parts = [p for p in author_id.split("-") if p]
    return "".join(p[0] for p in parts).upper()[:2] or "XX"


def next_archive_id(author_id):
    """Allocate the next free {INITIALS}{NNNN} id for this author."""
    prefix = author_initials(author_id)
    highest = 0
    for path in WORKS.glob("*.md"):
        match = re.match(r"^%s(\d{4})-" % re.escape(prefix), path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return "%s%04d" % (prefix, highest + 1)


def ensure_absent(path, force):
    if path.exists() and not force:
        sys.exit("Refusing to overwrite existing file: %s\nPass --force to replace it."
                 % path.relative_to(ROOT))


def front_matter_lines(path):
    """Yield the lines between the opening and closing --- of a file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return []


def existing_work_with_permalink(permalink):
    """Find a work already published at this URL.

    The filename carries a freshly allocated id, so it never collides on a
    repeat run. The permalink is what actually has to be unique -- two files
    sharing one would silently fight over the same page.
    """
    wanted = permalink.strip("/")
    for path in sorted(WORKS.glob("*.md")):
        for line in front_matter_lines(path):
            key, _, value = line.partition(":")
            if key.strip() == "permalink" and value.strip().strip('"').strip("/") == wanted:
                return path
    return None


def create_work(args):
    author_file = AUTHORS / ("%s.md" % args.author)
    if not author_file.exists():
        sys.exit("No author file at %s.\nCreate the author first:\n"
                 "  python scripts/new_work.py author --name \"...\""
                 % author_file.relative_to(ROOT))

    slug = args.slug or slugify(args.title)
    if not slug:
        sys.exit("Could not derive a slug from the title; pass --slug explicitly.")

    permalink = "/djela/%s/%s/" % (args.author, slug)
    clash = existing_work_with_permalink(permalink)
    if clash is not None and not args.force:
        sys.exit("%s already publishes %s.\nUse --slug to pick a different URL, "
                 "or --force to overwrite." % (clash.relative_to(ROOT), permalink))

    archive_id = args.id or next_archive_id(args.author)

    # `id` is what the archive format calls the permanent identifier, but Jekyll
    # reserves `id` on collection documents, so `archive_id` carries it in
    # templates. Both are written, with the same value.
    fields = [
        ("id", yaml_quote(archive_id)),
        ("archive_id", yaml_quote(archive_id)),
        ("title", yaml_quote(args.title)),
        ("slug", yaml_quote(slug)),
        ("permalink", permalink),
        ("author", yaml_quote(args.author)),
        ("year", args.year if args.year is not None else '""'),
        ("language", yaml_quote(args.language)),
        ("script", yaml_quote(args.script)),
        ("type", yaml_quote(args.type)),
    ]

    lines = ["---"]
    lines += ["%s: %s" % pair for pair in fields]
    lines.append("genres:")
    for genre in (args.genre or []):
        lines.append("  - %s" % genre)
    lines += [
        "period: %s" % yaml_quote(args.period or ""),
        "source: %s" % yaml_quote(args.source or ""),
        "edition: %s" % yaml_quote(args.edition or ""),
        "source_pages: %s" % yaml_quote(args.source_pages or ""),
        "rights: %s" % yaml_quote(args.rights),
        "rights_note: %s" % yaml_quote(args.rights_note or ""),
        "featured: %s" % ("true" if args.featured else "false"),
        "description: %s" % yaml_quote(args.description or ""),
        "---",
        "",
        "Paste the complete literary text here, as Markdown. Separate paragraphs",
        "with a blank line, use _italics_ for emphasis, and start a line with a",
        "greater-than sign to quote a passage. Delete this placeholder.",
        "",
    ]

    path = WORKS / ("%s-%s.md" % (archive_id, slug))
    ensure_absent(path, args.force)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("Wrote %s" % path.relative_to(ROOT))
    print("Public URL: /djela/%s/%s/" % (args.author, slug))
    print("Next: paste the text into that file, then `bundle exec jekyll serve` to check it.")


def create_author(args):
    author_id = args.id or slugify(args.name)
    if not author_id:
        sys.exit("Could not derive an id from the name; pass --id explicitly.")

    sort_name = args.sort_name
    if not sort_name:
        parts = args.name.split()
        sort_name = "%s, %s" % (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else args.name

    lines = [
        "---",
        "layout: author",
        "id: %s" % yaml_quote(author_id),
        "archive_id: %s" % yaml_quote(author_id),
        "permalink: /autori/%s/" % author_id,
        "name: %s" % yaml_quote(args.name),
        "birth_year: %s" % (args.born if args.born is not None else '""'),
        "death_year: %s" % (args.died if args.died is not None else '""'),
        "sort_name: %s" % yaml_quote(sort_name),
        "photo: \"\"",
        "description: %s" % yaml_quote(args.description or ""),
        "---",
        "",
        "Short biography. Delete this placeholder.",
        "",
    ]

    path = AUTHORS / ("%s.md" % author_id)
    ensure_absent(path, args.force)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("Wrote %s" % path.relative_to(ROOT))
    print("Author id for work files: %s" % author_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    work = sub.add_parser("work", help="scaffold a work in _works/")
    work.add_argument("--title", required=True)
    work.add_argument("--author", required=True, help="author id, e.g. petar-kocic")
    work.add_argument("--year", type=int)
    work.add_argument("--type", choices=TYPES, default="short-story")
    work.add_argument("--language", choices=LANGUAGES, default="sr")
    work.add_argument("--script", choices=SCRIPTS, default="latin")
    work.add_argument("--rights", choices=RIGHTS, default="unknown")
    work.add_argument("--rights-note", dest="rights_note")
    work.add_argument("--genre", action="append", help="repeatable")
    work.add_argument("--period")
    work.add_argument("--source")
    work.add_argument("--edition")
    work.add_argument("--source-pages", dest="source_pages")
    work.add_argument("--description")
    work.add_argument("--slug", help="default: derived from the title")
    work.add_argument("--id", help="default: next free id for this author")
    work.add_argument("--featured", action="store_true")
    work.add_argument("--force", action="store_true")
    work.set_defaults(func=create_work)

    author = sub.add_parser("author", help="scaffold an author in _authors/")
    author.add_argument("--name", required=True)
    author.add_argument("--born", type=int)
    author.add_argument("--died", type=int)
    author.add_argument("--sort-name", dest="sort_name", help="default: Surname, Given")
    author.add_argument("--description")
    author.add_argument("--id", help="default: derived from the name")
    author.add_argument("--force", action="store_true")
    author.set_defaults(func=create_author)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
