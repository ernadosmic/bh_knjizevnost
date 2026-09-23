"""Synchronize folder membership and derived metadata before any archive build."""
import argparse
from pathlib import Path

import sync_authors
import sync_zbirke
from work_tree import apply_placements, migrate_flat


def prepare(root, migrate=False):
    root = Path(root).resolve()
    works, authors, collections = (root / name for name in ("_works", "_authors", "_zbirke"))
    for module in (sync_authors, sync_zbirke):
        module.ROOT, module.WORKS, module.ZBIRKE = root, works, collections
    sync_authors.AUTHORS = authors
    if migrate:
        for source, target in migrate_flat(works):
            print(f"Moved {source.relative_to(root)} -> {target.relative_to(root)}")
    apply_placements(works, authors, collections)
    aliases, names, errors = sync_authors.normalize_authors()
    errors.extend(sync_authors.normalize_works(aliases, names))
    errors.extend(sync_authors.normalize_zbirke(aliases))
    aliases, collection_errors = sync_zbirke.normalize_zbirke()
    errors.extend(collection_errors)
    errors.extend(sync_zbirke.normalize_work_membership(aliases))
    if errors:
        raise ValueError("\n".join(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--migrate", action="store_true", help="move legacy flat works into their metadata-defined folders")
    args = parser.parse_args()
    prepare(args.root, args.migrate)
