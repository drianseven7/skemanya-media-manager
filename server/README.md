# SKEMANYA Private Server

Fondasi self-hosted SKEMANYA Media Manager: website operasional, API, PostgreSQL, dan HTTPS reverse proxy.

## Struktur
- `public/`: website responsif (desktop dan Android browser).
- `src/`: REST API Node.js + Express.
- `migrations/`: skema PostgreSQL.
- `docker-compose.yml`: API, database, dan Caddy.

## Menjalankan lokal untuk pengujian
1. Install Docker Engine dan Docker Compose.
2. Salin `.env.example` menjadi `.env`, lalu isi nilai rahasia acak. Jangan commit `.env`.
3. Jalankan `docker compose up -d --build`.
4. Buka `http://localhost` (Caddy membutuhkan domain publik untuk sertifikat HTTPS; untuk tes lokal, jalankan API pada port 8080 dan akses `http://localhost:8080`).
5. Buka website dan buat admin pertama menggunakan bootstrap key.

## Deployment VPS
1. Gunakan Ubuntu 24.04 dan pasang Docker Engine + Compose.
2. Salin folder `server` ke VPS.
3. Isi `.env`: domain, email ACME, password database, JWT secret, bootstrap key, dan origin aplikasi.
4. Arahkan DNS A record domain ke IPv4 VPS; buka TCP 80/443 dan SSH seperlunya.
5. Jalankan `docker compose up -d --build`.
6. Buka `https://DOMAIN`; website dan API berada di host yang sama.
7. Buat admin pertama. Setelah itu endpoint setup otomatis tertutup karena pengguna pertama sudah ada.

## Gratis / biaya
Kode dan stack ini menggunakan komponen open-source. Itu tidak berarti VPS publik gratis tersedia permanen. Belum ada VPS yang dibuat atau biaya yang diaktifkan. Gunakan hanya compute gratis yang memenuhi syarat; jangan menyetujui upgrade atau memasukkan metode pembayaran tanpa persetujuan pemilik.

## Fitur website tahap awal
- Login admin dan setup admin pertama.
- Ringkasan operasional.
- Bank berita, ruang draft konten, tugas, kalender editorial, dan log aktivitas.
- PostgreSQL persisten.
- Website dan API satu origin; tidak memerlukan layanan AI eksternal.

## Keamanan dan batasan
- Password disimpan sebagai hash bcrypt; sesi JWT berlaku 12 jam dan disimpan di sessionStorage browser.
- Database tidak dipublikasikan ke internet; hanya API yang dapat diakses dari reverse proxy.
- Setup awal memerlukan bootstrap key dan hanya berfungsi saat belum ada pengguna.
- Ini fondasi tahap awal, bukan produksi final. Sebelum dipakai publik perlu penguatan rate limit login, rotasi secret, backup otomatis dan uji pemulihan, audit akses, validasi input lanjutan, serta pengujian TLS.
- Belum ada upload file, reset password, multi-role granular, atau APK.
