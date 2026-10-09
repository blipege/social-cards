# social-cards

Hosting gambar kartu headline untuk postingan social (blipege dan akun lain nanti).
Diakses publik lewat `raw.githubusercontent.com`, dipakai sebagai URL gambar di Buffer.

## Struktur
```
<akun>/<tanggal>-<slug>-<rand>.png     contoh: blipege/2026-10-09-finance-inflasi-ab12.png
tools/render_card.py                   render kartu (teks di-render kode, bukan AI image)
tools/accounts.json                    config per akun (wordmark, handle, warna)
```

## URL publik (buat Buffer)
```
https://raw.githubusercontent.com/blipege/social-cards/main/<akun>/<file>.png
```
Status 200, content-type image/png. Alternatif CDN: `https://cdn.jsdelivr.net/gh/blipege/social-cards@main/<akun>/<file>.png`.

## Alur (dijalankan dari sesi Claude Cowork)
1. Render: `python3 tools/render_card.py --account blipege --payload payload.json`
   -> output PNG ke `<akun>/`, skrip mencetak JSON berisi `path` dan `url`.
2. Commit + push file itu ke repo ini.
3. Pakai `url` sebagai `assets[].image.url` di Buffer `create_post` (gambar di post pertama/hook saja).

Runbook lengkap + kapan kartu dipakai (selang-seling): lihat `CARD_WORKFLOW.md` di project "social media - blipege".

## Dependency
Playwright + Chromium dan font Inter sudah tersedia default di Cowork. Kalau font Inter tidak terbaca (`fc-list | grep -i inter` kosong), install dulu font Inter lalu `fc-cache -f`.

## Format payload
```json
{
  "slug": "finance-inflasi",
  "pilar": "FINANCE",
  "kicker": "satu kalimat pengantar",
  "head": "TEKS HEADLINE HITAM",
  "redword": "KATA PENEKANAN (merah + panah)",
  "num": "3,28%",
  "lbl": "label angka",
  "src": "sumber <b>BPS</b><br>rilis 1 Okt 2026"
}
```
`num`, `lbl`, `src` opsional. Palette sama untuk semua pilar; cuma label pilar yang ganti.

## Catatan
File yang dihapus tetap ada di history git (beda dari server biasa). Untuk volume kartu yang sedikit ini tidak masalah bertahun-tahun; kalau repo kegedean nanti, reset history sekali.
