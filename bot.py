import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TUAN_ID = zzzzzzzzzzzzzzzzzzz

ai_client = genai.Client(api_key=GEMINI_API_KEY)

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

def generate_ai_content(prompt_text, instruksi):
    daftar_model = [
        'gemini-3.5-flash',
        'gemini-3.1-flash-lite',
        'gemini-3-flash',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2-flash',
        'gemini-2-flash-lite',
    ]
    
    for model in daftar_model:
        try:
            print(f"Mencoba memproses menggunakan model: {model}...")
            response = ai_client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=instruksi,
                    temperature=0.7
                )
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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Mantap! Bot udah online sebagai {bot.user.name}")
    
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.CustomActivity(
            name="nanggepin orang sok asik", 
            emoji="😵‍💫"
        )
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
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
                        konteks_pesan.append(f"{msg.author.name}: {msg.content}")
                    
                    konteks_pesan.reverse()
                    riwayat_teks = "\n".join(konteks_pesan)
                    prompt_akhir = (
                        f"Berikut adalah riwayat beberapa percakapan terakhir di channel ini:\n"
                        f"{riwayat_teks}\n\n"
                        f"Sekarang, respon pesan terakhir dari user dengan tetap memperhatikan konteks di atas."
                    )

                    jawaban_ai = generate_ai_content(prompt_akhir, instruksi_saat_ini)
                    
                    if jawaban_ai:
                        await message.reply(jawaban_ai)
                    else:
                        await message.reply("duhh pusing bgt, semua model otak gw lagi limit/eror bentar yaa... 😭")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)