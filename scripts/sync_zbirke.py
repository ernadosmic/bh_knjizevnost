#!/usr/bin/env python3
"""Keep collection identities stable and assign positions to newly added works."""

from pathlib import Path

from sync_authors import read_front_matter, rewrite_front_matter, safe_identifier
from work_tree import work_paths

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "_works"
ZBIRKE = WORKS


def normalize_zbirke():
    aliases = {}
    problems = []

    ZBIRKE.mkdir(parents=True, exist_ok=True)

    for original_path in sorted(ZBIRKE.glob("*/*/index.md")):
        data = read_front_matter(original_path)
        title = str(data.get("title") or "").strip()
        if not title:
            problems.append("%s: missing collection title" % original_path.name)
            continue

        desired_id = str(data.get("id") or data.get("archive_id") or original_path.parent.name).strip()
        public_slug = str(data.get("slug") or desired_id).strip()
        if not safe_identifier(desired_id) or not safe_identifier(public_slug):
            problems.append("%s: invalid collection identifier" % original_path.name)
            continue

        old_ids = {
            original_path.parent.name,
            str(data.get("id") or "").strip(),
            str(data.get("archive_id") or "").strip(),
            str(data.get("slug") or "").strip(),
        }
        old_ids.discard("")

        rewrite_front_matter(
            original_path,
            {
                "record_type": "collection",
                "author": original_path.parent.parent.name,
                "id": desired_id,
                "archive_id": desired_id,
                "slug": public_slug,
                "permalink": data.get("permalink") or "/zbirke/%s/" % public_slug,
            },
        )

        for old_id in old_ids | {desired_id}:
            aliases[old_id] = desired_id

    return aliases, problems


def normalize_work_membership(aliases):
    problems = []
    used_orders = {}
    collection_paths = {str(read_front_matter(p).get("id")): p for p in ZBIRKE.glob("*/*/index.md")}
    pending = []

    for work_path in work_paths(WORKS):
        data = read_front_matter(work_path)
        zbirka_id = str(data.get("zbirka") or "").strip()
        if not zbirka_id:
            continue

        desired_id = aliases.get(zbirka_id, zbirka_id)
        zbirka_path = collection_paths.get(desired_id)
        if not safe_identifier(desired_id) or not zbirka_path or not zbirka_path.exists():
            problems.append(
                "%s: collection %s does not exist" % (work_path.name, desired_id)
            )
            continue

        if desired_id != zbirka_id:
            rewrite_front_matter(work_path, {"zbirka": desired_id})
            print("Updated %s" % work_path.relative_to(ROOT))

        order = data.get("zbirka_order")
        if order in (None, ""):
            pending.append((str(data.get("created_at") or ""), work_path, desired_id))
            continue
        try:
            order_number = int(order)
        except (TypeError, ValueError):
            problems.append("%s: invalid collection order %r" % (work_path.name, order))
            continue
        if order_number < 1:
            problems.append("%s: collection order must be at least 1" % work_path.name)
            continue

        key = (desired_id, order_number)
        if key in used_orders:
            problems.append(
                "%s and %s both use order %s in collection %s"
                % (used_orders[key], work_path.name, order_number, desired_id)
            )
        else:
            used_orders[key] = work_path.name

    # Collect explicit positions first, then append new works in creation order.
    # This prevents collisions with positions found later in the directory.
    if not problems:
        highest = {}
        for collection_id, number in used_orders:
            highest[collection_id] = max(highest.get(collection_id, 0), number)
        for _, work_path, collection_id in sorted(pending):
            number = highest.get(collection_id, 0) + 1
            highest[collection_id] = number
            rewrite_front_matter(work_path, {"zbirka_order": number})
            print("Assigned position %s to %s" % (number, work_path.relative_to(ROOT)))

    return problems


def main():
    from prepare_archive import prepare
    prepare(ROOT)


if __name__ == "__main__":
    main()
