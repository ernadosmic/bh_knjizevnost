"""Check spacing and every-fifth-line labels in an actual, multipage PDF."""
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from generate_downloads import run_pandoc


def main():
    for tool in ("pandoc", "xelatex", "pdftotext"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} must be on PATH to check PDF rendering.")

    # Include source newlines, blank lines, inline formatting, a wrapped source
    # line, and enough text to check that numbering continues across pages.
    rows = []
    for index in range(1, 106):
        row = f"Row{index:03}"
        if index == 3:
            row = f"*{row}*"
        if index == 12:
            row += " continuation" * 80
        rows.append(row + ("\n\n" if index % 10 == 0 else "\n"))

    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "spacing.md"
        output = Path(directory) / "spacing.pdf"
        source.write_text("".join(rows), encoding="utf-8")
        run_pandoc(source, output, {"title": "Rendering check", "author": ""}, True)
        result = subprocess.run(
            ["pdftotext", "-bbox", str(output), "-"],
            capture_output=True, check=True, encoding="utf-8",
        )

    document = ET.fromstring(result.stdout)
    pages = document.findall(".//{*}page")
    assert len(pages) > 1, "The fixture must exercise page breaks"
    line_count = 0
    labels = []
    positions = {}
    indents = {}
    body_margin = float('inf')
    for page in pages:
        words = page.findall(".//{*}word")
        body = [w for w in words if re.fullmatch(r"Row\d{3}|continuation", w.text or "")]
        if not body:
            continue
        baselines = sorted({round(float(w.get("yMax")), 1) for w in body})
        margin = min(float(w.get("xMin")) for w in body)
        body_margin = min(body_margin, margin)
        for word in body:
            positions[word.text] = float(word.get("yMax"))
            if word.text.startswith("Row"):
                indents[word.text] = float(word.get("xMin"))
        numbers = [w for w in words if (w.text or "").isdigit() and float(w.get("xMax")) < margin]
        for number in numbers:
            baseline = float(number.get("yMax"))
            closest = min(range(len(baselines)), key=lambda i: abs(baselines[i] - baseline))
            assert abs(baselines[closest] - baseline) < 4, "Label must align with its text line"
            expected = line_count + closest + 1
            assert int(number.text) == expected, f"Expected line {expected}, got {number.text}"
            labels.append(int(number.text))
        line_count += len(baselines)

    tight = positions["Row002"] - positions["Row001"]
    assert 8 < tight < 20, "A single Markdown newline must have ordinary line spacing"
    assert abs((positions["Row004"] - positions["Row003"]) - tight) < 0.5
    gap = positions["Row011"] - positions["Row010"]
    assert gap > tight + 8, "A blank Markdown line must add a visible paragraph gap"
    for row in ("Row002", "Row003", "Row004", "Row011", "Row012", "Row013"):
        assert 13 < indents[row] - body_margin < 17, \
            f"{row}: source lines must start with a 1.5 em indent; wrapped lines stay flush"
    assert line_count > 105, "Wrapped source lines must count as multiple printed lines"
    assert labels == list(range(5, line_count + 1, 5)), "Print every fifth line, continuously across pages"
    print("Passed: PDF newline indents, spacing, blank-line gaps, wrapping, and continuous labels 5, 10, 15, ...")


if __name__ == "__main__":
    main()
