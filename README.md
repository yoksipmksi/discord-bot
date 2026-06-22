

# teman ngobrol discord kamu

bot discord sederhana berbasis python yang menggunakan gemini ai untuk membalas pesan ketika bot di-mention. bot ini memiliki dua gaya balasan, yaitu gaya umum untuk user biasa dan gaya khusus untuk user tertentu berdasarkan discord user id.

## fitur

* bot hanya membalas ketika di-mention/reply
* menggunakan gemini ai sebagai otak balasan
* mendukung fallback beberapa model gemini jika model utama terkena limit
* memiliki persona berbeda untuk user umum dan user khusus
* mengambil riwayat chat terakhir sebagai konteks percakapan
* menggunakan file `.env` agar token tidak ditulis langsung di kode
* status bot bisa diatur

## persyaratan

sebelum menjalankan bot, pastikan sudah menyiapkan:

* python
* akun discord
* discord developer portal
* google ai studio / gemini api key
* koneksi internet
* text editor seperti visual studio code

## 1. download atau siapkan project

buat folder project terlebih dahulu, misalnya:

```bash
discord-bot
```

masuk ke folder tersebut:

```bash
cd discord-bot
```

lalu simpan file python bot, misalnya dengan nama:

```text
bot.py
```

## 2. buat virtual environment

disarankan memakai virtual environment agar library project tidak bercampur dengan python utama.

### windows

```bash
python -m venv venv
```

aktifkan virtual environment:

```bash
venv\Scripts\activate
```

### linux / macos

```bash
python3 -m venv venv
```

aktifkan virtual environment:

```bash
source venv/bin/activate
```

jika berhasil, biasanya terminal akan menampilkan tanda seperti ini:

```text
(venv)
```

## 3. install library yang dibutuhkan

install semua library berikut:

```bash
pip install -r requirements.txt
```
pastikan virtual environment sudah aktif sebelum menjalankan perintah instalasi.
library yang digunakan:

```text
discord.py      = untuk membuat bot discord
python-dotenv   = untuk membaca file .env
google-genai    = untuk menghubungkan python dengan gemini ai
```

## 4. membuat discord bot token

ikuti langkah berikut:

1. buka discord developer portal
2. login menggunakan akun discord
3. klik `new application`
4. beri nama aplikasi, misalnya `discord-bot`
5. masuk ke menu `bot`
6. klik `add bot`
7. pada bagian token, klik `reset token` atau `copy token`
8. simpan token tersebut untuk dimasukkan ke file `.env`

jangan pernah membagikan token bot ke orang lain, karena token bisa digunakan untuk mengontrol bot kamu.

## 5. aktifkan message content intent

agar bot bisa membaca isi pesan, aktifkan intent berikut:

1. buka aplikasi bot di discord developer portal
2. masuk ke menu `bot`
3. cari bagian `privileged gateway intents`
4. aktifkan `message content intent`
5. klik save jika ada tombol penyimpanan

bagian ini penting karena kode menggunakan:

```python
intents.message_content = True
```

tanpa mengaktifkan intent ini di developer portal, bot bisa online tetapi tidak bisa membaca isi pesan dengan benar.

## 6. invite bot ke server discord

masuk ke menu `oauth2` lalu pilih `url generator`.

centang bagian:

```text
bot
applications.commands
```

pada bagian bot permissions, pilih permission dasar seperti:

```text
send messages
read message history
view channels
use slash commands
```

jika ingin bot bisa membalas pesan dengan lancar, pastikan permission berikut aktif:

```text
view channels
send messages
read message history
```

setelah itu copy url yang muncul, buka di browser, lalu pilih server tempat bot akan dimasukkan.

## 7. membuat gemini api key

ikuti langkah berikut:

1. buka google ai studio
2. login menggunakan akun google
3. masuk ke bagian api key
4. buat api key baru
5. copy api key tersebut
6. simpan api key ke file `.env`

jangan menyebarkan gemini api key ke publik, github, grup, atau discord.

## 8. membuat file .env

buat file baru di folder project dengan nama:

```text
.env
```

isi file `.env` seperti ini:

```env
DISCORD_TOKEN=masukkan_token_discord_di_sini
GEMINI_API_KEY=masukkan_api_key_gemini_di_sini
```

contoh:

```env
DISCORD_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=yyyyyyyyyyyyyyyyyyyyyyyy
```

pastikan tidak ada spasi berlebihan sebelum atau sesudah tanda `=`.

## 9. struktur folder project

struktur folder yang disarankan:

```text
│ discord-bot/
  ├── bot.py
  ├── .env
  └── README.md
```

jika memakai virtual environment, biasanya akan menjadi seperti ini:

```text
│ discord-bot/
  ├── main.py
  ├── .env
  ├── README.md
  └── venv/
```

## 10. menjalankan bot

jalankan bot dengan perintah:

```bash
python bot.py
```

atau jika memakai linux / macos:

```bash
python3 main.py
```

jika berhasil, terminal akan menampilkan pesan seperti:

```text
Mantap! Bot udah online sebagai nama_bot
```

setelah itu bot sudah online di discord.

## 11. cara menggunakan bot

bot akan merespons jika di-mention di channel discord.

contoh:

```text
@nama-bot halo
```

atau:

```text
@nama-bot hari ini mood kamu gimana?
```

jika bot hanya di-mention tanpa pesan, bot akan menjawab:

```text
ehh iyaa? ada apa kak?
```

## 12. cara kerja bot secara singkat

alur kerja bot:

1. user mengirim pesan dan mention bot
2. bot mengecek apakah pesan berasal dari dirinya sendiri atau bukan
3. jika bot di-mention, bot membersihkan mention dari isi pesan
4. bot mengecek apakah pengirim adalah user khusus berdasarkan `TUAN_ID`
5. jika user adalah `TUAN_ID`, bot memakai persona khusus
6. jika user biasa, bot memakai persona umum
7. bot mengambil 10 pesan terakhir sebagai konteks
8. konteks dan pesan dikirim ke gemini ai
9. gemini ai mengirim jawaban
10. bot membalas pesan user di discord

## 13. mengatur user khusus / tuan

di kode terdapat bagian:

```python
TUAN_ID = zzzzzzzzzzzzzzzzzzz
```

angka tersebut adalah discord user id untuk user khusus.

jika ingin mengganti user khusus, ganti angka tersebut dengan discord user id milikmu.

cara mengambil discord user id:

1. buka discord
2. masuk ke user settings
3. pilih advanced
4. aktifkan developer mode
5. klik kanan pada profil user
6. pilih copy user id

lalu tempel ke kode:

```python
TUAN_ID = id_user_baru
```

contoh:

```python
TUAN_ID = zzzzzzzzzzzzzzzzzzz
```

## 14. mengatur jumlah riwayat chat

di kode terdapat bagian:

```python
async for msg in message.channel.history(limit=10):
```

angka `10` berarti bot mengambil 10 pesan terakhir sebagai konteks.

jika ingin lebih hemat token, ubah menjadi:

```python
async for msg in message.channel.history(limit=5):
```

semakin besar limit, semakin banyak konteks yang dikirim ke ai. namun prompt juga menjadi lebih panjang dan bisa lebih boros token.

rekomendasi:

```text
limit=5  cocok untuk bot hemat token
limit=10 cocok untuk bot percakapan biasa
limit=20 cocok jika butuh konteks lebih panjang
```

## 15. mengatur model gemini

di kode terdapat daftar model:

```python
daftar_model = [
    'gemini-3.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-3-flash',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2-flash',
    'gemini-2-flash-lite',
]
```

bot akan mencoba model dari atas ke bawah.

jika model pertama terkena limit, bot akan mencoba model berikutnya.

agar lebih ringan, daftar model bisa dibuat lebih pendek:

```python
daftar_model = [
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
]
```

semakin banyak model fallback, semakin besar kemungkinan bot tetap menjawab ketika satu model limit. tetapi jika banyak model gagal, satu pesan user bisa memicu beberapa percobaan request.

## 16. mengatur gaya balasan bot

gaya balasan user umum diatur pada bagian:

```python
system_instruction_umum = (...)
```

gaya balasan user khusus diatur pada bagian:

```python
system_instruction_tuan = (...)
```

jika ingin mengubah karakter bot, ubah teks instruksi tersebut.

contoh instruksi sederhana:

```python
system_instruction_umum = (
    "kamu adalah bot discord yang ramah, santai, dan menjawab dengan singkat."
)
```

## 17. troubleshooting

### bot tidak online

cek bagian berikut:

* token discord sudah benar
* file `.env` berada satu folder dengan `main.py`
* nama variabel di `.env` benar
* koneksi internet aktif
* library sudah terinstall

pastikan isi `.env` seperti ini:

```env
DISCORD_TOKEN=token_discord
GEMINI_API_KEY=api_key_gemini
```

### bot online tapi tidak merespons pesan

cek bagian berikut:

* bot sudah di-mention
* message content intent sudah aktif di discord developer portal
* kode sudah memakai:

```python
intents.message_content = True
```

* bot punya permission untuk membaca dan mengirim pesan di channel

### muncul error 429

error `429` biasanya berarti model terkena rate limit.

solusi:

* tunggu beberapa saat
* kurangi jumlah request
* kecilkan `history(limit=10)` menjadi `history(limit=5)`
* gunakan model lite
* jangan terlalu sering spam mention bot
* cek limit di google ai studio

### muncul error token none

jika token terbaca `None`, kemungkinan file `.env` salah.

cek kembali nama variabel:

```env
DISCORD_TOKEN=...
GEMINI_API_KEY=...
```

jangan menulis seperti ini:

```env
DISCORD TOKEN=...
GEMINI API KEY=...
```

karena nama variabel tidak boleh memakai spasi.

### bot tidak bisa membaca pesan

pastikan sudah mengaktifkan `message content intent` di discord developer portal.

di kode python:

```python
intents = discord.Intents.default()
intents.message_content = True
```

di developer portal juga harus aktif.

## 18. keamanan

hal yang tidak boleh dilakukan:

* jangan share discord token
* jangan share gemini api key
* jangan kirim token ke chat publik
* jangan screenshot token
* jangan menaruh token langsung di source code


## 19. contoh file bot.py

pastikan file utama bernama:

```text
bot.py
```

lalu jalankan dengan:

```bash
python bot.py
python3 bot.py
```

bot ini adalah bot discord berbasis python yang memanfaatkan gemini ai untuk membalas pesan secara otomatis ketika di-mention. bot menggunakan `.env` untuk menyimpan token dengan lebih aman, memiliki persona berbeda untuk user umum dan user khusus, serta memakai sistem fallback model agar tetap bisa menjawab ketika salah satu model terkena limit.

```
if [[ -d .git ]] && [[ "0" == "1" ]]; then git pull; fi; if [[ ! -z "" ]]; then pip install -U --prefix .local ; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; /usr/local/bin/python /home/container/bot.py
```
```
/usr/local/bin/python /home/container/bot.py
```