import os
import discord
from discord.ext import commands
import yt_dlp  # youtube_dl 대신 yt-dlp 사용
import asyncio

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

# 음악 큐
music_queue = []
current_song = None

# 봇이 준비되었을 때 호출
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 시간 형식 변환 함수
def format_duration(duration):
    minutes, seconds = divmod(duration, 60)
    return f"{minutes}:{seconds:02}"

# 음악 재생 함수
async def play_music(ctx):
    global current_song
    if len(music_queue) > 0:
        voice_channel = ctx.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client:
            await voice_channel.connect()
            voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        url = music_queue.pop(0)
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = next((f['url'] for f in info['formats'] if 'acodec' in f and f['acodec'] != 'none' and f['vcodec'] == 'none'), None)
                if not url2:
                    await ctx.send("오디오 스트림을 찾을 수 없습니다.")
                    return
                print(f"FFmpeg URL: {url2}")
                current_song = info['title']

            if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(source=url2, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_music(ctx), bot.loop))
                
                # 임베드 메시지 생성
                embed = discord.Embed(title="현재 재생 중", description=f"[{info['title'][:30]}...]({url})", color=discord.Color.blue())
                embed.set_thumbnail(url=info['thumbnail'])
                embed.add_field(name="곡 순번", value=str(len(music_queue) + 1), inline=True)
                embed.add_field(name="곡 길이", value=format_duration(info.get('duration', 0)), inline=True)
                embed.add_field(name="곡 링크", value=f"링크", inline=True)
                embed.add_field(name="요청자", value=ctx.author.display_name, inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send("이미 음악이 재생 중입니다.")
        except Exception as e:
            await ctx.send(f"오류 발생: {str(e)}")
            print(f"오류 발생: {str(e)}")

# 음악 재생 명령어
@bot.command(name="play")
async def play(ctx, *, search: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("음성 채널에 들어가셔야 음악을 들을 수 있습니다.")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice_client:
        await voice_channel.connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # 노래 제목으로 검색
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch:{search}", download=False)
            if not search_results['entries']:
                await ctx.send("검색 결과를 찾을 수 없습니다.")
                return
            info = search_results['entries'][0]
            url = info['webpage_url']
            music_queue.append(url)
        except Exception as e:
            await ctx.send(f"오류 발생: {str(e)}")
            return

    if not voice_client.is_playing():
        await play_music(ctx)

# 큐 보기 명령어
@bot.command(name="queue")
async def queue(ctx):
    if len(music_queue) == 0:
        await ctx.send("큐에 노래가 없습니다.")
    else:
        embed = discord.Embed(title="현재 큐", description="", color=discord.Color.blue())
        for idx, url in enumerate(music_queue):
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                embed.add_field(name=f"{idx+1}.", value=info['title'], inline=False)
        await ctx.send(embed=embed)

# 노래 스킵 명령어
@bot.command(name="skip")
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("노래를 스킵합니다.")
        await play_music(ctx)
    else:
        await ctx.send("현재 재생 중인 노래가 없습니다.")

# 음악 종료 명령어
@bot.command(name="stop")
async def stop(ctx):
    global music_queue
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        music_queue = []
        await ctx.send("음악 재생을 중지하고 큐를 비웠습니다.")

# 봇 토큰 입력 (자신의 봇 토큰을 여기에 넣어야 합니다)
bot.run(os.getenv('BOT_TOKEN'))
