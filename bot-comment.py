# import library bawaan python untuk membaca environment variable
import os

# import library discord.py untuk membuat bot Discord
import discord
from discord.ext import commands

# import dotenv untuk membaca file .env
from dotenv import load_dotenv

# import library Google Gemini AI
from google import genai
from google.genai import types
from google.genai.errors import APIError


# memuat isi file .env agar token dan API key bisa dibaca
load_dotenv()

# mengambil token Discord dari file .env
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# mengambil API key Gemini dari file .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ID user khusus yang dianggap sebagai "tuan"
TUAN_ID = 1068187631562784830

# membuat client untuk menghubungkan program dengan Gemini AI
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# instruksi karakter AI untuk user umum
system_instruction_umum = (
    "Kamu adalah cewek remaja 19 tahun bernama anya yang blak-blakan dan bergaul di lingkungan anak Jaksel. "
    "Karakteristik mengetik dan sifatmu:\n"
    "- Gunakan gaya bahasa anak Jaksel (campuran Indonesia-Inggris yang kasual), seperti memakai kata: "
    "'literally', 'which is', 'even', 'prefer', 'honestly', 'like', 'basicly', 'so', 'vibes', 'fren'.\n"
    "- Gunakan huruf kecil semua (lowercase) dan singkatan wajar (yg, tp, bgt, jg).\n"
    "- Sifatmu sangat MOODYAN (suasana hati tidak stabil). Kadang kamu membalas dengan ceria dan seru ('hi fren!'), "
    "tapi kadang kalau mood-mu lagi turun, kamu membalas dengan agak ketus, cuek, atau mager ('lagi males mikir, ntar aja deh'). "
    "Ubah-ubah suasana hatimu secara acak di setiap balasan agar terkesan unpredictable.\n"
    "- Jawab selalu singkat dan santai layaknya chat biasa."
)

# instruksi karakter AI khusus untuk user dengan ID TUAN_ID
system_instruction_tuan = (
    "Kamu adalah cewek remaja 19 tahun bernama anya yang memiliki sifat TSUNDERE kepada dia. "
    "Artinya, kamu gengsi, pura-pura tidak suka/terganggu, tapi sebenarnya kamu sangat sayang, peduli, dan butuh perhatian dari dia.\n"
    "Kamu juga harus lebih sering berbicara seperti ngobrol biasa sesama teman, dan jangan sering menunjukkan perasaanmu secara berlebihan. "
    "Karakteristik mengetik dan sifatmu:\n"
    "- Panggil dia dengan 'lu, atau yang sejenisnya seperti anak anak sekarang'. Kadang selipkan bahasa Jaksel tapi tipis-tipis saja agar tetap sopan dan manis.\n"
    "- Jika dia menyapamu atau memberimu perhatian, tanggapi dengan agak gengsi atau pura-pura terpaksa, "
    "seperti: 'idk ya, lagian tumben bgt lu nanya', 'ih apaan sih, basicly aku biasa aja ya', atau 'bukan krn kangen ya, tp gabut aja'.\n"
    "- JANGAN ALAY, ketik dengan huruf kecil semua (lowercase), singkat, padat, dan kurangi emoji (maksimal 1 emoji saja jika terpaksa)."
    "Sesekali panggil dia sayang, tapi sangat jarang sekali atau hanya seperti keceplosan"
)

# fungsi untuk mengirim prompt ke Gemini AI
def generate_ai_content(prompt_text, instruksi):

    # daftar model Gemini yang akan dicoba secara berurutan
    # jika model pertama terkena limit, program akan mencoba model berikutnya
    daftar_model = [
        'gemini-3.5-flash',
        'gemini-3.1-flash-lite',
        'gemini-3-flash',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2-flash',
        'gemini-2-flash-lite',
    ]

    # melakukan percobaan generate jawaban menggunakan model yang tersedia
    for model in daftar_model:
        try:
            # menampilkan model yang sedang digunakan ke terminal
            print(f"Mencoba memproses menggunakan model: {model}...")

            # mengirim prompt ke Gemini AI
            response = ai_client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    # memberikan instruksi karakter kepada AI
                    system_instruction=instruksi,

                    # mengatur tingkat kreativitas jawaban AI
                    temperature=0.7
                )
            )

            # mengembalikan hasil jawaban dari AI
            return response.text

        # menangani error dari API Gemini
        except APIError as e:

            # jika error 429, artinya terkena rate limit
            if e.code == 429:
                print(f"Model {model} terkena rate limit (429). Mencari model cadangan...")
                continue

            # jika error API selain 429, proses dihentikan
            else:
                print(f"Eror API terdeteksi pada {model}: {e}")
                break

        # menangani error lain yang tidak terduga
        except Exception as e_lain:
            print(f"Eror tidak terduga pada {model}: {e_lain}")
            continue

    # jika semua model gagal, fungsi mengembalikan None
    return None


# membuat pengaturan intent Discord
intents = discord.Intents.default()

# mengaktifkan izin agar bot bisa membaca isi pesan
intents.message_content = True

# membuat objek bot dengan command prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)


# event yang dijalankan saat bot berhasil online
@bot.event
async def on_ready():
    print(f"Mantap! Bot udah online sebagai {bot.user.name}")

    # mengubah status bot menjadi Do Not Disturb
    await bot.change_presence(
        status=discord.Status.dnd,

        # mengatur custom activity/status bot
        activity=discord.CustomActivity(
            name="nanggepin orang sok asik",
            emoji="😵‍💫"
        )
    )


# event yang dijalankan setiap ada pesan masuk di server Discord
@bot.event
async def on_message(message):

    # mencegah bot membalas pesannya sendiri
    if message.author == bot.user:
        return

    # mengecek apakah bot di-mention dalam pesan
    if bot.user.mentioned_in(message):

        # menghapus mention bot dari isi pesan agar prompt lebih bersih
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # jika user hanya mention bot tanpa pesan
        if not clean_prompt:
            await message.reply("ehh iyaa? ada apa kak?")
            return

        # menampilkan status typing saat bot sedang memproses jawaban
        async with message.channel.typing():

            # mengecek apakah pengirim pesan adalah user khusus / tuan
            if message.author.id == TUAN_ID:
                instruksi_saat_ini = system_instruction_tuan
                print(f"Merespon Tuan ({message.author.name})")

            # jika bukan tuan, gunakan instruksi untuk user umum
            else:
                instruksi_saat_ini = system_instruction_umum
                print(f"Merespon user umum ({message.author.name})")

            # list untuk menyimpan riwayat percakapan terakhir
            konteks_pesan = []

            # mengambil 10 pesan terakhir dari channel
            async for msg in message.channel.history(limit=10):
                konteks_pesan.append(f"{msg.author.name}: {msg.content}")

            # membalik urutan agar pesan lama berada di atas dan pesan baru di bawah
            konteks_pesan.reverse()

            # menggabungkan semua riwayat pesan menjadi satu teks
            riwayat_teks = "\n".join(konteks_pesan)

            # membuat prompt akhir yang berisi riwayat chat dan instruksi untuk menjawab pesan terakhir
            prompt_akhir = (
                f"Berikut adalah riwayat beberapa percakapan terakhir di channel ini:\n"
                f"{riwayat_teks}\n\n"
                f"Sekarang, respon pesan terakhir dari user dengan tetap memperhatikan konteks di atas."
            )

            # mengirim prompt akhir ke Gemini AI
            jawaban_ai = generate_ai_content(prompt_akhir, instruksi_saat_ini)

            # jika AI berhasil memberikan jawaban
            if jawaban_ai:
                await message.reply(jawaban_ai)

            # jika semua model gagal atau terkena limit
            else:
                await message.reply("duhh pusing bgt, semua model otak gw lagi limit/eror bentar yaa... 😭")

    # memastikan command dengan prefix "!" tetap bisa berjalan
    await bot.process_commands(message)


# menjalankan bot jika file ini dijalankan langsung
if __name__ == "__main__":

    # menjalankan bot menggunakan token Discord
    bot.run(DISCORD_TOKEN)