"""Generate reproducible PDF, EPUB, and archive manifest files from _works Markdown."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml
from work_tree import work_paths

ROOT = Path(__file__).resolve().parents[1]
WORKS = ROOT / "_works"
AUTHORS = ROOT / "_authors"
PDF_DIR = ROOT / "assets" / "downloads" / "pdf"
EPUB_DIR = ROOT / "assets" / "downloads" / "epub"
PARAGRAPH_FILTER = ROOT / "scripts" / "work_paragraphs.lua"


def read_document(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not match:
        raise ValueError(f"Missing YAML front matter: {path}")
    return yaml.safe_load(match.group(1)) or {}, match.group(2).lstrip()


def run_pandoc(input_path: Path, output_path: Path, metadata: dict, pdf: bool) -> None:
    command = ["pandoc", str(input_path), "--from=markdown+hard_line_breaks", "-o", str(output_path), "--standalone"]
    command += ["--lua-filter", str(PARAGRAPH_FILTER), "--metadata", f"work-type={metadata.get('type', '')}"]
    command += ["--metadata", f"title={metadata['title']}", "--metadata", f"author={metadata['author']}"]
    if metadata.get("language"):
        command += ["--metadata", f"lang={metadata['language']}"]
    if pdf:
        command += ["--pdf-engine=xelatex", "-V", "geometry:a4paper", "-V", "mainfont=DejaVu Serif"]
        command += [
            "-V", "indent=true",
            # Hard line breaks stay within a paragraph; only blank source lines
            # start a new paragraph and receive this extra vertical space.
            "-V", r"header-includes=\usepackage{lineno}\modulolinenumbers[5]\leftlinenumbers\renewcommand{\linenumberfont}{\normalfont\tiny\color[gray]{0.55}}\setlength{\linenumbersep}{1em}\setlength{\parindent}{1.5em}\setlength{\parskip}{1.3em}",
            # Start counting after the title; leave the opening paragraph flush left.
            "-V", r"include-before=\linenumbers\makeatletter\@afterindentfalse\@afterheading\makeatother",
        ]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    from prepare_archive import prepare
    prepare(ROOT)
    if not shutil.which("pandoc"):
        raise SystemExit("Pandoc is required to generate downloads. Install it and retry.")
    author_data = {}
    for path in AUTHORS.glob("*.md"):
        metadata, _ = read_document(path)
        author_data[metadata["id"]] = metadata
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    EPUB_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in work_paths(WORKS):
        metadata, body = read_document(path)
        author = author_data.get(metadata.get("author", ""), {})
        author_name = author.get("name", metadata.get("author", ""))
        filename = f"{metadata['id']}-{metadata['slug']}"
        source_note = "\n\n---\n\n## Arhivska bilješka {.archive-note}\n\n"
        source_note += f"**Arhivski identifikator:** {metadata['id']}\n\n"
        if metadata.get("year"):
            source_note += f"**Godina:** {metadata['year']}\n\n"
        source_note += f"**Status prava:** {metadata.get('rights', 'unknown')}\n"
        if metadata.get("rights_note"):
            source_note += f"\n{metadata['rights_note']}\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "work.md"
            # Pandoc's standalone templates render the title and author from metadata.
            source.write_text(f"{body}{source_note}", encoding="utf-8")
            download_metadata = {"title": metadata["title"], "author": author_name, "language": metadata.get("language"), "type": metadata.get("type")}
            run_pandoc(source, PDF_DIR / f"{filename}.pdf", download_metadata, True)
            run_pandoc(source, EPUB_DIR / f"{filename}.epub", download_metadata, False)
        manifest.append({
            "id": metadata["id"],
            "source_path": path.relative_to(ROOT).as_posix(),
            "title": metadata["title"],
            "author": author_name,
            "author_id": metadata.get("author", ""),
            "year": metadata.get("year"),
            "language": metadata.get("language", ""),
            "type": metadata.get("type", ""),
            "rights": metadata.get("rights", "unknown"),
            "url": metadata.get("permalink") or f"/djela/{metadata.get('author', '')}/{metadata['slug']}/",
            "pdf": f"/assets/downloads/pdf/{filename}.pdf",
            "epub": f"/assets/downloads/epub/{filename}.epub",
        })
    (ROOT / "archive-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(manifest)} work(s), PDFs, EPUBs, and archive-manifest.json")


if __name__ == "__main__":
    main()
