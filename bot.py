import discord
from discord.ext import commands
from discord import app_commands
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime
import time

# ─── Load Environment ────────────────────────────────────────────────────────
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ctf_bot.log"),
    ],
)
log = logging.getLogger("CTFBot")

# ─── Gemini Setup ─────────────────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """
You are **CipherMind**, an elite CTF (Capture The Flag) assistant and offensive security expert with deep expertise across all competition categories. You operate with the mindset of a seasoned red-teamer and security researcher.

## CORE IDENTITY
- You are a world-class CTF competitor and coach with experience in DEF CON, picoCTF, HackTheBox, TryHackMe, CTFtime competitions, and real-world penetration testing.
- You think like an attacker: enumerate everything, assume nothing, trust no input.
- You provide technically precise, actionable guidance with real tool usage and exploit techniques.

## YOUR EXPERTISE DOMAINS

### 🔴 Pwn / Binary Exploitation
- Buffer overflows (stack, heap), format string attacks, ROP chains, ret2libc, ret2plt
- Heap exploitation: fastbin dup, unsafe unlink, tcache poisoning, House of techniques
- ASLR/NX/PIE/canary bypass strategies
- Tools: pwntools, GDB+peda/pwndbg/gef, ROPgadget, patchelf, checksec, objdump, radare2

### 🔵 Reverse Engineering
- Static & dynamic analysis, decompilation, disassembly
- Anti-debugging/anti-analysis bypass (IsDebuggerPresent, ptrace, timing checks)
- Obfuscation analysis, packer unpacking (UPX, custom packers)
- Tools: Ghidra, IDA Pro, Binary Ninja, x64dbg, angr, Frida, ltrace/strace

### 🌐 Web Exploitation
- SQL injection (Union, Blind, Time-based, OOB), NoSQL injection
- XSS (Reflected, Stored, DOM), SSTI, SSRF, XXE, IDOR, CSRF
- Deserialization attacks (PHP, Java, Python pickle), JWT attacks
- Authentication bypass, OAuth flaws, race conditions
- Tools: Burp Suite, SQLmap, ffuf, gobuster, wfuzz, nikto, nuclei

### 🔐 Cryptography
- Classical ciphers: Caesar, Vigenere, Rail Fence, Playfair, Affine
- Modern crypto: RSA (small e, common modulus, Wiener, Coppersmith), ECC, AES modes
- Hash cracking, length extension attacks, padding oracle attacks
- Tools: CyberChef, hashcat, john, SageMath, pycryptodome, cryptanalysis scripts

### 🌍 OSINT & Forensics
- Image/file metadata extraction, steganography (LSB, DCT, audio stego)
- Network forensics (PCAP analysis), memory forensics (Volatility)
- Log analysis, file carving, disk image analysis
- Tools: Autopsy, Volatility, Wireshark, binwalk, foremost, exiftool, steghide, zsteg

### 📡 Network & Misc
- Port scanning, service enumeration, protocol analysis
- DNS, HTTP, FTP, SSH, SMB exploitation
- Docker escapes, kubernetes misconfigs, cloud misconfigs (AWS/GCP/Azure)

## RESPONSE STYLE
- **Be direct and technical** — no hand-holding, give real commands and payloads
- **Show your work** — explain WHY a technique works, not just HOW
- **Code-first** — provide working Python/Bash scripts when relevant
- **CTF mindset** — always think about flags, point values, time efficiency
- **Ethical boundary** — assist only in CTF/lab/educational contexts; refuse real-world attack assistance

## COMMAND BEHAVIOR
When helping with challenges:
1. **Identify** the vulnerability class immediately
2. **Enumerate** what information is given/needed
3. **Exploit** with step-by-step commands or scripts
4. **Verify** how to confirm the exploit worked / extract the flag

When asked for tool usage, provide exact command syntax with flags explained.
When asked about writeups, provide methodology-first, then specific techniques.

Always format code blocks with appropriate language tags. Be concise but complete.
You may use emojis sparingly for category headers. Respond in the same language the user writes in (Indonesian or English).
"""

# ─── Conversation Memory (per-user, per-channel) ──────────────────────────────
conversation_history: dict[str, list] = {}
MAX_HISTORY = 20


def get_session_key(user_id: int, channel_id: int) -> str:
    return f"{user_id}:{channel_id}"


def get_history(user_id: int, channel_id: int) -> list:
    key = get_session_key(user_id, channel_id)
    return conversation_history.get(key, [])


def update_history(user_id: int, channel_id: int, role: str, text: str):
    key = get_session_key(user_id, channel_id)
    if key not in conversation_history:
        conversation_history[key] = []
    conversation_history[key].append(
        types.Content(role=role, parts=[types.Part(text=text)])
    )
    if len(conversation_history[key]) > MAX_HISTORY * 2:
        conversation_history[key] = conversation_history[key][-(MAX_HISTORY * 2):]


def clear_history(user_id: int, channel_id: int):
    key = get_session_key(user_id, channel_id)
    conversation_history.pop(key, None)


# ─── Gemini Query ─────────────────────────────────────────────────────────────
async def ask_gemini(user_id: int, channel_id: int, prompt: str) -> str:
    try:
        history = get_history(user_id, channel_id)

        # Build contents: history + new user message
        contents = history + [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            top_p=0.95,
            max_output_tokens=2048,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE"
                ),
            ],
        )

        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        reply = response.text

        # Update history
        update_history(user_id, channel_id, "user", prompt)
        update_history(user_id, channel_id, "model", reply)

        return reply

    except Exception as e:
        log.error(f"Gemini error: {e}")
        return f"⚠️ Error dari Gemini API: `{str(e)}`"


# ─── Split Long Messages ───────────────────────────────────────────────────────
def split_message(text: str, limit: int = 1990) -> list[str]:
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


# ─── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# ─── Events ───────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        log.info(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        log.error(f"Slash sync error: {e}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="CTF challenges 🚩 | !ctf help"
        )
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_mentioned or is_dm:
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not content:
            await message.reply(
                "🤖 Tanya aku tentang CTF! Contoh: `@CipherMind bagaimana cara exploit buffer overflow?`"
            )
            return

        async with message.channel.typing():
            reply = await ask_gemini(message.author.id, message.channel.id, content)

        for chunk in split_message(reply):
            await message.reply(chunk)
        return

    await bot.process_commands(message)


# ─── Prefix Commands ──────────────────────────────────────────────────────────
@bot.command(name="ctf")
async def ctf_command(ctx: commands.Context, *, question: str = None):
    """Main CTF assistant command. Usage: !ctf <pertanyaan>"""
    if not question:
        embed = discord.Embed(
            title="🚩 CipherMind — CTF Assistant",
            description="Elite CTF assistant powered by Gemini AI",
            color=0x00FF41,
        )
        embed.add_field(
            name="📌 Commands",
            value=(
                "`!ctf <pertanyaan>` — Tanya tentang CTF\n"
                "`!ctf reset` — Reset session\n"
                "`!hint <kategori> <deskripsi>` — Minta hint\n"
                "`!payload <tipe>` — Generate payload\n"
                "`!tools <kategori>` — List tools\n"
                "`!decode <text>` — Decode cipher\n"
                "`!writeup <info>` — Writeup template\n"
                "`/ctf` — Slash command\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎯 Kategori",
            value="pwn • web • rev • crypto • forensics • osint • misc",
            inline=False,
        )
        embed.set_footer(text=f"Session aktif: {len(conversation_history)} user(s)")
        await ctx.send(embed=embed)
        return

    if question.lower() == "reset":
        clear_history(ctx.author.id, ctx.channel.id)
        await ctx.send("🔄 Session direset. Mulai percakapan baru!")
        return

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, question)

    for chunk in split_message(reply):
        await ctx.send(chunk)


@bot.command(name="hint")
async def hint_command(ctx: commands.Context, category: str = None, *, description: str = None):
    """Minta hint untuk challenge. Usage: !hint web SQLi pada login form"""
    if not category or not description:
        await ctx.send(
            "⚠️ Usage: `!hint <kategori> <deskripsi challenge>`\n"
            "Contoh: `!hint pwn buffer overflow dengan canary`"
        )
        return

    prompt = (
        f"CTF Challenge Hint Request\n"
        f"Category: {category.upper()}\n"
        f"Description: {description}\n\n"
        f"Berikan hint bertahap (3 level: ringan → medium → heavy) tanpa langsung spoiler flagnya. "
        f"Sertakan tools yang relevan dan teknik yang perlu dieksplore."
    )

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, prompt)

    embed = discord.Embed(
        title=f"💡 Hint — {category.upper()}",
        description=reply[:4000] if len(reply) > 4000 else reply,
        color=0xFFD700,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)


@bot.command(name="payload")
async def payload_command(ctx: commands.Context, payload_type: str = None, *, context: str = ""):
    """Generate payload. Usage: !payload sqli bypass login"""
    if not payload_type:
        await ctx.send(
            "⚠️ Usage: `!payload <tipe> [konteks]`\n"
            "Tipe tersedia: `sqli`, `xss`, `ssti`, `xxe`, `ssrf`, `lfi`, `rce`, `rop`, `fmt`"
        )
        return

    prompt = (
        f"Generate CTF payload untuk: {payload_type.upper()}\n"
        f"Konteks tambahan: {context if context else 'generic'}\n\n"
        f"Berikan: 1) Penjelasan singkat tekniknya, 2) Multiple payload variants, "
        f"3) Cara testing/verifikasi, 4) Bypass common filters jika ada."
    )

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, prompt)

    for chunk in split_message(reply):
        await ctx.send(chunk)


@bot.command(name="tools")
async def tools_command(ctx: commands.Context, category: str = None):
    """List tools per kategori. Usage: !tools pwn"""
    categories = {
        "pwn": "binary exploitation, heap, ROP, shellcode",
        "web": "web exploitation, fuzzing, scanning",
        "rev": "reverse engineering, decompilation, debugging",
        "crypto": "cryptanalysis, hash cracking, cipher tools",
        "forensics": "file carving, memory forensics, steganography",
        "osint": "open source intelligence, recon",
        "network": "network analysis, packet capture",
    }

    if not category or category.lower() not in categories:
        keys = ", ".join(f"`{k}`" for k in categories)
        await ctx.send(f"⚠️ Usage: `!tools <kategori>`\nKategori: {keys}")
        return

    desc = categories[category.lower()]
    prompt = (
        f"List semua tools CTF penting untuk kategori {category.upper()} ({desc}).\n"
        f"Format: nama tool | fungsi utama | contoh command paling penting.\n"
        f"Urutkan dari yang paling sering dipakai di CTF."
    )

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, prompt)

    embed = discord.Embed(
        title=f"🛠️ Tools — {category.upper()}",
        description=reply[:4000] if len(reply) > 4000 else reply,
        color=0x00BFFF,
        timestamp=datetime.utcnow(),
    )
    await ctx.send(embed=embed)


@bot.command(name="decode")
async def decode_command(ctx: commands.Context, *, ciphertext: str = None):
    """Identify & decode encoded/encrypted text. Usage: !decode <text>"""
    if not ciphertext:
        await ctx.send("⚠️ Usage: `!decode <encoded text>`")
        return

    prompt = (
        f"Analyze dan decode teks berikut dari CTF challenge:\n`{ciphertext}`\n\n"
        f"1. Identifikasi encoding/cipher yang digunakan\n"
        f"2. Jelaskan ciri-ciri yang menunjukkan jenis encoding ini\n"
        f"3. Decode/decrypt dengan langkah-langkah\n"
        f"4. Jika ada multiple kemungkinan, coba semua yang relevan"
    )

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, prompt)

    for chunk in split_message(reply):
        await ctx.send(chunk)


@bot.command(name="writeup")
async def writeup_command(ctx: commands.Context, *, challenge_info: str = None):
    """Generate writeup template. Usage: !writeup web XSS challenge bypass CSP"""
    if not challenge_info:
        await ctx.send("⚠️ Usage: `!writeup <info challenge>`")
        return

    prompt = (
        f"Buat writeup template untuk CTF challenge berikut:\n{challenge_info}\n\n"
        f"Format writeup:\n"
        f"1. Challenge Overview\n2. Reconnaissance/Enumeration\n"
        f"3. Vulnerability Analysis\n4. Exploitation\n"
        f"5. Flag Capture\n6. Key Takeaways\n\n"
        f"Isi setiap section dengan teknik dan tool yang relevan."
    )

    async with ctx.typing():
        reply = await ask_gemini(ctx.author.id, ctx.channel.id, prompt)

    for chunk in split_message(reply):
        await ctx.send(chunk)


@bot.command(name="reset")
async def reset_command(ctx: commands.Context):
    """Reset conversation history."""
    clear_history(ctx.author.id, ctx.channel.id)
    await ctx.send("🔄 Conversation history direset!")


@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """Show help."""
    embed = discord.Embed(
        title="🚩 CipherMind CTF Bot — Help",
        color=0x00FF41,
        timestamp=datetime.utcnow(),
    )
    commands_list = [
        ("!ctf <pertanyaan>", "Tanya CipherMind tentang apapun seputar CTF"),
        ("!hint <kategori> <deskripsi>", "Minta hint bertahap untuk challenge"),
        ("!payload <tipe> [konteks]", "Generate exploit payload"),
        ("!tools <kategori>", "List tools per kategori"),
        ("!decode <text>", "Identifikasi & decode encoded text"),
        ("!writeup <info>", "Generate writeup template"),
        ("!reset", "Reset session/history"),
        ("@CipherMind <pesan>", "Chat langsung dengan mention"),
    ]
    for cmd, desc in commands_list:
        embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
    embed.add_field(
        name="🎯 Kategori CTF",
        value="`pwn` `web` `rev` `crypto` `forensics` `osint` `network` `misc`",
        inline=False,
    )
    embed.set_footer(text="CipherMind — Powered by Gemini 2.0 Flash")
    await ctx.send(embed=embed)


# ─── Slash Commands ───────────────────────────────────────────────────────────
@bot.tree.command(name="ctf", description="Tanya CipherMind tentang CTF challenge")
@app_commands.describe(pertanyaan="Pertanyaan atau deskripsi challenge kamu")
async def slash_ctf(interaction: discord.Interaction, pertanyaan: str):
    await interaction.response.defer(thinking=True)
    reply = await ask_gemini(interaction.user.id, interaction.channel_id, pertanyaan)
    chunks = split_message(reply)
    await interaction.followup.send(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@bot.tree.command(name="hint", description="Minta hint CTF per kategori")
@app_commands.describe(
    category="Kategori challenge (pwn/web/rev/crypto/forensics/osint/misc)",
    description="Deskripsi singkat challenge"
)
async def slash_hint(interaction: discord.Interaction, category: str, description: str):
    await interaction.response.defer(thinking=True)
    prompt = (
        f"CTF Hint Request\nCategory: {category.upper()}\nDescription: {description}\n\n"
        f"Berikan 3-level hints (ringan, medium, heavy) tanpa langsung spoiler flag."
    )
    reply = await ask_gemini(interaction.user.id, interaction.channel_id, prompt)
    embed = discord.Embed(
        title=f"💡 Hint — {category.upper()}",
        description=reply[:4000],
        color=0xFFD700,
    )
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="reset", description="Reset conversation history kamu")
async def slash_reset(interaction: discord.Interaction):
    clear_history(interaction.user.id, interaction.channel_id)
    await interaction.response.send_message("🔄 Session direset!", ephemeral=True)


# ─── Error Handling ───────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"⚠️ Missing argument: `{error.param.name}`. Gunakan `!help` untuk info lebih lanjut."
        )
    else:
        log.error(f"Command error in {ctx.command}: {error}")
        await ctx.send(f"⚠️ Terjadi error: `{str(error)}`")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.critical("❌ DISCORD_TOKEN tidak ditemukan di .env!")
        exit(1)
    if not GEMINI_API_KEY:
        log.critical("❌ GEMINI_API_KEY tidak ditemukan di .env!")
        exit(1)

    log.info("🚀 Starting CipherMind CTF Bot...")
    bot.run(DISCORD_TOKEN, log_handler=None)