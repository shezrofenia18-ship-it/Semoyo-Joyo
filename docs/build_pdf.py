"""Render docs/PANDUAN-PENGGUNA.md -> docs/PANDUAN-PENGGUNA.pdf via headless Chrome."""
import re
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
MD = ROOT / "PANDUAN-PENGGUNA.md"
HTML = ROOT / "PANDUAN-PENGGUNA.html"
PDF = ROOT / "PANDUAN-PENGGUNA.pdf"
LOGO = (ROOT.parent / "frontend" / "public" / "logo.png").resolve()

src = re.sub(r"(📷 \*\*\[[^\]]+\]\*\*)\n(?=📷)", r"\1\n\n", MD.read_text(encoding="utf-8"))
body = markdown.markdown(src, extensions=["tables", "sane_lists"])
body = re.sub(
    r"<p>📷 <strong>\[Tangkapan layar: (.*?)\]</strong></p>",
    r'<div class="shot"><span class="cam">📷</span><div><b>Placeholder tangkapan layar</b><br>\1</div></div>',
    body,
)
body = body.replace("<hr />", '<hr class="sep" />')
body = re.sub(r"<h1>(# )?BAGIAN", r'<h1 class="part">BAGIAN', body)

css = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2937; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; page-break-after: always; border-left: 8px solid #F5C400; padding-left: 28px; }
.cover img { height: 70px; margin-bottom: 40px; }
.cover h1 { font-size: 34pt; color: #0B4EA2; margin: 0 0 8px; line-height: 1.1; }
.cover h2 { font-size: 16pt; color: #374151; font-weight: 500; margin: 0 0 30px; border: 0; }
.cover .meta { color: #6b7280; font-size: 10pt; }
h1 { font-size: 20pt; color: #0B4EA2; margin: 26px 0 10px; padding-bottom: 6px; border-bottom: 3px solid #F5C400; page-break-after: avoid; }
h1.part { page-break-before: always; background: #0B4EA2; color: #fff; padding: 14px 16px; border-bottom: 6px solid #F5C400; font-size: 16pt; letter-spacing: .5px; }
h2 { font-size: 15pt; color: #0B4EA2; margin: 24px 0 8px; page-break-after: avoid; page-break-before: always; }
h2:first-of-type, h1 + h2, h1.part + h2 { page-break-before: auto; }
h3 { font-size: 12pt; color: #111827; margin: 18px 0 6px; page-break-after: avoid; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0 6px 0; padding-left: 22px; }
li { margin: 3px 0; }
code { background: #eef2ff; color: #1e3a8a; padding: 1px 5px; border-radius: 4px; font-size: 9.5pt; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 12px; font-size: 9.5pt; page-break-inside: avoid; }
th { background: #0B4EA2; color: #fff; text-align: left; padding: 6px 8px; }
td { border: 1px solid #d1d5db; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
blockquote { margin: 10px 0; padding: 8px 14px; background: #fffbea; border-left: 4px solid #F5C400; color: #374151; }
blockquote p { margin: 2px 0; }
hr.sep { border: 0; border-top: 1px dashed #cbd5e1; margin: 18px 0; }
.shot { display: flex; gap: 12px; align-items: center; border: 2px dashed #94a3b8; background: #f1f5f9; border-radius: 10px; padding: 14px 16px; margin: 12px 0; min-height: 88px; color: #475569; font-size: 9.5pt; page-break-inside: avoid; }
.shot .cam { font-size: 22pt; }
.shot b { color: #0B4EA2; }
.toc-note { font-size: 9pt; color: #6b7280; }
"""

# Cover: pull first two headings out of body
body = re.sub(r"^<h1>Panduan Pengguna Lengkap</h1>\s*<h2>(.*?)</h2>", "", body, count=1, flags=re.S)
cover = f"""
<div class="cover">
  <img src="file://{LOGO}" alt="Semoyo Joyo" />
  <h1>Panduan Pengguna Lengkap</h1>
  <h2>Semoyo Joyo — B2B E-Commerce + Mini ERP</h2>
  <div class="meta">Versi 1.0 · Juni 2026 · Dokumen internal untuk staf Admin &amp; Owner<br>
  Kotak bergaris putus-putus berlogo kamera adalah placeholder tangkapan layar.</div>
</div>
"""

HTML.write_text(f"<!doctype html><html lang='id'><head><meta charset='utf-8'><style>{css}</style></head><body>{cover}{body}</body></html>", encoding="utf-8")

subprocess.run(
    ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
     f"--print-to-pdf={PDF}", f"file://{HTML}"],
    check=True, capture_output=True, timeout=120,
)
print(f"OK -> {PDF} ({PDF.stat().st_size // 1024} KB)")
