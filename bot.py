import os
import re
import asyncio
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TUAN_ID = 1234567891011121314
ai_client = genai.Client(api_key=GEMINI_API_KEY)

system_instruction_umum = (
    "masukkan instruksi.\n"
)

system_instruction_tuan = (
    "masukkan instruksi.\n"
)

# Mengirim prompt ke Gemini dan mencoba model cadangan jika model sebelumnya terkena limit.
def generate_ai_content(prompt_text, instruksi):
    daftar_model = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2-flash", "gemini-2-flash-lite"]
    for model in daftar_model:
        try:
            print(f"Mencoba memproses menggunakan model: {model}...")
            response = ai_client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(system_instruction=instruksi, temperature=0.7)
            )
            return response.text
        except APIError as e:
            if e.code == 429:
                print(f"Model {model} terkena rate limit (429). Mencari model cadangan...")
                continue
            else:
                print(f"Eror API terdeteksi pada {model}: {e}")
                break
        except Exception as e_lain:
            print(f"Eror tidak terduga pada {model}: {e_lain}")
            continue
    return None

# Menghasilkan teks waktu saat ini dalam format Indonesia/WIB untuk dimasukkan ke prompt AI.
def waktu_sekarang_text():
    sekarang = datetime.now(ZoneInfo("Asia/Jakarta"))
    nama_hari = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
    hari_inggris = sekarang.strftime("%A")
    hari = nama_hari.get(hari_inggris, hari_inggris)
    return sekarang.strftime(f"{hari}, %d-%m-%Y jam %H:%M WIB")

# Memotong teks biasa secara natural berdasarkan kalimat/kata agar chat tidak terlalu panjang.
def potong_pesan_natural(text, max_len=450, max_parts=4):
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    kalimat = re.split(r'(?<=[.!?…])\s+', text)
    bagian = []
    sekarang = ""
    for k in kalimat:
        if len(sekarang) + len(k) + 1 <= max_len:
            sekarang += (" " + k if sekarang else k)
        else:
            if sekarang:
                bagian.append(sekarang.strip())
            if len(k) > max_len:
                kata_kata = k.split()
                temp = ""
                for kata in kata_kata:
                    if len(temp) + len(kata) + 1 <= max_len:
                        temp += (" " + kata if temp else kata)
                    else:
                        bagian.append(temp.strip())
                        temp = kata
                sekarang = temp
            else:
                sekarang = k
    if sekarang:
        bagian.append(sekarang.strip())
    if len(bagian) > max_parts:
        bagian_awal = bagian[:max_parts - 1]
        sisa = " ".join(bagian[max_parts - 1:])
        if len(sisa) > 1900:
            sisa = sisa[:1900] + "..."
        bagian = bagian_awal + [sisa]
    return bagian

# Memotong teks yang berisi code block agar format markdown dan indentasi kode tidak rusak.
def potong_blok_kode(text, max_len=1900):
    if len(text) <= max_len:
        return [text]
    bagian = []
    baris = text.split("\n")
    sekarang = ""
    dalam_blok_kode = False
    bahasa_kode = ""
    for b in baris:
        stripped = b.strip()
        is_fence = stripped.startswith("```")
        is_opening_fence = is_fence and not dalam_blok_kode
        is_closing_fence = is_fence and dalam_blok_kode
        tambahan = b if not sekarang else "\n" + b
        if len(sekarang) + len(tambahan) > max_len:
            if dalam_blok_kode:
                sekarang += "\n```"
            bagian.append(sekarang)
            if dalam_blok_kode and not is_closing_fence:
                pembuka = f"```{bahasa_kode}\n" if bahasa_kode else "```\n"
                sekarang = pembuka + b
            else:
                sekarang = b
        else:
            sekarang += tambahan
        if is_opening_fence:
            bahasa_kode = stripped[3:].strip()
            dalam_blok_kode = True
        elif is_closing_fence:
            dalam_blok_kode = False
    if sekarang:
        bagian.append(sekarang)
    return bagian

# Mengirim jawaban AI ke Discord dengan pemotongan berbeda untuk teks biasa dan kode.
async def kirim_natural(message, text):
    text = text.strip()
    if not text:
        await message.reply("duhh jawabannya kosong kak 😭")
        return
    if "```" in text:
        bagian_pesan = potong_blok_kode(text, max_len=1900)
    else:
        bagian_pesan = potong_pesan_natural(text, max_len=150, max_parts=4)
    for i, bagian in enumerate(bagian_pesan):
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(0.2, 0.5))
        if i == 0:
            await message.reply(bagian)
        else:
            await message.channel.send(bagian)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Event yang berjalan saat bot berhasil online dan mengatur status Discord bot.
@bot.event
async def on_ready():
    print(f"Mantap! Bot udah online sebagai {bot.user.name}")
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.CustomActivity(name="nanggepin orang sok asik", emoji="😵‍💫")
    )

# Event utama untuk membaca mention, mengambil konteks chat, memilih persona, lalu membalas dengan AI.
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
        if not clean_prompt:
            await message.reply("ehh iyaa? ada apa kak?")
            return
        async with message.channel.typing():
            if message.author.id == TUAN_ID:
                instruksi_saat_ini = system_instruction_tuan
                print(f"Merespon Tuan ({message.author.name})")
            else:
                instruksi_saat_ini = system_instruction_umum
                print(f"Merespon user umum ({message.author.name})")
            konteks_pesan = []
            async for msg in message.channel.history(limit=10):
                konten = msg.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
                if konten:
                    konteks_pesan.append(f"{msg.author.display_name}: {konten}")
            konteks_pesan.reverse()
            nama_user = message.author.display_name
            riwayat_teks = "\n".join(konteks_pesan)
            waktu_saat_ini = waktu_sekarang_text()
            prompt_akhir = (
                f"Waktu saat ini: {waktu_saat_ini}\n\n"
                f"User yang sedang berbicara: {nama_user}\n"
                f"Pesan terakhir user: {clean_prompt}\n\n"
                f"Berikut adalah riwayat beberapa percakapan terakhir di channel ini:\n"
                f"{riwayat_teks}\n\n"
                f"Sekarang, respon pesan terakhir dari user dengan tetap memperhatikan konteks di atas."
            )
            jawaban_ai = await asyncio.to_thread(generate_ai_content, prompt_akhir, instruksi_saat_ini)
        if jawaban_ai:
            await kirim_natural(message, jawaban_ai)
        else:
            await message.reply("duhh pusing bgt, semua model otak gw lagi limit/eror bentar yaa... 😭")
    await bot.process_commands(message)

# Menjalankan bot menggunakan token Discord dari file .env.
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)