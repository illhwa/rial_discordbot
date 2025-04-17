import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from gtts import gTTS

# Flask 포트 유지용
from flask import Flask
from threading import Thread

# 환경변수 로드
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ 로그인됨: {bot.user}')

@bot.command()
async def 안녕(ctx):
    await ctx.send('안녕하세요! 디스코드 봇 rial이에요! 🤖')

@bot.command()
async def 도움말(ctx):
    await ctx.send('도움이 필요하시면 Discord: `illhwa`로 연락주세요!')

@bot.command()
async def 명령어(ctx):
    msg = """📋 사용 가능한 명령어 목록:
- `!안녕`: 인사해요!
- `!도움말`: 연락처 정보를 보여줘요.
- `!명령어`: 이 도움말을 다시 보여줘요.
- `!말해 [내용]`: 음성 채널에서 TTS로 말해요.
- `!멈춰`: 음성 채널에서 나가요."""
    await ctx.send(msg)

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

@bot.command()
async def 멈춰(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ 통화방을 나갈게요! 다음에 봐요!")

# 🧠 Flask 웹서버 - Render에서 서비스 살아있게 유지용
app = Flask('')

@app.route('/')
def home():
    return "✅ Discord bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 💡 Flask는 bot.run()보다 먼저 실행해야 함!
keep_alive()
bot.run(os.getenv("BOT_TOKEN"))
