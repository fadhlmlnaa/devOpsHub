# Panduan Testing Mandiri Platform DevOps (DevOpsHub)

Dokumen ini berisi panduan langkah demi langkah untuk menguji backend dan aplikasi mobile secara mandiri.

---

## Ringkasan Perintah Cepat

### 1. Menjalankan Semua Test Backend (72 Tests)
```bash
docker compose exec backend pytest -v
```

### 2. Menjalankan Analisis & Test Mobile (33 Tests)
```bash
cd mobile
flutter analyze
flutter test
```

---

## 📱 Panduan Pengujian Manual Mobile (Step 05 - Step 10)

### Persiapan Menjalankan Aplikasi Mobile

1. Pastikan backend aktif:
   ```bash
   docker compose up -d
   ```
2. Jalankan aplikasi mobile pada emulator Android / simulator iOS / macOS / Chrome:
   ```bash
   cd mobile
   flutter run
   ```

*(Catatan: Konfigurasi default di `AppConstants` otomatis menggunakan `http://10.0.2.2:8000/api/v1` untuk Android Emulator, dan `http://localhost:8000/api/v1` untuk iOS Simulator / macOS / Web).*

---

### Skenario Uji 1: Splash Screen & Startup Session Check
1. Buka aplikasi untuk pertama kali (keadaan belum login).
2. Tampilan Splash Screen muncul sesaat dengan logo bernuansa **Deep Dark Teal & Electric Cyan** serta font **Plus Jakarta Sans**.
3. Aplikasi otomatis mendeteksi tidak ada token dan mengarahkan ke halaman **Login** (`/auth/login`).

---

### Skenario Uji 2: Pendaftaran Akun Baru (Register)
1. Pada layar Login, klik **"Daftar Sekarang"**.
2. Anda akan diarahkan ke layar **Register** (`/auth/register`).
3. Masukkan:
   - Nama: `Fadhil Maulana`
   - Email: `fadhil.tester@devopshub.io`
   - Password: `PasswordSuperAman123!`
4. Klik tombol **"Daftar Sekarang"**.
5. Muncul notifikasi pendaftaran berhasil dan otomatis kembali ke halaman login.

---

### Skenario Uji 3: Login Pengguna & Validasi Error
1. Coba masukkan password yang salah terlebih dahulu.
   - Hasil: Tampil alert error *"Invalid email or password"*. Tombol login kembali ke state normal tanpa crash.
2. Masukkan email & password yang benar:
   - Email: `fadhil.tester@devopshub.io`
   - Password: `PasswordSuperAman123!`
3. Klik tombol **"Masuk ke Akun"**.
4. Tombol berubah menjadi loading state *(Memproses...)* lalu otomatis diarahkan ke **Workspace List** (`/workspaces`).

---

### Skenario Uji 4: Workspace List & Empty State
1. Jika pengguna baru belum memiliki workspace, layar akan menampilkan ilustrasi empty state yang rapi dengan tombol **"Buat Workspace"**.

---

### Skenario Uji 5: Membuat Workspace Baru (Modal Bottom Sheet)
1. Klik tombol **"Workspace Baru"** (FAB) atau tombol di empty state.
2. Modal Bottom Sheet (`CreateWorkspaceSheet`) akan muncul dari bawah.
3. Isi form:
   - Nama Workspace: `PT Bintang Solusi Cloud`
   - Deskripsi: `Infrastruktur DevOps dan Staging Server`
   - Timezone: `Asia/Jakarta`
4. Klik **"Buat Workspace"**.
5. Workspace berhasil dibuat di backend, pengguna otomatis mendapatkan role **`OWNER`**, dan daftar workspace diperbarui secara otomatis.

---

### Skenario Uji 6: Memilih Workspace & Masuk ke Workspace Home
1. Klik pada card workspace `PT Bintang Solusi Cloud`.
2. Anda akan masuk ke halaman **Workspace Home** (`/workspaces/:id`).
3. Header menampilkan:
   - Nama Workspace
   - Deskripsi & Timezone
   - Badge Role **`OWNER`** (berwarna cyan cerah)
4. Section Environment dan Server Management aktif di Workspace Home.

---

### Skenario Uji 7: Mengelola Environment (Step 06)
1. Di Workspace Home, pada tab **Environments**, klik **+ Tambah Environment**.
2. Masukkan data:
   - Nama: `Production`
   - Key: `production` (otomatis disesuaikan lowercase & sanitized)
   - Deskripsi: `Main production cluster`
3. Klik **Simpan Environment**.
4. Environment baru muncul pada daftar dengan badge server count awal `0`.

---

### Skenario Uji 8: Mendaftarkan Server Baru & Enkripsi Kredensial (Step 06)
1. Pindah ke tab **Servers** atau klik tombol **+ Tambah Server**.
2. Lengkapi form pendaftaran server:
   - Nama Server: `Prod Web App 01`
   - Environment: Pilih `Production` dari dropdown
   - Hostname: `app.prod.internal`
   - IP Address: `103.120.45.67`
   - Port SSH: `22`
   - Username SSH: `ubuntu`
   - Tipe Autentikasi: `Password` atau `Private Key`
   - Masukkan Password atau Paste OpenSSH Private Key (dan passphrase opsional).
3. Klik **Simpan Server**.
4. Backend mengenkripsi kredensial ke tabel `server_credentials` dengan Fernet AES-128-CBC + HMAC-SHA256. Password/private key tidak pernah dikembalikan ke client.
5. Server muncul di list dengan status awal `UNKNOWN` atau `OFFLINE` jika belum diuji.

---

### Skenario Uji 9: Test SSH Connection & Remote System Info (Step 06)
1. Klik pada card server `Prod Web App 01` untuk membuka **Server Detail**.
2. Klik tombol **⚡ Test Connection**.
3. Tombol berubah menjadi loading state *(Menguji Koneksi SSH...)*.
4. Backend menjalankan SSH Provider (`asyncssh`) dengan command ringan (`uname -s`, `hostname`, `uname -r`, `uname -m`, `uptime`).
5. Jika server aktif dan kredensial cocok:
   - Status berubah menjadi 🟢 `ONLINE`.
   - Menampilkan kartu detail Remote System Info: Hostname, Operating System, Kernel, Architecture, dan Uptime.
6. Jika server tidak dapat dijangkau atau auth gagal:
   - Status berubah menjadi 🔴 `OFFLINE`.
   - Menampilkan pesan error yang aman tanpa mengekspos exception traceback atau rahasia server.

---

### Skenario Uji 10: Real-time Server Monitoring & Telemetry Dashboard (Step 07)
1. Buka detail server yang berstatus `ONLINE` atau sudah dikonfigurasi kredensial SSH yang valid.
2. Halaman **Server Detail** akan otomatis memuat metrik telemetri langsung (*Real-time Metrics*).
3. Verifikasi widget metrik menampilkan data akurat:
   - **CPU**: Persentase penggunaan CPU (0-100%), visual progress bar dinamis, dan jumlah CPU cores.
   - **Memory (RAM)**: Persentase penggunaan RAM, visual bar, detail terpakai vs total dalam format gigabytes (contoh `4.2 GB / 16.0 GB`).
   - **Disk Storage**: Persentase kapasitas root mount point `/`, terpakai vs total dalam GB/TB.
   - **Load Average**: Nilai load average untuk interval 1 menit, 5 menit, dan 15 menit.
   - **System Specifications**: Hostname, OS distribution, Linux kernel, CPU architecture, dan Uptime.
   - **Network Interfaces**: Daftar antarmuka jaringan terdeteksi beserta IP private (jika ada).
4. Tarik layar ke bawah (**Pull to Refresh**) atau klik tombol **🔄 Refresh** di kanan atas kartu metrik:
   - Data telemetri terbaru akan diperbarui langsung via 1 sesi eksekusi SSH terisolasi.
5. Uji skenario **Server Offline**:
   - Jika server target tidak dapat dijangkau dalam waktu 5 detik (timeout) atau kredensial salah, status server menjadi `OFFLINE` atau `UNKNOWN`.
   - UI menampilkan status offline yang jelas, waktu terakhir berhasil diperiksa, dan tombol **Coba Lagi (Retry)**.

---

### Skenario Uji 11: Manajemen Service Linux Systemd (Step 08)
1. Buka detail server di halaman **Server Detail**.
2. Scroll ke bagian kartu **Layanan & Services (Systemd)** lalu klik tombol **"Buka Manajemen Services"**.
3. Halaman daftar service (`ServiceListView`) akan terbuka dan memuat daftar unit service systemd:
   - Gunakan search bar untuk mencari service spesifik (contoh: `nginx`, `docker`, `postgresql`, `odoo`).
   - Gunakan filter chips (**Semua**, **Active (Running)**, **Inactive (Stopped)**, **Failed**) untuk memfilter daftar service.
4. Klik salah satu card service (contoh: `nginx.service`) untuk membuka **Service Detail**:
   - Menampilkan status badge (`RUNNING`, `STOPPED`, `FAILED`, `UNKNOWN`), startup boot enabled, main PID, sub-state, load-state, dan waktu aktif.
5. Uji tombol aksi (**Start**, **Stop**, **Restart**, **Reload**):
   - Klik tombol **Restart**: Dialog konfirmasi muncul dengan peringatan server target.
   - Klik **RESTART**: Tombol berubah menjadi loading state, backend mengeksekusi `sudo -n systemctl restart nginx.service`.
   - Setelah selesai, backend mengembalikan status sebelum & sesudah aksi, memunculkan notifikasi berhasil (snackbar), dan status service otomatis ter-refresh secara real-time.
6. Uji otorisasi dan proteksi:
   - Pengguna dengan role `VIEWER` atau `DEVELOPER` dapat melihat daftar & detail service, namun tombol aksi Start/Stop/Restart/Reload dinonaktifkan dengan penanda gembok oranye.
   - Hanya role `OWNER` dan `ADMIN` yang diizinkan menjalankan operasi mutasi.

---

### Skenario Uji 12: Inspeksi Log Service Systemd (Step 09)
1. Buka detail service tertentu (contoh: `nginx.service`) di **Service Detail**.
2. Klik tombol **"Lihat Log Service (Journald)"** di bagian bawah kartu aksi.
3. Halaman viewer log (`ServiceLogView`) akan terbuka dan memuat log stream dari `journalctl` secara instan:
   - Gunakan filter baris (**50**, **100**, **200**, **500**, **1000**) untuk membatasi jumlah baris log yang ditarik.
   - Gunakan filter waktu (**Semua**, **5m**, **10m**, **30m**, **1h**, **6h**, **24h**) untuk membatasi rentang waktu log.
   - Gunakan search bar untuk mencari kata kunci tertentu di dalam log yang sudah dimuat.
4. Periksa visualisasi baris log:
   - Priority badge terformat dengan warna tematik (`EMERGENCY/ALERT/CRITICAL/ERROR` = Merah, `WARNING` = Oranye, `INFO/NOTICE` = Biru/Cyan, `DEBUG` = Abu-abu).
   - Waktu log (timestamp) diformat rapi sesuai zona waktu lokal.
   - Pesan log ditampilkan dengan font monospace presisi.
5. Uji fitur proteksi rahasia (*Secret Redaction*):
   - Kunci API, token OAuth, header `Authorization: Bearer`, password, dan private key yang mungkin tercetak pada stdout/stderr service otomatis disensor (`********`) oleh backend sebelum dikirimkan ke perangkat mobile.
6. Uji fitur salin log (*Copy to Clipboard*):
   - Klik tombol **Copy** pada kartu baris log untuk menyalin satu baris pesan ke clipboard.
   - Klik ikon **Copy All** di pojok kanan atas AppBar untuk menyalin seluruh entri log yang sedang ditampilkan (dengan dialog konfirmasi jika ukuran log > 100 baris).
7. Uji otorisasi:
   - Semua role (`VIEWER`, `DEVELOPER`, `ADMIN`, `OWNER`) dapat membaca log service workspace miliknya. User di luar workspace akan ditolak dengan `403/404`.

---

---

### Skenario Uji 13: Manajemen Docker & Containers (Step 10)
1. Buka halaman **Server Detail** pada server yang memiliki daemon Docker.
2. Periksa kartu **Docker Container Platform**:
   - Jika daemon Docker aktif, kartu menampilkan status **RUNNING** dengan versi daemon (misal: `Docker 28.0.1`) dan tombol **"Buka Docker Dashboard"**.
   - Jika Docker tidak terinstal, kartu menampilkan **NOT_INSTALLED** atau **STOPPED** dengan informasi yang aman.
3. Klik **"Buka Docker Dashboard"**:
   - Dashboard menampilkan status daemon, total containers, dan tab segmentasi: **Containers** dan **Compose Projects**.
4. Di tab **Containers**:
   - Filter container berdasarkan state (**Running**, **Stopped**, **Semua**).
   - Klik kartu container (misal: `web-nginx` atau `postgres_db`) untuk masuk ke **Container Detail View**.
5. Di halaman **Container Detail**:
   - Periksa spesifikasi: ID, Nama, Image, Status, Ports mapping, Restart Policy, serta resource CPU/RAM usage.
   - Uji mutasi siklus hidup: **Start**, **Stop**, **Restart**.
   - Setiap mutasi memunculkan modal dialog konfirmasi bahaya dengan `confirm: true`.
   - Role `VIEWER` dan `DEVELOPER` hanya melihat (tombol mutasi nonaktif/hidden). Role `ADMIN` dan `OWNER` dapat mengeksekusi aksi.
6. Klik **"Lihat Log Container (stdout/stderr)"**:
   - Halaman terminal log container terbuka dengan log stream real-time.
   - Terapkan filter baris log (50, 100, 200, 500, 1000) dan rentang waktu.
   - Periksa bahwa secret redaction aktif menyensor kata sandi/token pada output log.

---

### Skenario Uji 14: Manajemen Docker Compose Projects (Step 10)
1. Di **Docker Dashboard**, pilih tab **Compose Projects**.
2. Klik tombol **"+ Registrasikan Compose Project"**:
   - Masukkan Nama Tampilan: `PTBI Production`
   - Masukkan Nama Project: `ptbi`
   - Masukkan Direktori Kerja Absolut: `/opt/apps/ptbi`
   - Masukkan Nama File Compose: `docker-compose.yml`
   - Klik **"Simpan Project"**.
3. Periksa kartu **Compose Project**:
   - Menampilkan status project (**RUNNING**, **STOPPED**, **PARTIAL**, **FAILED**), direktori kerja, dan daftar sub-service (misal: `web`, `db`, `redis`).
4. Uji operasi Compose:
   - Klik **Up** untuk menjalankan `docker compose up -d`.
   - Klik **Restart** untuk memulai ulang stack `docker compose restart`.
   - Klik **Down** untuk menghentikan stack `docker compose down`.
   - Semua operasi memerlukan konfirmasi eksplisit sebelum dijalankan.
5. Role `VIEWER` dan `DEVELOPER` hanya dapat memantau status Compose project.

---

### Skenario Uji 15: Deployment Management (Step 11)
1. Buka halaman **Server Detail** pada server terdaftar.
2. Periksa kartu **Application Deployments** yang menampilkan jumlah konfigurasi terdaftar dan tombol **"Buka Deployment Dashboard"**.
3. Klik **"Buka Deployment Dashboard"**:
   - Terdapat 2 tab: **Riwayat Deploy** dan **Konfigurasi App**.
4. Di tab **Konfigurasi App**:
   - Klik **"+ Daftarkan Konfigurasi"** untuk membuat config deployment baru.
   - Isi Formulir:
     - Nama Konfigurasi: `Staging Odoo`
     - Nama Aplikasi: `PTBI Odoo 17`
     - Direktori Kerja: `/opt/odoo`
     - Tipe Deployment: `Systemd Linux` atau `Docker Compose`
     - Git Branch: `staging`
     - Nama Unit Service: `odoo.service`
   - Klik **"Simpan Konfigurasi"**.
5. Uji Trigger Deployment:
   - Klik tombol **"Deploy"** pada kartu konfigurasi.
   - Modal sheet **Konfirmasi Deployment** muncul:
     - Menampilkan ringkasan Aplikasi, Environment, Server, dan Tipe Deployment.
     - Jika Environment bertipe **PROTECTED (Production)**, muncul banner peringatan merah tebal.
   - Klik **"Eksekusi Deployment Sekarang"**.
6. Pemantauan Log & Riwayat Deployment:
   - Aplikasi otomatis berpindah ke tab **Riwayat Deploy**.
   - Kartu deployment baru berstatus **RUNNING** dengan animasi indikator progress.
   - Klik kartu untuk membuka **Terminal Log Deployment**.
   - Log ditampilkan secara real-time dengan monospace font dan color-coded log level (INFO, WARNING, ERROR).
   - Seluruh token/password otomatis di-masking (redacted).
   - Setelah workflow selesai, status otomatis berubah menjadi **SUCCESS** atau **FAILED**.
7. Uji Concurrency Lock (409 Conflict):
   - Jika deployment sedang berstatus `RUNNING`, trigger deployment kedua pada konfigurasi yang sama akan ditolak dengan error 409: `"Deployment sedang berjalan."`.
8. Role RBAC:
   - Role `VIEWER` dan `DEVELOPER` hanya dapat melihat daftar konfigurasi, riwayat, dan detail log.
   - Role `ADMIN` dan `OWNER` memiliki akses penuh CRUD konfigurasi dan trigger deployment.

---

### Skenario Uji 16: Backup Management & Verifikasi Integritas Checksum (Step 12)
1. Buka halaman **Detail Server** dari Workspace Home.
2. Scroll ke bagian bawah dan klik kartu **"Buka Dashboard Backup"** pada seksi *Backup Management & Cadangan Data*.
3. Tampilan **Backup Dashboard** terbuka dengan 2 tab:
   - **Riwayat Backup**
   - **Konfigurasi Target**
4. Uji Registrasi Target Backup Baru:
   - Beralih ke tab **Konfigurasi Target**, klik tombol **"Tambah Konfigurasi"** (atau Floating Action Button).
   - Masukkan informasi konfigurasi:
     - Tipe Target: `PostgreSQL`, `Filesystem`, atau `Docker Volume`
     - Nama Konfigurasi: `Production DB Backup`
     - Sumber Target: `my_production_db` (untuk DB) / `/opt/myapp/uploads` (untuk Filesystem) / `myapp_data` (untuk Docker Volume)
     - Direktori Tujuan di Server: `/var/backups/postgresql`
     - Retensi: `14` Hari
     - Toggle Kompresi: `Aktif`
   - Klik **"Daftarkan Konfigurasi"**.
5. Uji Trigger Backup:
   - Klik tombol **"Jalankan Backup"** pada kartu target backup.
   - Modal sheet **Konfirmasi Backup** muncul:
     - Menampilkan ringkasan Tipe, Sumber, Direktori Tujuan, dan Retensi.
     - Jika Environment bertipe **PROTECTED (Production)**, muncul banner peringatan merah tebal.
   - Klik **"Eksekusi Backup Sekarang"**.
6. Pemantauan Riwayat & Log Backup:
   - Aplikasi otomatis berpindah ke tab **Riwayat Backup**.
   - Kartu backup baru berstatus **RUNNING** dengan indikator progress.
   - Klik kartu untuk membuka **Detail Backup**.
   - Klik **"Lihat Log Backup"** untuk membuka **Terminal Log Backup**.
   - Log ditampilkan secara real-time dengan monospace font dan color-coded log level (INFO, WARNING, ERROR).
   - Seluruh token/password otomatis di-masking (redacted) menggunakan `SecretRedactor`.
   - Setelah operasi selesai, status berubah menjadi **SUCCESS** atau **FAILED**, dengan metadata nama file, ukuran berkas, dan cuplikan hash SHA-256.
7. Uji Verifikasi Berkas Backup:
   - Pada halaman **Detail Backup**, klik tombol **"Verifikasi Berkas Backup"**.
   - Backend memvalidasi keberadaan fisik berkas di server, mengkalkulasi ulang hash SHA-256 langsung di server, dan membandingkannya dengan hash yang tersimpan di database.
   - Kotak status verifikasi hijau muncul jika checksum cocok ("Verifikasi berhasil. Checksum SHA-256 cocok.").
8. Uji Concurrency Lock (409 Conflict):
   - Jika backup sedang berstatus `RUNNING`, trigger backup kedua pada konfigurasi yang sama akan ditolak dengan error 409: `"Backup sedang berjalan."`.
9. Role RBAC:
   - Role `VIEWER` dan `DEVELOPER` hanya dapat melihat daftar konfigurasi, riwayat, dan detail log.
   - Role `ADMIN` dan `OWNER` memiliki akses penuh CRUD konfigurasi, trigger backup, dan verifikasi checksum.

---

### Skenario Uji 17: Alerts & Notifications (Step 13)
1. Buka halaman **Workspace Home** atau **Server Detail**.
2. Periksa ikon lonceng notifikasi 🔔 di AppBar:
   - Jika terdapat notifikasi yang belum dibaca, badge merah menampilkan jumlah unread count (misal: `3` atau `99+`).
3. Klik ikon lonceng 🔔 untuk membuka **Inbox Notifikasi**:
   - Menampilkan daftar notifikasi in-app lengkap dengan tingkat keparahan (*CRITICAL*, *WARNING*, *INFO*), judul, pesan, dan waktu relatif.
   - Klik chip **"Hanya Belum Dibaca"** untuk memfilter notifikasi unread.
   - Klik kartu notifikasi: status berubah menjadi terbaca (*read*) dan counter badge di AppBar berkurang secara real-time.
   - Klik ikon **"Tandai Semua Dibaca"** di AppBar untuk menandai seluruh notifikasi sekaligus.
   - Klik ikon gerigi (Preferensi) untuk membuka modal bottom sheet **Preferensi Notifikasi** (`In-App Notification`, `Email Notification`, dan `Minimum Severity`).
4. Buka **Alerts Dashboard** (melalui ikon lonceng aktif di Workspace Home atau tombol *"Buka Dashboard Alerts Server"* di Server Detail):
   - Terdapat 2 tab: **Alert** dan **Aturan Rules**.
5. Di tab **Aturan Rules**:
   - Klik tombol **"Tambah Aturan"** (Floating Action Button).
   - Isi formulir aturan:
     - Nama Aturan: `High CPU Prod Alert`
     - Tipe Metrik: `CPU_USAGE` (atau `MEMORY_USAGE`, `DISK_USAGE`, `SERVER_STATUS`, `SERVICE_STATUS`, `DEPLOYMENT_STATUS`, `BACKUP_STATUS`)
     - Operator: `GREATER_THAN` (`>`)
     - Batas (Threshold): `90.0`
     - Durasi Bertahan: `300` detik
     - Severity: `CRITICAL`
     - Toggle Aktifkan: `Aktif`
   - Klik **"Buat Aturan Alert"**. Aturan baru langsung muncul di daftar rules.
   - Uji toggle switch untuk mengaktifkan/menonaktifkan aturan secara instan.
6. Di tab **Alert**:
   - Terapkan filter chips: **Semua Status**, **🔥 Firing**, **✅ Resolved**, serta filter severity (**Critical**, **Warning**, **Info**).
   - Klik tombol **Sync / Evaluasi Alert Sekarang** di pojok kanan atas AppBar untuk memicu siklus evaluasi manual ke backend.
7. Buka **Detail Alert**:
   - Menampilkan status alert (*FIRING* merah / *RESOLVED* hijau), tingkat keparahan, nama server, environment, nilai metrik terdeteksi vs nilai batas, dan waktu terpicu.
   - Periksa **Audit Trail Riwayat Event**: Menampilkan urutan timeline event (*TRIGGERED*, *NOTIFICATION_SENT*, *RESOLVED*).
   - Jika alert berstatus *FIRING*, role `ADMIN` atau `OWNER` dapat mengklik tombol **"Selesaikan Alert Secara Manual"**. Muncul dialog konfirmasi bahaya, dan setelah dikonfirmasi, alert berubah menjadi *RESOLVED* dan event audit manual tercatat.
8. Role RBAC:
   - Role `VIEWER` dan `DEVELOPER` hanya dapat melihat daftar alert, rules, dan preferensi notifikasi miliknya sendiri.
   - Role `ADMIN` dan `OWNER` memiliki akses penuh membuat, mengedit, menghapus rules, dan menyelesaikan alert manual.

---

### Skenario Uji 18: Auto-Refresh Token & Sesi Aman
1. Sesi pengguna (Access Token & Refresh Token) tersimpan di storage terenkripsi perangkat (`flutter_secure_storage`).
2. Jika Access Token kadaluarsa (401), `ApiClient` secara transparan memicu endpoint `/auth/refresh` di background, memperbarui token di storage, dan mengulang request data tanpa mengganggu interaksi pengguna.
3. Jika Refresh Token juga kadaluarsa atau di-revoke, sesi dibersihkan dan pengguna diarahkan kembali ke layar Login.

---

### Skenario Uji 20: Audit Logging & Security Hardening (Step 14)
1. **Pencatatan Audit Otomatis (Append-Only)**:
   - Lakukan berbagai aksi di aplikasi: Login, buat/edit server, restart service systemd, trigger container action, jalankan deployment, atau trigger backup.
   - Buka **Workspace Home** -> Klik menu **"Audit Logs"** (ikon history/security).
   - Pastikan setiap aksi yang baru saja dijalankan muncul di daftar audit logs dengan status badge (*SUCCESS* hijau / *FAILED* merah), nama aksi (misal `SERVICE_ACTION`, `DEPLOYMENT_TRIGGER`, `LOGIN`), nama actor/user, IP address, dan timestamp relatif.
2. **Filter & Pencarian Audit Log**:
   - Filter berdasarkan tipe resource (`server`, `service`, `deployment`, `backup`, `alert`).
   - Filter berdasarkan action (`LOGIN`, `SERVICE_ACTION`, `TRIGGER_DEPLOYMENT`, dll.).
   - Klik salah satu item audit log untuk membuka dialog **Detail Metadata Audit**:
     - Pastikan informasi sensitif seperti token, SSH key, atau password telah di-mask menjadi `[REDACTED]`.
3. **Uji RBAC Audit Log**:
   - Login sebagai user dengan role `VIEWER` atau `DEVELOPER`: Menu Audit Log tidak muncul di Workspace Home dan akses langsung ke endpoint audit log mengembalikan HTTP 403 Forbidden.
   - Login sebagai `ADMIN` atau `OWNER`: Menu Audit Log tampil dan dapat diakses dengan lancar.
4. **Uji Token Rotation & Reuse Detection**:
   - Lakukan refresh token. Token lama otomatis di-revoke dan token baru diberikan.
   - Jika refresh token lama dicoba dipakai ulang secara sengaja (serangan replay), backend langsung membatalkan seluruh token family pengguna tersebut.
5. **Uji Rate Limiting**:
   - Lakukan request login salah sebanyak 6 kali berturut-turut dalam 1 menit:
   - Backend merespons dengan HTTP `429 Too Many Requests` disertai header `Retry-After`.

---

## 🧪 Struktur Unit & Widget Test Otomatis (Mobile & Backend)

### Skenario Uji 21: DevOps Standalone Agent (Step 15)
1. **Pengecekan Status Connection Mode di Server Detail**:
   - Buka **Server Detail** salah satu server.
   - Pada header card, perhatikan badge mode koneksi (`SSH` atau `AGENT`).
   - Server existing secara default berstatus `SSH` dan tetap berfungsi normal tanpa perubahan konfigurasi.
2. **Generate Enrollment Token (One-Time Token)**:
   - Pada section **DevOps Agent (Execution Plane)**, klik tombol **"Generate Agent Enrollment Token"**.
   - Muncul dialog modal menampilkan perintah setup command lengkap dengan token hash one-time (berlaku 15 menit).
   - Klik tombol **"Salin"** untuk menyalin perintah setup ke clipboard.
   - Token ini disimpan dalam bentuk hash SHA-256 di database (bukan plaintext) dan hanya dapat digunakan 1 kali (*single-use*).
3. **Pendaftaran Agent (Outbound Enrollment Handshake)**:
   - Jalankan installer agent pada target server / environment pengujian:
     ```bash
     python3 -m agent.main enroll --server http://127.0.0.1:8000 --token <ENROLLMENT_TOKEN>
     ```
   - Agent akan mengirim handshake ke `/api/v1/agent/enroll`, memvalidasi token, dan menerima kredensial permanen terisolasi (`agent_token`).
   - Mode server otomatis beralih menjadi `AGENT`.
4. **Heartbeat & Capabilities Verification**:
   - Agent menjalankan koneksi WebSocket / HTTP Heartbeat secara berkala ke backend.
   - Pada aplikasi mobile Server Detail, status agent akan berubah menjadi **`ONLINE`** (badge hijau), menampilkan versi agent (`1.0.0`), waktu heartbeat terakhir, serta checklist capability (`✓ systemd`, `✓ Docker`, `✓ Monitoring`, `✓ PostgreSQL`, `✓ Filesystem Backup`).
5. **Eksekusi Operasi Predefined via Agent**:
   - Lakukan refresh metrik, restart service systemd, atau cek container Docker pada server ber-tipe `AGENT`.
   - Backend memvalidasi otorisasi & audit log, lalu mengirim job terstruktur ke Agent via WebSocket (`dispatcher_instance`).
   - Agent memvalidasi nonce (replay protection), expiration, dan menjalankan fungsi terisolasi sesuai allowlist (tanpa arbitrary shell string).
6. **Nonaktifkan & Cabut Kredensial (Disable & Revoke)**:
   - Klik **"Nonaktifkan"** pada card Agent: Agent berubah status menjadi `DISABLED` dan menolak job baru.
   - Klik **"Revoke (SSH)"**: Kredensial agent dihapus permanen dan mode server di-reset kembali ke `SSH`.

---

## 🧪 Struktur Unit & Widget Test Otomatis (Mobile & Backend)

### Mobile Test
File test terletak di folder `mobile/test/`:
- `models_test.dart`: Pengujian serialisasi & parsing JSON untuk seluruh model backend termasuk `AgentModel`, `AgentEnrollmentResponseModel`, `AgentJobModel` (Step 15), `AuditLogModel`, `AlertRuleModel`, `AlertModel`, `NotificationModel`.
- `api_exception_test.dart`: Pengujian parsing error backend, handling status code HTTP (400, 401, 403, 404, 409, 422, 429, 500) dan timeout connection.
- `widgets_test.dart`: Pengujian rendering dan event listener pada Base Widgets (`AppButton`, `AppTextField`, `AppStatusBadge`, `AppCard`).
- `widget_test.dart`: Pengujian inisialisasi aplikasi `DevOpsHubApp` dan halaman startup.

Jalankan seluruh test:
```bash
cd mobile && flutter test
```

### Backend Test
File test terletak di folder `backend/tests/`:
- `test_agent.py`: Pengujian komprehensif lifecycle DevOps Agent: pembuatan enrollment token, verifikasi token kedaluwarsa / digunakan ulang, handshake pendaftaran agent, autentikasi heartbeat, WebSocket dispatcher job protocol, proteksi replay nonce, proteksi injeksi service name, serta isolasi Provider Factory tanpa silent fallback.
- `test_security_audit.py`: Validasi audit logging append-only, immutability, RBAC access control, IDOR workspace isolation, token rotation, token reuse revocation, sliding window rate limiting (429), security headers, dan input validation anti-traversal.

Jalankan backend test:
```bash
docker compose exec backend pytest -v
```




