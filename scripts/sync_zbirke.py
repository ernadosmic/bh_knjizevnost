#!/usr/bin/env python3
"""Normalize literary collection slugs and work references."""

from pathlib import Path

from new_work import slugify
from sync_authors import read_front_matter, rewrite_front_matter

ROOT = Path(__file__).resolve().parent.parent
WORKS = ROOT / "_works"
ZBIRKE = ROOT / "_zbirke"


def normalize_zbirke():
    aliases = {}
    problems = []

    ZBIRKE.mkdir(parents=True, exist_ok=True)

    for original_path in sorted(ZBIRKE.glob("*.md")):
        data = read_front_matter(original_path)
        title = str(data.get("title") or "").strip()
        if not title:
            problems.append("%s: missing collection title" % original_path.name)
            continue

        desired_id = slugify(title)
        if not desired_id:
            problems.append("%s: could not derive collection slug" % original_path.name)
            continue

        old_ids = {
            original_path.stem,
            str(data.get("id") or "").strip(),
            str(data.get("archive_id") or "").strip(),
            str(data.get("slug") or "").strip(),
        }
        old_ids.discard("")

        target_path = ZBIRKE / ("%s.md" % desired_id)
        if target_path.exists() and target_path != original_path:
            problems.append(
                "%s: cannot rename to %s because that collection already exists"
                % (original_path.name, target_path.name)
            )
            continue

        rewrite_front_matter(
            original_path,
            {
                "id": desired_id,
                "archive_id": desired_id,
                "slug": desired_id,
                "permalink": "/zbirke/%s/" % desired_id,
            },
        )

        if target_path != original_path:
            original_path.rename(target_path)
            print(
                "Renamed %s -> %s"
                % (original_path.relative_to(ROOT), target_path.relative_to(ROOT))
            )

        for old_id in old_ids | {desired_id}:
            aliases[old_id] = desired_id

    return aliases, problems


def normalize_work_membership(aliases):
    problems = []
    used_orders = {}

    for work_path in sorted(WORKS.glob("*.md")):
        data = read_front_matter(work_path)
        zbirka_id = str(data.get("zbirka") or "").strip()
        if not zbirka_id:
            continue

        desired_id = aliases.get(zbirka_id, zbirka_id)
        zbirka_path = ZBIRKE / ("%s.md" % desired_id)
        if not zbirka_path.exists():
            problems.append(
                "%s: collection %s does not exist" % (work_path.name, desired_id)
            )
            continue

        if desired_id != zbirka_id:
            rewrite_front_matter(work_path, {"zbirka": desired_id})
            print("Updated %s" % work_path.relative_to(ROOT))

        order = data.get("zbirka_order")
        if order in (None, ""):
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

    return problems


def main():
    aliases, problems = normalize_zbirke()
    problems.extend(normalize_work_membership(aliases))

    if problems:
        print("\nCollection consistency errors:")
        for issue in problems:
            print("- %s" % issue)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
