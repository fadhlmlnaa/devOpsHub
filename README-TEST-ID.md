# Panduan Testing Mandiri Platform DevOps (DevOpsHub)

Dokumen ini berisi panduan langkah demi langkah untuk menguji backend dan aplikasi mobile secara mandiri.

---

## Ringkasan Perintah Cepat

### 1. Menjalankan Semua Test Backend (34 Tests)
```bash
docker compose exec backend pytest -v
```

### 2. Menjalankan Analisis & Test Mobile (15 Tests)
```bash
cd mobile
flutter analyze
flutter test
```

---

## 📱 Panduan Pengujian Manual Mobile (Step 05)

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

### Skenario Uji 13: Auto-Refresh Token & Sesi Aman
1. Sesi pengguna (Access Token & Refresh Token) tersimpan di storage terenkripsi perangkat (`flutter_secure_storage`).
2. Jika Access Token kadaluarsa (401), `ApiClient` secara transparan memicu endpoint `/auth/refresh` di background, memperbarui token di storage, dan mengulang request data tanpa mengganggu interaksi pengguna.
3. Jika Refresh Token juga kadaluarsa atau di-revoke, sesi dibersihkan dan pengguna diarahkan kembali ke layar Login.

---

### Skenario Uji 14: Logout
1. Klik tombol **Logout** di AppBar.
2. Dialog konfirmasi muncul.
3. Klik **"Logout"**.
4. Sesi lokal dibersihkan, Refresh Token di-revoke di backend, dan aplikasi kembali ke layar Login.

---

## 🧪 Struktur Unit & Widget Test Otomatis (Mobile)

File test terletak di folder `mobile/test/`:
- `models_test.dart`: Pengujian serialisasi & parsing JSON untuk `UserModel`, `AuthTokenModel`, `WorkspaceModel`, `WorkspaceMemberModel`, `EnvironmentModel`, `ServerModel`, `ConnectionTestModel`, `ServerMetricsModel`, `ServiceModel`, `ServiceListModel`, `ServiceActionResultModel`, `LogEntryModel`, dan `LogResponseModel` (Step 09).
- `api_exception_test.dart`: Pengujian parsing error backend, handling status code HTTP (400, 401, 403, 404, 409, 422, 500) dan timeout connection.
- `widgets_test.dart`: Pengujian rendering dan event listener pada Base Widgets (`AppButton`, `AppTextField`, `AppStatusBadge`, `AppCard`).
- `widget_test.dart`: Pengujian inisialisasi aplikasi `DevOpsHubApp` dan halaman startup.

Jalankan seluruh test:
```bash
cd mobile && flutter test
```

