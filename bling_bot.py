import os
import discord
from discord.ext import commands
import yt_dlp  # youtube_dl 대신 yt-dlp 사용

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# FFmpeg 설정
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel debug'  # 로그 레벨 추가
}

# YouTube-DL 설정
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}

# 봇이 준비되었을 때 호출
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 음악 재생 명령어
@bot.command(name="play")
async def play(ctx, url):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("음성 채널에 들어가셔야 음악을 들을 수 있습니다.")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice_client:
        await voice_channel.connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            # 오디오 스트림 URL 추출
            url2 = next((f['url'] for f in info['formats'] if 'acodec' in f and f['acodec'] != 'none' and f['vcodec'] == 'none'), None)
            if not url2:
                await ctx.send("오디오 스트림을 찾을 수 없습니다.")
                return
            print(f"FFmpeg URL: {url2}")

        if not voice_client.is_playing():
            voice_client.play(discord.FFmpegPCMAudio(source=url2, **FFMPEG_OPTIONS))
            await ctx.send(f"노래를 재생합니다: {info['title']}")
        else:
            await ctx.send("이미 음악이 재생 중입니다.")
    except Exception as e:
        await ctx.send(f"오류 발생: {str(e)}")
        print(f"오류 발생: {str(e)}")

# 음악 종료 명령어
@bot.command(name="stop")
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()

# 봇 토큰 입력 (환경 변수에서 가져오기)
bot.run(os.getenv('BOT_TOKEN'))
