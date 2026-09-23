"""Check matching website/download paragraph and verse handling with real parsers."""
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from literary_markdown import literal_dashes

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    {"text": "First passage.\nSecond passage.\n\nThird passage.\nFourth passage.\n"},
    {"text": "First *italic\ncontinued* passage.\n\n## Heading\n\nAfter heading.\nNext passage.\n"},
    {"text": "Prose.\n\n```verse\nVerse one\nVerse two\n```\n\nMore prose.\n"},
    {"text": "Verse one\nVerse two\n\nNext stanza\n", "poetry": True},
    {"text": "* Item one\n* Item two\n\n```text\nCode one\nCode two\n```\n\n> Quote one\n> Quote two\n"},
    {"text": "Intro.\n- First *speaker*.\n- Second speaker.\n\n- Third speaker.\n"},
    {"text": "- First verse\n- Second verse\n\n- Next stanza\n", "poetry": True},
    {"text": "````markdown\n- Code dash\n```\n- Still code\n````\n\n    - Indented code\n\n> - Quoted dialogue\n\n- - -\n\n\\- Already escaped\n\n+ Deliberate bullet\n"},
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
puts JSON.generate(cases.map { |c| { html: WorkParagraphs.render(c['text'], poetry: c['poetry']), source: WorkParagraphs.literal_dashes(c['text']) } })
"""
    ruby = "; ".join(ruby.strip().splitlines())
    rendered = json.loads(run([bundle, "exec", "ruby", "-e", ruby], json.dumps(CASES)))
    assert [r["source"] for r in rendered] == [literal_dashes(c["text"]) for c in CASES], "Website and download escaping must agree"
    outputs = [r["html"] for r in rendered]
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
    for index in (5, 6):
        assert html[index].find(".//ul") is None, "Dialogue must not become a bullet list"
        assert "".join(html[index].itertext()).count("- ") == 3
    assert html[5].find("p/em") is not None, "Keep emphasis within dialogue"
    assert len(html[6].findall("p[@class='verse']")) == 2
    assert "- Code dash\n```\n- Still code" in "".join(html[7].find(".//code").itertext())
    assert "- Quoted dialogue" in "".join(html[7].find("blockquote").itertext())
    assert html[7].find("hr") is not None
    assert len(html[7].findall("ul/li")) == 1

    documents = []
    for case in CASES:
        command = [pandoc, "--from=markdown+hard_line_breaks", "--to=json",
                   "--lua-filter", str(ROOT / "scripts/work_paragraphs.lua")]
        if case.get("poetry"):
            command += ["--metadata", "work-type=poetry"]
        documents.append(json.loads(run(command, literal_dashes(case["text"])))["blocks"])
    assert [b["t"] for b in documents[0]] == ["Para", "Para"]
    assert [b["t"] for b in documents[1]] == ["Para", "Header", "Para"]
    assert any(
        any(i["t"] == "Emph" for i in block["c"]) for block in documents[1] if block["t"] == "Para"
    )
    assert [b["t"] for b in documents[2]] == ["Para", "LineBlock", "Para"]
    assert len(documents[2][1]["c"]) == 2
    assert [b["t"] for b in documents[3]] == ["LineBlock", "LineBlock"]
    assert [b["t"] for b in documents[4]] == ["BulletList", "CodeBlock", "BlockQuote"]
    assert [b["t"] for b in documents[5]] == ["Para", "Para"]
    assert [b["t"] for b in documents[6]] == ["LineBlock", "LineBlock"]
    for index in (5, 6):
        assert json.dumps(documents[index]).count('"c": "-"') == 3, "Downloads must retain literal dashes"
    assert documents[7][0]["c"][1] == "- Code dash\n```\n- Still code"
    assert [b["t"] for b in documents[7]] == ["CodeBlock", "CodeBlock", "BlockQuote", "HorizontalRule", "Para", "BulletList"]
    print("Passed: literal dialogue dashes, spacing, formatting, verse, poetry, code, and deliberate lists in both renderers.")


if __name__ == "__main__":
    main()
