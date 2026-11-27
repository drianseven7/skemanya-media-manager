# SKEMANYA Private Server

Fondasi backend self-hosted untuk SKEMANYA Media Manager. API, PostgreSQL, dan reverse proxy HTTPS dikelola di VPS melalui Docker Compose. Tidak ada AI provider atau layanan berbayar yang menjadi dependensi backend ini.

## Isi
- Node.js API: autentikasi admin, dashboard, berita, konten, tugas, pengguna, aktivitas, pengaturan.
- PostgreSQL: database utama dan volume persisten.
- Caddy: reverse proxy dan TLS otomatis setelah DNS diarahkan ke VPS.
- Docker Compose: pengelolaan layanan.

## Catatan sebelum deployment
VPS belum dibuat dan domain belum diarahkan. Jangan mengisi data rahasia di Git. VPS gratis permanen tidak dijamin tersedia; verifikasi syarat provider, metode pembayaran, region, kapasitas, dan kebijakan idle sebelum membuat instance. Jangan mengaktifkan upgrade berbayar.

## Menyiapkan VPS (Ubuntu 24.04)
1. Pasang Docker Engine dan plugin Docker Compose dari dokumentasi resmi Docker.
2. Salin folder `server` ke VPS.
3. Buat `.env` dari `.env.example`; isi domain, email ACME, password database, JWT secret, bootstrap key, dan origin aplikasi.
4. Arahkan DNS record A domain API ke IPv4 VPS. Buka TCP 80/443 dan SSH seperlunya.
5. Jalankan `docker compose up -d --build`.
6. Uji `https://DOMAIN/api/health`.
7. Buat admin pertama dengan POST `/api/setup`, header `x-bootstrap-key`, body JSON `{"name":"Admin","email":"alamat-email","password":"password-minimal-12-karakter"}`. Endpoint setup otomatis tertutup setelah pengguna pertama dibuat.
8. Simpan token login dengan aman. Ganti/rotasi bootstrap key setelah setup, lalu batasi endpoint setup melalui konfigurasi pada rilis hardening berikutnya.

## Endpoint awal
- `GET /api/health` — status API dan database.
- `POST /api/setup` — membuat admin pertama (hanya saat tabel users kosong).
- `POST /api/auth/login` — login.
- `GET /api/me` — profil pengguna.
- `GET /api/dashboard` — ringkasan.
- `GET|POST|PATCH /api/news` — data berita.
- `GET|POST|PATCH /api/content` — data konten.
- `GET|POST|PATCH /api/tasks` — tugas.
- `GET /api/users` — admin saja.
- `GET /api/activity` — log aktivitas.
- `GET|PUT /api/settings/:key` — pengaturan admin.

## Batasan tahap ini
Ini adalah fondasi backend, bukan sistem produksi final. Belum ada unggah file, reset password, manajemen role granular, backup terjadwal, push notification, atau integrasi Android. Sebelum dipakai publik, perlu audit keamanan, backup restore test, TLS/DNS test, dan pembatasan percobaan login.
