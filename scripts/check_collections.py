"""Check collection contents, counts, and work backlinks in the built site."""
from html.parser import HTMLParser
from generate_downloads import ROOT, read_document


class Links(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.current = None
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = dict(attrs)
            self.current["text"] = ""

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def page(url):
    return ROOT / "_site" / url.strip("/") / "index.html"


def main():
    works = [read_document(p)[0] for p in (ROOT / "_works").glob("*.md")]
    authors = {read_document(p)[0]["id"]: read_document(p)[0]
               for p in (ROOT / "_authors").glob("*.md")}
    index = Links(page("/zbirke/")).links
    for path in (ROOT / "_zbirke").glob("*.md"):
        collection, _ = read_document(path)
        members = [w for w in works if w.get("zbirka") == collection["archive_id"]]
        cards = [link for link in Links(page(collection["permalink"])).links
                 if "work-card" in link.get("class", "").split()]
        assert len(cards) == len(members), f"Wrong contents for {collection['title']}"
        for work in members:
            assert any(link.get("href", "").endswith(work["permalink"]) for link in cards)
            assert any(link.get("href", "").endswith(collection["permalink"])
                       for link in Links(page(work["permalink"])).links), "Missing work backlink"
        listings = [index]
        if collection.get("author") in authors:
            listings.append(Links(page(authors[collection["author"]]["permalink"])).links)
        for links in listings:
            card = next(link for link in links
                        if link.get("href", "").endswith(collection["permalink"])
                        and "work-card" in link.get("class", "").split())
            assert f"{len(members)} djela" in card["text"], "Wrong collection work count"
    print("Passed: collection contents, collection/author counts, and work backlinks.")


if __name__ == "__main__":
    main()
