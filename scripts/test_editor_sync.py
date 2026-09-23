"""Regression checks for automated editor metadata, using isolated archives."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
import sync_authors
import sync_zbirke


class EditorSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("_works", "_authors", "_zbirke"):
            (self.root / directory).mkdir()
        for module in (sync_authors, sync_zbirke):
            for name, value in {
                "ROOT": self.root, "WORKS": self.root / "_works",
                "AUTHORS": self.root / "_authors", "ZBIRKE": self.root / "_zbirke",
            }.items():
                if hasattr(module, name):
                    patcher = patch.object(module, name, value)
                    patcher.start()
                    self.addCleanup(patcher.stop)

    def write(self, filename, **metadata):
        path = self.root / filename
        path.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\nText\n", encoding="utf-8")
        return path

    def test_name_corrections_preserve_identities_and_references(self):
        author = self.write("_authors/original-author.md", id="original-author", name="Corrected Name")
        collection = self.write("_zbirke/original-title.md", id="original-title", title="Corrected Title", author="original-author")
        work = self.write("_works/legacy.md", id="PK0001", title="Work", slug="work", author="original-author", zbirka="original-title")
        aliases, names, errors = sync_authors.normalize_authors()
        self.assertEqual(errors, [])
        self.assertEqual(sync_authors.normalize_works(aliases, names), [])
        collection_aliases, errors = sync_zbirke.normalize_zbirke()
        self.assertEqual(errors, [])
        self.assertEqual(sync_zbirke.normalize_work_membership(collection_aliases), [])
        self.assertTrue(author.exists())
        self.assertTrue(collection.exists())
        self.assertEqual(sync_authors.read_front_matter(author)["id"], "original-author")
        self.assertEqual(sync_authors.read_front_matter(collection)["permalink"], "/zbirke/original-title/")
        data = sync_authors.read_front_matter(work)
        self.assertEqual(data["author"], "original-author")
        self.assertEqual(data["author_name"], "Corrected Name")
        self.assertEqual(data["id"], "PK0001")

    def test_automatic_positions_append_and_are_idempotent(self):
        self.write("_zbirke/book.md", id="book", title="Book")
        self.write("_works/z-existing.md", zbirka="book", zbirka_order=4)
        later = self.write("_works/a-later.md", zbirka="book", created_at="2026-09-23T10:00:00Z")
        earlier = self.write("_works/b-earlier.md", zbirka="book", created_at="2026-09-23T09:00:00Z")
        self.assertEqual(sync_zbirke.normalize_work_membership({}), [])
        self.assertEqual(sync_authors.read_front_matter(earlier)["zbirka_order"], 5)
        self.assertEqual(sync_authors.read_front_matter(later)["zbirka_order"], 6)
        before = {p: p.read_bytes() for p in (self.root / "_works").glob("*.md")}
        self.assertEqual(sync_zbirke.normalize_work_membership({}), [])
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_invalid_explicit_positions_do_not_partially_assign_new_ones(self):
        self.write("_zbirke/book.md", id="book", title="Book")
        self.write("_works/a.md", zbirka="book", zbirka_order=1)
        self.write("_works/b.md", zbirka="book", zbirka_order=1)
        new = self.write("_works/new.md", zbirka="book")
        self.assertTrue(sync_zbirke.normalize_work_membership({}))
        self.assertNotIn("zbirka_order", sync_authors.read_front_matter(new))

    def test_inline_author_creation_reuses_an_existing_record(self):
        self.write("_works/a.md", title="First", slug="first", author="new-author", author_name="New Author")
        self.write("_works/b.md", title="Second", slug="second", author="new-author", author_name="New Author")
        self.assertEqual(sync_authors.normalize_works({}, {}), [])
        self.assertEqual(len(list((self.root / "_authors").glob("*.md"))), 1)
        self.assertEqual(sync_authors.read_front_matter(self.root / "_authors/new-author.md")["name"], "New Author")

    def test_inline_author_reuses_a_corrected_name_with_an_older_id(self):
        self.write("_authors/old-name.md", id="old-name", name="Corrected Name")
        work = self.write("_works/new.md", title="Work", slug="work", author="corrected-name", author_name="Corrected Name")
        aliases, names, errors = sync_authors.normalize_authors()
        self.assertEqual(errors, [])
        self.assertEqual(sync_authors.normalize_works(aliases, names), [])
        self.assertEqual(sync_authors.read_front_matter(work)["author"], "old-name")
        self.assertFalse((self.root / "_authors/corrected-name.md").exists())


if __name__ == "__main__":
    unittest.main()
