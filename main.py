import discord
from discord.ext import commands
from gtts import gTTS
import os
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
import asyncio
import yt_dlp
from flask import Flask
from threading import Thread

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 전역 상태 저장용 변수들
music_queue = {}
tts_channel_id = None
volume = 0.5

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

# 음악 재생 명령어
@bot.command(name="들어")
async def play(ctx, *, url):
    voice_channel = ctx.author.voice.channel
    if ctx.guild.id not in music_queue:
        music_queue[ctx.guild.id] = []
    music_queue[ctx.guild.id].append(url)

    if ctx.voice_client is None:
        vc = await voice_channel.connect()
        await play_music(ctx, vc)
    elif not ctx.voice_client.is_playing():
        await play_music(ctx, ctx.voice_client)

async def play_music(ctx, vc):
    if not music_queue[ctx.guild.id]:
        await vc.disconnect()
        return

    url = music_queue[ctx.guild.id].pop(0)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'auto'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info['url']

    ffmpeg_options = {
        'options': f'-vn -filter:a "volume={volume}"'
    }

    vc.play(discord.FFmpegPCMAudio(stream_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_music(ctx, vc), bot.loop))

# 일시정지
@bot.command(name="일시정지")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ 음악을 일시정지했어요.")

# 볼륨 조절
@bot.command(name="볼륨")
async def set_volume(ctx, vol: int):
    global volume
    volume = vol / 100
    await ctx.send(f"🔊 볼륨을 {vol}%로 설정했어요.")

# TTS 채널 설정
@bot.command(name="tts채널")
async def set_tts_channel(ctx):
    global tts_channel_id
    tts_channel_id = ctx.channel.id
    await ctx.send(f"🔈 이제부터 이 채널 메시지를 TTS로 읽을게요!")

# 메시지 감지 및 TTS 실행
@bot.event
async def on_message(message):
    global tts_channel_id

    if message.author.bot:
        return

    await bot.process_commands(message)  # 이건 반드시 먼저 실행해야 명령어 인식됨

    if message.channel.id != tts_channel_id:
        return

    if not message.author.voice or not message.author.voice.channel:
        return

    voice_channel = message.author.voice.channel
    try:
        vc = await voice_channel.connect()
    except discord.ClientException:
        vc = discord.utils.get(bot.voice_clients, guild=message.guild)

    tts = gTTS(text=message.content, lang='ko')
    tts.save("tts.mp3")

    vc.play(FFmpegPCMAudio("tts.mp3"))

    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect()
    os.remove("tts.mp3")

# Render용 웹 서버 (Render는 웹 서버가 있어야 "서비스가 살아 있다"고 인식함)
app = Flask('')

@app.route('/')
def home():
    return '✅ Bot is alive!'

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(TOKEN)
