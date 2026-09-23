"""Work placement is author/[collection]/file.md; filenames are not identifiers."""
from pathlib import Path
import re
import uuid


def work_paths(root):
    return sorted(Path(root).rglob("*.md"))


def placement(path, root):
    parts = Path(path).resolve().relative_to(Path(root).resolve()).parts
    if len(parts) == 1:
        return None  # Legacy flat file, migrated explicitly from its metadata.
    if len(parts) not in (2, 3):
        raise ValueError(f"{path}: use author/file.md or author/collection/file.md")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", part) for part in parts[:-1]):
        raise ValueError(f"{path}: author and collection folders must use their archive IDs")
    return parts[0], parts[1] if len(parts) == 3 else ""


def unique_path(directory, stem, reserved=()):
    directory = Path(directory)
    occupied = {str(Path(p)).casefold() for p in reserved}
    occupied.update(str(p).casefold() for p in directory.glob("*.md"))
    candidate = directory / f"{stem}.md"
    number = 2
    while str(candidate).casefold() in occupied:
        candidate = directory / f"{stem}-{number}.md"
        number += 1
    return candidate


def migrate_flat(root):
    from new_work import slugify
    from sync_authors import read_front_matter, safe_identifier
    root = Path(root).resolve()
    planned = []
    for source in sorted(root.glob("*.md")):
        data = read_front_matter(source)
        author = str(data.get("author") or "").strip()
        collection = str(data.get("zbirka") or "").strip()
        if not safe_identifier(author) or (collection and not safe_identifier(collection)):
            raise ValueError(f"{source}: cannot migrate without a valid author/collection")
        directory = root / author
        if collection:
            directory /= collection
        stem = slugify(str(data.get("title") or "")) or "djelo"
        target = unique_path(directory, stem, [p[1] for p in planned])
        # Validate all paths before moving any file. Never replace an existing work.
        target.resolve().relative_to(root)
        source.resolve().relative_to(root)
        planned.append((source, target))
    for source, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError(f"Refusing to overwrite {target}")
        source.rename(target)
    return planned


def apply_placements(root, authors, collections):
    from new_work import slugify
    from sync_authors import read_front_matter, rewrite_front_matter
    root, authors, collections = map(Path, (root, authors, collections))
    author_names = {str(d.get("id")): str(d.get("name") or "")
                    for p in authors.glob("*.md") for d in [read_front_matter(p)]}
    known_collections = {str(read_front_matter(p).get("id")) for p in collections.glob("*.md")}
    updates = []
    ids, urls = {}, {}
    new_collections = {}
    for path in work_paths(root):
        location = placement(path, root)
        if location is None:
            raise ValueError(f"{path}: move this work into an author folder (or run --migrate)")
        author, collection = location
        data = read_front_matter(path)
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValueError(f"{path}: missing title in YAML front matter")
        identifier = str(data.get("id") or data.get("archive_id") or f"D-{uuid.uuid4()}")
        slug = str(data.get("slug") or f"{slugify(title) or 'djelo'}-{identifier.lower()}")
        url = str(data.get("permalink") or f"/djela/{author}/{slug}/")
        for value, seen, label in [(identifier, ids, "ID"), (url, urls, "public URL")]:
            if value in seen:
                raise ValueError(f"Duplicate {label} {value}: {seen[value]} and {path}")
            seen[value] = path
        changed_author = data.get("author") != author
        name = author_names.get(author) or (
            str(data.get("author_name") or "") if not changed_author else ""
        ) or author.replace("-", " ").title()
        patch = {"id": identifier, "archive_id": identifier, "slug": slug,
                 "permalink": url, "author": author, "author_name": name, "zbirka": collection}
        if str(data.get("zbirka") or "") != collection:
            patch["zbirka_order"] = ""
        patch = {key: value for key, value in patch.items() if data.get(key, "") != value}
        if patch:
            updates.append((path, patch))
        if collection and collection not in known_collections:
            new_collections.setdefault(collection, set()).add(author)
    # No source changes until the complete tree has passed validation.
    collections.mkdir(parents=True, exist_ok=True)
    for identifier, members in new_collections.items():
        import yaml
        metadata = {"id": identifier, "archive_id": identifier,
                    "title": identifier.replace("-", " ").title(), "slug": identifier,
                    "permalink": f"/zbirke/{identifier}/", "type": "mixed-collection"}
        if len(members) == 1:
            metadata["author"] = next(iter(members))
        target = collections / f"{identifier}.md"
        with target.open("x", encoding="utf-8", newline="\n") as output:
            output.write("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n")
    for path, patch in updates:
        rewrite_front_matter(path, patch)
