import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
from discord import PCMVolumeTransformer
from gtts import gTTS
import threading
from flask import Flask

# .env 로딩
load_dotenv()

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 봇 로그인 완료 메시지
@bot.event
async def on_ready():
    print(f'✅ 로그인됨: {bot.user}')

@bot.command()
async def 안녕(ctx):
    await ctx.send('안녕하세요! 디스코드 봇이에요 🤖')

@bot.command()
async def 들어(ctx, url):
    if not ctx.author.voice:
        await ctx.send("먼저 음성 채널에 들어가 있어야 해요!")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    if vc.is_playing():
        vc.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies.txt',  # ← 이 줄 추가
        'default_search': 'auto',
    }

    ffmpeg_options = {
        'options': '-vn'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info['url']

    # ffmpeg 경로 (Render는 시스템에 설치되어 있어 지정 불필요)
    vc.play(discord.FFmpegPCMAudio(stream_url, **ffmpeg_options))
    await ctx.send(f"🎶 지금 재생 중: {info['title']}")

@bot.command()
async def 멈춰(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ 음악을 멈췄어요!")

@bot.command()
async def 일시정지(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ 음악을 일시정지했어요!")

@bot.command()
async def 다시재생(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ 음악을 다시 재생했어요!")

@bot.command()
async def 볼륨(ctx, volume: float):
    vc = ctx.voice_client
    if not vc or not vc.is_playing():
        await ctx.send("지금 재생 중인 음악이 없어요!")
        return
    if volume < 0.0 or volume > 2.0:
        await ctx.send("볼륨은 0.0부터 2.0 사이로 설정할 수 있어요.")
        return

    vc.source = PCMVolumeTransformer(vc.source, volume)
    await ctx.send(f"🔊 볼륨을 {volume:.1f}으로 설정했어요.")

@bot.command()
async def 말해(ctx, *, text: str):
    if not ctx.author.voice:
        await ctx.send("먼저 음성 채널에 들어가 있어야 해요!")
        return

    vc = ctx.voice_client
    if vc is None:
        vc = await ctx.author.voice.channel.connect()

    tts = gTTS(text=text, lang='ko')
    tts.save("tts.mp3")

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio("tts.mp3"))
    await ctx.send(f"🗣️ `{text}` 라고 말했어요.")

# --------------------
# Flask 가짜 웹 서버 (Render 웹 서비스용)
# --------------------
app = Flask('')

@app.route('/')
def home():
    return "봇 작동 중입니다!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# 디스코드 봇 실행
bot.run(os.getenv("BOT_TOKEN"))
