import os
import discord
from discord.ext import commands
import yt_dlp  # youtube_dl 대신 yt-dlp 사용
import asyncio
from dotenv import load_dotenv
import re 

# .env 파일 로드
load_dotenv()

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 봇 초기화 (help 명령어 제거)
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # ⬅️ help_command=None 추가

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

# 한 페이지당 표시할 곡 수
SONGS_PER_PAGE = 20

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
                
                # 요청자 태그 설정
                requester = ctx.author.display_name  

                # 임베드 메시지 생성
                embed = discord.Embed(title="현재 재생 중", description=f"🎶 [{info['title'][:30]}...]({url})", color=discord.Color.blue())
                embed.set_thumbnail(url=info['thumbnail'])
                
                # 필드 배치 조정 (한 줄에 3개씩 배치)
                embed.add_field(name="곡 길이", value=format_duration(info.get('duration', 0)), inline=True)
                embed.add_field(name="곡 순번", value="바로 재생", inline=True)
                embed.add_field(name="요청자", value=requester, inline=True)

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
                await ctx.send("🔍 검색 결과를 찾을 수 없습니다.")
                return
            info = search_results['entries'][0]
            url = info['webpage_url']
            title = info.get("title", "알 수 없는 곡")  # 제목 가져오기
            music_queue.append(url)
        except Exception as e:
            await ctx.send(f"⚠️ 오류 발생: {str(e)}")
            return

    # 현재 노래가 재생 중이라면 큐에 추가되었음을 알림
    if voice_client.is_playing():
        await ctx.send(f"📌 **{title}** (이)가 대기열에 추가되었습니다!")
    else:
        await play_music(ctx)

# 큐 보기 명령어
@bot.command(name="queue")
async def queue(ctx):
    if len(music_queue) == 0:
        await ctx.send("📭 현재 큐에 노래가 없습니다.")
        return

    # 최대 20곡까지만 표시
    display_queue = music_queue[:SONGS_PER_PAGE]

    # 메시지 업데이트 함수 (기존 메시지를 수정)
    async def update_queue_embed(message):
        embed = discord.Embed(
            title=f"📜 현재 큐 - 총 {len(music_queue)}곡",
            color=discord.Color.blue()
        )

        for idx, url in enumerate(display_queue, start=1):
            with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "알 수 없는 제목")
                duration = info.get("duration", 0)
                requester = ctx.author.display_name

            embed.add_field(
                name=f"{idx}. {title}",
                value=f"⏳ **길이:** {duration//60}:{duration%60:02d} | 👤 **요청자:** {requester}",
                inline=False
            )

        if message:
            await message.edit(embed=embed)  # 기존 메시지를 수정하여 갱신
            return message
        else:
            return await ctx.send(embed=embed)  # 새로운 메시지를 보냄

    # 첫 번째 큐 메시지 표시
    message = await update_queue_embed(None)



# 노래 스킵 명령어
@bot.command(name="skip")   
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("노래를 스킵합니다.")
        await play_music(ctx)
    else:
        await ctx.send("🚫 현재 재생 중인 노래가 없습니다.")

# 음악 종료 명령어
@bot.command(name="stop")   
async def stop(ctx):
    global music_queue
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        music_queue = []
        await ctx.send("🛑 음악 재생을 중지하고 큐를 비웠으며, 봇이 음성 채널에서 퇴장했습니다.")

@bot.command(name="help")
async def help_command(ctx):
    """📜 사용 가능한 명령어 목록을 보여줌"""
    embed = discord.Embed(title="📌 명령어 목록", description="디스코드 음악 봇의 사용 가능한 명령어들입니다.", color=discord.Color.purple())

    embed.add_field(name="🎶 `!play <노래 제목>`", value="검색한 노래를 재생합니다.", inline=False)
    embed.add_field(name="⏭️ `!skip`", value="현재 재생 중인 곡을 스킵하고 다음 곡을 재생합니다.", inline=False)
    embed.add_field(name="📋 `!queue`", value="현재 큐에 대기 중인 곡 목록을 표시합니다.", inline=False)
    embed.add_field(name="🛑 `!stop`", value="음악 재생을 중지하고 봇을 음성 채널에서 퇴장합니다.", inline=False)
    embed.add_field(name="📜 `!help`", value="사용 가능한 명령어 목록을 표시합니다.", inline=False)

    embed.set_footer(text="봇이 정상적으로 실행되지 않을 경우 봇을 다시 시작해보세요!")
    
    await ctx.send(embed=embed)

# 봇 토큰 입력 (자신의 봇 토큰을 여기에 넣어야 합니다)
bot.run(os.getenv('BOT_TOKEN'))
