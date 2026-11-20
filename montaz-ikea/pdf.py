#!/usr/bin/env python3
"""README.md → podklad-montaz-ikea.pdf (bílý papír, A4) přes headless Chrome.

Jednoduchý převod jen pro použité prvky Markdownu: nadpisy, tabulky, obrázky, odrážky, **tučně**, *kurzíva*, ---.
Spuštění: python3 pdf.py
"""
import html
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def join_paragraphs(md):
    """Spojí řádky jednoho odstavce (Markdown zalomení uvnitř odstavce) do jednoho řádku."""
    res = []
    for line in md.splitlines():
        plain = line.strip() and not re.match(r"(#|\||!\[|- |---)", line)
        if plain and res and res[-1].strip() and not re.match(r"(#|\||!\[|---)", res[-1]):
            res[-1] += " " + line.strip()
        else:
            res.append(line)
    return res


def convert(md):
    out, table, lst = [], [], False
    for line in join_paragraphs(md) + [""]:
        if line.startswith("|"):
            table.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if table:
            has_head = any(table[0])
            rows = [r for r in table if not all(re.fullmatch(r":?-+:?", c) or not c for c in r)]
            out.append("<table>")
            for i, r in enumerate(rows):
                tag = "th" if i == 0 and has_head else "td"
                out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in r) + "</tr>")
            out.append("</table>")
            table = []
        if lst and not line.startswith("- "):
            out.append("</ul>")
            lst = False
        m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if m:
            out.append(f'<figure><img src="{m.group(2)}"><figcaption>{inline(m.group(1))}</figcaption></figure>')
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.strip() == "---":
            out.append("<hr>")
        elif line.startswith("- "):
            if not lst:
                out.append("<ul>")
                lst = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif line.strip():
            out.append(f"<p>{inline(line)}</p>")
    return "\n".join(out)


CSS = """
@page { size: A4; margin: 14mm 14mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 10.5pt; color: #111; background: #fff; }
h1 { font-size: 18pt; margin: 0 0 8px; }
h2 { font-size: 14pt; margin: 18px 0 6px; page-break-after: avoid; border-bottom: 2px solid #1f3a93; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; page-break-inside: avoid; }
td, th { border: 1px solid #999; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #eef1f8; }
figure { margin: 8px 0; page-break-inside: avoid; text-align: center; }
img { max-width: 100%; max-height: 105mm; border: 1px solid #ccc; }
figcaption { font-size: 9pt; color: #444; }
hr { border: 0; page-break-after: always; }
code { font-size: 9.5pt; }
"""

if __name__ == "__main__":
    md = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    page = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{convert(md)}</body></html>"
    src = os.path.join(HERE, "_podklad.html")
    with open(src, "w", encoding="utf-8") as f:
        f.write(page)
    pdf = os.path.join(HERE, "podklad-montaz-ikea.pdf")
    subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + src], check=True, stderr=subprocess.DEVNULL)
    os.remove(src)
    print("hotovo:", pdf, os.path.getsize(pdf) // 1024, "kB")
