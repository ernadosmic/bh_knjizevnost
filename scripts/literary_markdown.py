"""Protect literary dialogue dashes before Markdown parsing."""
import re


def literal_dashes(source: str) -> str:
    output = []
    fence = None
    for line in source.splitlines(keepends=True):
        # Ignore quote prefixes when recognizing code fences and separators.
        content = re.sub(r"^(?: {0,3}>[ \t]?)+", "", line).rstrip("\r\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", content)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        elif not re.fullmatch(r" {0,3}(?:-[ \t]*){3,}", content):
            line = re.sub(r"^((?: {0,3}>[ \t]?)* {0,3})-(?=[ \t]|$)", r"\1\\-", line)
        output.append(line)
    return "".join(output)
