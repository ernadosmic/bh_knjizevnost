"""Regression checks for the unified archive tree, using isolated fixtures."""
import tempfile
import unittest
from pathlib import Path
import yaml
from prepare_archive import prepare
from sync_authors import read_front_matter, split_document
from work_tree import work_paths

class EditorSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tree = self.root / "_works"
        self.tree.mkdir()

    def write(self, filename, body="Text\n", **metadata):
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n" + body, encoding="utf-8")
        return path

    def test_indexes_and_arbitrary_work_filenames(self):
        author = self.write("_works/writer/index.md", name="Corrected Name")
        collection = self.write("_works/writer/book/index.md", title="Corrected Title")
        work = self.write("_works/writer/book/anything at all.md", id="PK0001", title="Work", author="stale", zbirka="stale", permalink="/old/link/")
        prepare(self.root)
        self.assertEqual(work_paths(self.tree), [work])
        self.assertEqual(read_front_matter(author)["record_type"], "author")
        self.assertEqual(read_front_matter(collection)["record_type"], "collection")
        data = read_front_matter(work)
        self.assertEqual((data["id"], data["author"], data["author_name"], data["zbirka"]), ("PK0001", "writer", "Corrected Name", "book"))
        renamed = work.with_name("different.md")
        work.rename(renamed)
        prepare(self.root)
        self.assertEqual(data, read_front_matter(renamed))
        self.assertEqual(data["permalink"], "/old/link/")

    def test_moving_work_preserves_identity_and_text(self):
        work = self.write("_works/first/book/poem.md", title="A --- title", body="Line one\n\n---\nLine two\n")
        prepare(self.root)
        before = read_front_matter(work)
        body = split_document(work)[2]
        target = self.tree / "second/different-name.md"
        target.parent.mkdir()
        work.rename(target)
        prepare(self.root)
        after = read_front_matter(target)
        for field in ("id", "archive_id", "slug", "permalink"):
            self.assertEqual(after[field], before[field])
        self.assertEqual(after["author"], "second")
        self.assertEqual(after["zbirka"], "")
        self.assertEqual(after["zbirka_order"], "")
        self.assertEqual(split_document(target)[2], body)
        self.assertTrue((self.tree / "second/index.md").exists())

    def test_moving_collection_updates_author_and_children(self):
        self.write("_works/first/index.md", name="First")
        collection = self.write("_works/first/book/index.md", id="book", title="Book", author="first")
        work = self.write("_works/first/book/poem.md", title="Poem")
        prepare(self.root)
        before = read_front_matter(work)
        (self.tree / "second").mkdir()
        collection.parent.rename(self.tree / "second/book")
        prepare(self.root)
        self.assertEqual(read_front_matter(self.tree / "second/book/index.md")["author"], "second")
        data = read_front_matter(self.tree / "second/book/poem.md")
        self.assertEqual(data["author"], "second")
        self.assertEqual(data["permalink"], before["permalink"])
        self.assertEqual(data["zbirka_order"], before["zbirka_order"])

    def test_automatic_positions_and_no_repeated_writes(self):
        self.write("_works/writer/book/existing.md", title="Existing", zbirka="book", zbirka_order=4)
        later = self.write("_works/writer/book/a-later.md", title="Later", created_at="2026-09-23T10:00:00Z")
        earlier = self.write("_works/writer/book/b-earlier.md", title="Earlier", created_at="2026-09-23T09:00:00Z")
        prepare(self.root)
        self.assertEqual(read_front_matter(earlier)["zbirka_order"], 5)
        self.assertEqual(read_front_matter(later)["zbirka_order"], 6)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.tree.rglob("*.md")}
        prepare(self.root)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_duplicate_work_identity_fails_before_writes(self):
        self.write("_works/writer/a.md", title="First", id="SAME")
        self.write("_works/writer/b.md", title="Second", id="SAME")
        before = {p: p.read_bytes() for p in work_paths(self.tree)}
        with self.assertRaisesRegex(ValueError, "Duplicate ID"):
            prepare(self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse((self.tree / "writer/index.md").exists())

    def test_duplicate_collection_identity_is_rejected(self):
        self.write("_works/first/book/index.md", title="First book")
        self.write("_works/second/book/index.md", title="Second book")
        with self.assertRaisesRegex(ValueError, "Duplicate collection ID"):
            prepare(self.root)

    def test_invalid_positions_do_not_assign_new_ones(self):
        self.write("_works/writer/book/a.md", title="First", zbirka="book", zbirka_order=1)
        self.write("_works/writer/book/b.md", title="Second", zbirka="book", zbirka_order=1)
        new = self.write("_works/writer/book/new.md", title="New", zbirka="book")
        with self.assertRaisesRegex(ValueError, "both use order"):
            prepare(self.root)
        self.assertNotIn("zbirka_order", read_front_matter(new))

    def test_migration_preserves_bodies_links_and_duplicate_titles(self):
        self.write("_authors/writer.md", name="Writer", id="writer", body="Biography\n")
        self.write("_zbirke/book.md", title="Book", id="book", author="writer", body="Introduction\n")
        self.write("_works/legacy-one.md", title="Same", author="writer", zbirka="book", id="ONE", permalink="/one/")
        self.write("_works/legacy-two.md", title="Same", author="writer", zbirka="book", id="TWO", permalink="/two/")
        prepare(self.root, migrate=True)
        self.assertFalse((self.root / "_authors").exists())
        self.assertFalse((self.root / "_zbirke").exists())
        self.assertEqual({p.name for p in work_paths(self.tree)}, {"same.md", "same-2.md"})
        self.assertEqual({read_front_matter(p)["permalink"] for p in work_paths(self.tree)}, {"/one/", "/two/"})
        self.assertEqual(split_document(self.tree / "writer/index.md")[2], "\nBiography\n")
        self.assertEqual(split_document(self.tree / "writer/book/index.md")[2], "\nIntroduction\n")

if __name__ == "__main__":
    unittest.main()
