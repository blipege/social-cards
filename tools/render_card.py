#!/usr/bin/env python3
"""
Render kartu headline blipege (versi putih yang disetujui) jadi PNG.
Teks di-render pakai kode, jadi ejaan & angka selalu benar.

Pakai:
  python3 tools/render_card.py --account blipege --payload /path/payload.json

Output: file PNG masuk ke <repo>/<account>/<tanggal>-<slug>-<rand>.png,
lalu skrip MENCETAK URL publik raw.githubusercontent. Skrip ini TIDAK push;
git add/commit/push dilakukan terpisah (lihat CARD_WORKFLOW.md di project).

Butuh: playwright + chromium (sudah ada di Cowork), font Inter (sudah ada di Cowork).
"""
import sys, json, argparse, datetime, re, pathlib, secrets
from playwright.sync_api import sync_playwright

REPO = "blipege/social-cards"
BRANCH = "main"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

TPL = """<!doctype html><html lang="id"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1350px}
body{font-family:'Inter Display','Inter',sans-serif;background:#FFFFFF;color:#141414;position:relative;overflow:hidden}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(20,20,20,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(20,20,20,.045) 1px,transparent 1px);background-size:90px 90px;mask:linear-gradient(180deg,transparent,#000 24%,#000 76%,transparent)}
.glow{position:absolute;width:620px;height:620px;right:-160px;top:-200px;background:radial-gradient(circle,__AMBER20__,rgba(0,0,0,0) 68%)}
.glow2{position:absolute;width:560px;height:560px;left:-180px;bottom:-200px;background:radial-gradient(circle,__ACCENT14__,rgba(0,0,0,0) 68%)}
.wrap{position:relative;height:100%;display:flex;flex-direction:column;padding:84px 84px 76px}
.top{display:flex;align-items:center;justify-content:space-between}
.pilar{font-size:26px;font-weight:800;letter-spacing:.26em;color:#141414;background:__AMBER__;padding:16px 26px 16px 28px;border-radius:100px}
.brand{font-size:30px;font-weight:800;letter-spacing:-.01em;color:#141414}.brand span{color:__ACCENT__}
.headline{margin-top:150px}.kicker{font-size:30px;font-weight:600;color:#7C828C;margin-bottom:34px}
h1{font-size:112px;line-height:.99;font-weight:800;letter-spacing:-.025em;color:#141414}h1 .red{color:__ACCENT__}
.arrow{display:inline-block;width:74px;height:74px;vertical-align:-10px;margin-left:8px}
.data{margin-top:auto;display:flex;align-items:flex-end;gap:40px;border-top:2px solid rgba(20,20,20,.1);padding-top:46px}
.stat .num{font-size:112px;font-weight:800;letter-spacing:-.03em;line-height:.9;color:__AMBER__}.stat .lbl{font-size:27px;font-weight:500;color:#7C828C;margin-top:18px}
.spacer{flex:1}.src{text-align:right;font-size:25px;font-weight:500;color:#9BA1A9;line-height:1.5}.src b{color:#4A4F57;font-weight:700}
.handle{position:absolute;left:0;right:0;bottom:40px;text-align:center;font-size:26px;font-weight:700;color:#B4B9C0}.handle b{color:#141414;font-weight:800}.handle b i{color:__ACCENT__;font-style:normal}
</style></head><body>
<div class="grid"></div><div class="glow"></div><div class="glow2"></div>
<div class="wrap">
<div class="top"><div class="pilar">__PILAR__</div><div class="brand">__WA__<span>__WB__</span></div></div>
<div class="headline"><div class="kicker">__KICKER__</div>
<h1>__HEAD__ <span class="red">__REDWORD__<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="__ACCENT__" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7l10 10"/><path d="M17 8v9h-9"/></svg></span></h1></div>
<div class="data"><div class="stat"><div class="num">__NUM__</div><div class="lbl">__LBL__</div></div><div class="spacer"></div><div class="src">__SRC__</div></div>
</div>
<div class="handle"><b>@__WA__<i>__WB__</i></b></div>
</body></html>"""

def hx(h, a):
    h = h.lstrip('#'); r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"

def build(acc, p):
    rep = {
        "__AMBER__": acc["amber"], "__ACCENT__": acc["accent"],
        "__AMBER20__": hx(acc["amber"], .20), "__ACCENT14__": hx(acc["accent"], .14),
        "__WA__": acc["wordmark_a"], "__WB__": acc["wordmark_b"],
        "__PILAR__": p["pilar"], "__KICKER__": p["kicker"],
        "__HEAD__": p["head"], "__REDWORD__": p["redword"],
        "__NUM__": p.get("num",""), "__LBL__": p.get("lbl",""), "__SRC__": p.get("src",""),
    }
    html = TPL
    for k,v in rep.items(): html = html.replace(k, v)
    if not p.get("num"):
        # tanpa angka sorotan: sembunyikan strip data
        html = html.replace('<div class="data">', '<div class="data" style="display:none">')
        # headline turun ke tengah biar ga ada ruang kosong di bawah
        html = html.replace('<div class="headline">', '<div class="headline" style="margin:auto 0;padding-bottom:60px">')
    if p.get("arrow", True) is False:
        html = re.sub(r'<svg class="arrow".*?</svg>', '', html, flags=re.S)
    return html

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--payload", required=True)
    a = ap.parse_args()
    accounts = json.load(open(REPO_ROOT/"tools"/"accounts.json"))
    if a.account not in accounts:
        sys.exit(f"ERROR: akun '{a.account}' tidak ada di tools/accounts.json")
    acc = accounts[a.account]
    p = json.load(open(a.payload))
    slug = re.sub(r'[^a-z0-9]+','-', p.get("slug","card").lower()).strip('-') or "card"
    fname = f"{datetime.date.today().isoformat()}-{slug}-{secrets.token_hex(2)}.png"
    outdir = REPO_ROOT/a.account; outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir/fname
    html_path = pathlib.Path("/tmp")/f"card_{a.account}_{slug}.html"
    html_path.write_text(build(acc, p), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width":1080,"height":1350}, device_scale_factor=2)
        pg.goto("file://"+str(html_path)); pg.wait_for_timeout(400)
        pg.screenshot(path=str(outpath), clip={"x":0,"y":0,"width":1080,"height":1350})
        b.close()
    rel = f"{a.account}/{fname}"
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel}"
    print(json.dumps({"path": rel, "abs": str(outpath), "url": url}, ensure_ascii=False))

if __name__ == "__main__":
    main()
