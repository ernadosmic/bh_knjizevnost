"""Check matching website/download paragraph and verse handling with real parsers."""
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    {"text": "First passage.\nSecond passage.\n\nThird passage.\nFourth passage.\n"},
    {"text": "First *italic\ncontinued* passage.\n\n## Heading\n\nAfter heading.\nNext passage.\n"},
    {"text": "Prose.\n\n```verse\nVerse one\nVerse two\n```\n\nMore prose.\n"},
    {"text": "Verse one\nVerse two\n\nNext stanza\n", "poetry": True},
    {"text": "- Item one\n- Item two\n\n```text\nCode one\nCode two\n```\n\n> Quote one\n> Quote two\n"},
]


def run(command, source):
    return subprocess.run(command, input=source, text=True, encoding="utf-8",
                          capture_output=True, check=True, cwd=ROOT).stdout


def main():
    bundle, pandoc = shutil.which("bundle"), shutil.which("pandoc")
    if not bundle or not pandoc:
        raise SystemExit("Bundler and Pandoc must be on PATH to check rendering.")
    ruby = """
require 'json'
require 'jekyll'
require './_plugins/work_paragraphs'
cases = JSON.parse(STDIN.read)
puts JSON.generate(cases.map { |c| WorkParagraphs.render(c['text'], poetry: c['poetry']) })
"""
    ruby = "; ".join(ruby.strip().splitlines())
    outputs = json.loads(run([bundle, "exec", "ruby", "-e", ruby], json.dumps(CASES)))
    html = [ET.fromstring("<main>" + output + "</main>") for output in outputs]

    paragraphs = html[0].findall("p")
    assert len(paragraphs) == 4, "Single newlines must create separate website paragraphs"
    assert [p.get("class") for p in paragraphs] == [None, None, "paragraph-gap", None], \
        "Only a source blank line should create the larger website gap"
    assert [p.findtext("em") for p in html[1].findall("p")[:2]] == ["italic", "\ncontinued"]
    assert html[1].find("h2") is not None
    verse = html[2].find("p[@class='verse']")
    assert verse is not None and len(verse.findall("br")) == 1
    assert len(html[3].findall("p[@class='verse']")) == 2
    assert len(html[4].findall("ul/li")) == 2
    assert "Code one\nCode two" in "".join(html[4].find(".//code").itertext())
    assert len(html[4].findall("blockquote/p")) == 1

    documents = []
    for case in CASES:
        command = [pandoc, "--from=markdown+hard_line_breaks", "--to=json",
                   "--lua-filter", str(ROOT / "scripts/work_paragraphs.lua")]
        if case.get("poetry"):
            command += ["--metadata", "work-type=poetry"]
        documents.append(json.loads(run(command, case["text"]))["blocks"])
    assert [b["t"] for b in documents[0]] == ["Para", "RawBlock", "Para", "RawBlock", "Para", "RawBlock", "Para"]
    assert [b["t"] for b in documents[1]] == ["Para", "RawBlock", "Para", "Header", "Para", "Para"]
    assert any(
        any(i["t"] == "Emph" for i in block["c"]) for block in documents[1] if block["t"] == "Para"
    )
    assert [b["t"] for b in documents[2]] == ["Para", "LineBlock", "Para"]
    assert len(documents[2][1]["c"]) == 2
    assert [b["t"] for b in documents[3]] == ["LineBlock", "LineBlock"]
    assert [b["t"] for b in documents[4]] == ["BulletList", "CodeBlock", "BlockQuote"]
    assert any(b["t"] == "RawBlock" and "addvspace" in b["c"][1] for b in documents[0]), \
        "A source blank line must create PDF paragraph spacing"
    print("Passed: source newline spacing, inline formatting, verse, poetry, and Markdown blocks in both renderers.")


if __name__ == "__main__":
    main()
