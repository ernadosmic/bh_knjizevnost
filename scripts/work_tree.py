"""Work placement is author/[collection]/file.md; filenames are not identifiers."""
from pathlib import Path
import re
import uuid


def work_paths(root):
    return sorted(path for path in Path(root).rglob("*.md") if path.name.lower() != "index.md")


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
    occupied.add(str(directory / "index.md").casefold())
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


def migrate_profiles(root):
    from sync_authors import read_front_matter, safe_identifier
    root = Path(root).resolve()
    planned = []
    for source in sorted((root / "_authors").glob("*.md")):
        identifier = str(read_front_matter(source).get("id") or source.stem)
        if not safe_identifier(identifier):
            raise ValueError(f"Invalid author ID: {source}")
        planned.append((source, root / "_works" / identifier / "index.md"))
    for source in sorted((root / "_zbirke").glob("*.md")):
        data = read_front_matter(source)
        author, identifier = str(data.get("author") or ""), str(data.get("id") or source.stem)
        if not safe_identifier(author) or not safe_identifier(identifier):
            raise ValueError(f"Collection needs an author and ID: {source}")
        planned.append((source, root / "_works" / author / identifier / "index.md"))
    destinations = set()
    for source, target in planned:
        source.resolve().relative_to(root)
        target.resolve().relative_to(root / "_works")
        key = str(target).casefold()
        if target.exists() or key in destinations:
            raise ValueError(f"Refusing to overwrite {target}")
        destinations.add(key)
    for source, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
    for name in ("_authors", "_zbirke"):
        directory = root / name
        marker = directory / ".gitkeep"
        if marker.is_file():
            marker.unlink()
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return planned


def apply_placements(root, authors, collections):
    from new_work import slugify
    from sync_authors import read_front_matter, rewrite_front_matter, safe_identifier
    root, authors, collections = map(Path, (root, authors, collections))
    profiles = sorted(p for p in root.rglob("*.md") if p.name.lower() == "index.md")
    seen_profiles = {}
    for path in profiles:
        if len(path.relative_to(root).parts) not in (2, 3) or path.name != "index.md":
            raise ValueError(f"{path}: profiles belong at author/index.md or author/collection/index.md")
        data = read_front_matter(path)
        identifier = str(data.get("id") or data.get("archive_id") or path.parent.name)
        kind = "author" if path.parent.parent == root else "collection"
        label = "name" if kind == "author" else "title"
        placement(path, root)
        if not str(data.get(label) or "").strip():
            raise ValueError(f"{path}: missing {label} in YAML front matter")
        if identifier != path.parent.name:
            raise ValueError(f"{path}: profile folder must match its permanent ID ({identifier})")
        key = kind, identifier
        if key in seen_profiles:
            raise ValueError(f"Duplicate {kind} ID {identifier}: {seen_profiles[key]} and {path}")
        seen_profiles[key] = path
    author_names = {str(d.get("id") or p.parent.name): str(d.get("name") or "")
                    for p in authors.glob("*/index.md") for d in [read_front_matter(p)]}
    collection_ids = {(p.parent.parent.name, p.parent.name): str(read_front_matter(p).get("id") or p.parent.name)
                      for p in collections.glob("*/*/index.md")}
    updates = []
    ids, urls = {}, {}
    new_collections = {}
    new_authors = {}
    for path in collections.glob("*/*/index.md"):
        author = path.parent.parent.name
        if author not in author_names:
            new_authors[author] = author.replace("-", " ").title()
    for path in work_paths(root):
        location = placement(path, root)
        if location is None:
            raise ValueError(f"{path}: move this work into an author folder (or run --migrate)")
        author, collection_folder = location
        collection = collection_ids.get(location, collection_folder)
        data = read_front_matter(path)
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValueError(f"{path}: missing title in YAML front matter")
        identifier = str(data.get("id") or data.get("archive_id") or f"D-{uuid.uuid4()}")
        slug = str(data.get("slug") or f"{slugify(title) or 'djelo'}-{identifier.lower()}")
        if not safe_identifier(identifier) or not safe_identifier(slug):
            raise ValueError(f"{path}: work ID and URL slug must contain only letters, numbers, hyphens or underscores")
        url = str(data.get("permalink") or f"/djela/{author}/{slug}/")
        for value, seen, label in [(identifier, ids, "ID"), (url, urls, "public URL")]:
            if value in seen:
                raise ValueError(f"Duplicate {label} {value}: {seen[value]} and {path}")
            seen[value] = path
        changed_author = data.get("author") != author
        name = author_names.get(author) or (
            str(data.get("author_name") or "") if not changed_author else ""
        ) or author.replace("-", " ").title()
        patch = {"record_type": "work", "id": identifier, "archive_id": identifier, "slug": slug,
                 "permalink": url, "author": author, "author_name": name, "zbirka": collection}
        if "source_folder" in data:
            patch["source_folder"] = path.parent.relative_to(root).as_posix()
        if str(data.get("zbirka") or "") != collection:
            patch["zbirka_order"] = ""
        patch = {key: value for key, value in patch.items() if data.get(key, "") != value}
        if patch:
            updates.append((path, patch))
        if author not in author_names:
            new_authors[author] = name
        if collection and location not in collection_ids:
            existing = seen_profiles.get(("collection", collection))
            if existing or (collection in new_collections.values() and location not in new_collections):
                raise ValueError(f"{path}: collection ID {collection} is already used in another author folder")
            new_collections[location] = collection
    # No source changes until the complete tree has passed validation.
    for author, name in new_authors.items():
        from sync_authors import create_author
        create_author(author, name)
    for (author, folder), identifier in new_collections.items():
        import yaml
        metadata = {"record_type": "collection", "id": identifier, "archive_id": identifier,
                    "title": identifier.replace("-", " ").title(), "slug": identifier,
                    "permalink": f"/zbirke/{identifier}/", "type": "mixed-collection"}
        metadata["author"] = author
        target = collections / author / folder / "index.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as output:
            output.write("---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n")
    for path, patch in updates:
        rewrite_front_matter(path, patch)
