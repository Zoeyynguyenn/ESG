#!/usr/bin/env python3
"""Convert Korean report Markdown to styled HTML and PDF (Edge/Chrome headless)."""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"

STYLE = """
:root {
  --bg: #f6f7fb;
  --text: #1d2433;
  --muted: #4a5468;
  --card: #ffffff;
  --accent: #1f6feb;
  --border: #d9e0ee;
  --table: #f8faff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Noto Sans KR", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
  line-height: 1.72;
  font-size: 15px;
}
.wrap {
  max-width: 980px;
  margin: 28px auto;
  padding: 30px 34px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
}
h1 { font-size: 30px; margin: 0 0 22px; color: #10213f; line-height: 1.3; }
h2 { font-size: 21px; margin: 28px 0 12px; color: #14305f; border-left: 5px solid var(--accent); padding-left: 10px; }
h3 { font-size: 17px; margin: 18px 0 8px; color: #1e3e73; }
p { margin: 0 0 10px; }
ul, ol { margin: 8px 0 12px 24px; padding: 0; }
li { margin: 4px 0; }
hr { border: 0; border-top: 1px solid var(--border); margin: 24px 0; }
code {
  background: #eef3ff;
  color: #1b3d8b;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 92%;
  white-space: normal;
}
pre.bar-chart {
  font-family: "Consolas", "Courier New", "D2Coding", "Malgun Gothic", monospace;
  white-space: pre;
  overflow-x: auto;
  background: #f3f5fa;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.55;
  margin: 10px 0 18px;
  letter-spacing: 0;
  word-break: normal;
}
table { width: 100%; border-collapse: collapse; margin: 12px 0 18px; table-layout: fixed; }
th, td { border: 1px solid var(--border); padding: 8px 10px; vertical-align: top; word-break: break-word; }
th { background: #eaf1ff; color: #132f5f; font-weight: 700; }
td { background: var(--table); }
em { color: var(--muted); }
@media print {
  body { background: #fff; }
  .wrap { margin: 0; max-width: none; border: 0; border-radius: 0; }
  h2 { break-after: avoid; }
  table { break-inside: avoid; }
  pre.bar-chart { break-inside: avoid; font-size: 11px; }
}
"""

BROWSERS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> Path:
    for p in BROWSERS:
        if p.is_file():
            return p
    raise FileNotFoundError("Edge/Chrome not found for PDF export")


def inline_format(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html_body(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_table = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("|") and "|" in stripped[1:]:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                out.append("<table><thead><tr>")
                out.extend(f"<th>{inline_format(c)}</th>" for c in cells)
                out.append("</tr></thead><tbody>")
                in_table = True
                i += 1
                if i < len(lines) and re.match(r"^\|[-:\s|]+\|$", lines[i].strip()):
                    i += 1
                continue
            if re.match(r"^[-:\s|]+$", stripped.replace("|", "")):
                i += 1
                continue
            out.append("<tr>")
            out.extend(f"<td>{inline_format(c)}</td>" for c in cells)
            out.append("</tr>")
            i += 1
            continue

        close_table()

        if stripped.startswith("```"):
            i += 1
            block_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            body = html.escape("\n".join(block_lines))
            out.append(f'<pre class="bar-chart">{body}</pre>')
            continue

        if stripped == "---":
            out.append("<hr />")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h1>{inline_format(stripped[2:])}</h1>")
            i += 1
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{inline_format(stripped[3:])}</h2>")
            i += 1
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{inline_format(stripped[4:])}</h3>")
            i += 1
            continue
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline_format(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(
                    f"<li>{inline_format(re.sub(r'^\\d+\\.\\s*', '', lines[i].strip()))}</li>"
                )
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        if stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 2:
            out.append(f"<p><em>{inline_format(stripped.strip('*'))}</em></p>")
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        out.append(f"<p>{inline_format(stripped)}</p>")
        i += 1

    close_table()
    return "\n    ".join(out)


def build_html(md_path: Path, title: str) -> str:
    body = md_to_html_body(md_path.read_text(encoding="utf-8"))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="wrap">
    {body}
  </main>
</body>
</html>
"""


def export_pdf(html_path: Path, pdf_path: Path) -> None:
    browser = find_browser()
    html_uri = html_path.resolve().as_uri()
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_uri,
    ]
    subprocess.run(cmd, check=True, timeout=120)


def process(md_path: Path) -> tuple[Path, Path]:
    stem = md_path.stem
    html_path = md_path.with_suffix(".html")
    pdf_path = md_path.with_suffix(".pdf")
    title = stem.replace("-", " ")
    html_path.write_text(build_html(md_path, title), encoding="utf-8")
    export_pdf(html_path, pdf_path)
    return html_path, pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Korean report MD to HTML+PDF")
    parser.add_argument("md_files", nargs="+", help="Markdown file paths")
    args = parser.parse_args()
    for raw in args.md_files:
        md_path = Path(raw).resolve()
        if not md_path.is_file():
            print(f"Missing: {md_path}", file=sys.stderr)
            return 1
        html_path, pdf_path = process(md_path)
        print(f"OK: {html_path}")
        print(f"OK: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
