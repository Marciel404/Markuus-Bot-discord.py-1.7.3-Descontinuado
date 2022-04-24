import asyncio,functools,itertools,math,random,discord, youtube_dl

from async_timeout import timeout
from discord.ext import commands
from Outhers.Random import better_time, banip

class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')
        if self.disliskes == None:
            self.dislikes = 'Não informado'
        if self.likes == None:
            self.likes = 'Não informado'

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Não foi possível encontrar nada que corresponda `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Não foi possível encontrar nada que corresponda `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Não foi possível buscar `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Não foi possível recuperar nenhuma correspondência para `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} dias'.format(days))
        if hours > 0:
            duration.append('{} horas'.format(hours))
        if minutes > 0:
            duration.append('{} minutos'.format(minutes))
        if seconds > 0:
            duration.append('{} segundos'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Tocando agora',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duração', value=self.source.duration)
                 .add_field(name='Pedido por', value=self.requester.mention)
                 .add_field(name='Publicado por', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .add_field(name = 'Likes', value = self.source.likes)
                 .add_field(name = 'Dislikes', value = self.source.dislikes)
                 .set_thumbnail(url=self.source.thumbnail))

        return embed



class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(180):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('Esse Comando não pode ser usado no privado')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply('Aconteceu um erro: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True, aliases = ['j'])
    async def _join(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return

            destination = ctx.author.voice.channel
            if ctx.voice_state.voice:
                await ctx.voice_state.voice.move_to(destination)
                return

            ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return 

            if not ctx.voice_state.voice:
                return await ctx.reply('Não estou em nenhum canal de voz')

            ctx.voice_state.songs.clear()
            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return

            if not ctx.voice_state.is_playing:
                return await ctx.reply('Não estou tocando nada nesse moemnto')

            if 0 > volume > 100:
                return await ctx.reply('O volume deve estar entre 0 e 100')

            ctx.voice_state.volume = volume / 100
            await ctx.reply('Volume do player está em {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if ctx.author.id == banip:
                return
            elif rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')

            await ctx.reply(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause', aliases = ['ps']) 
    async def _pause(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if ctx.author.id == banip:
                return
            elif rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')

            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

            if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
                await ctx.voice_state.voice.pause()
                await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if ctx.author.id == banip:
                return
            elif rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')

            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

            if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
                ctx.voice_state.voice.resume()
                await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if ctx.author.id == banip:
                return
            elif rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')


            ctx.voice_state.songs.clear()
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

            if not ctx.voice_state.is_playing:
                ctx.voice_state.voice.stop()
                await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases = ['s'])
    async def _skip(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if ctx.author.id == banip:
                return
            elif rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')

            if not ctx.voice_state.is_playing:
                return await ctx.reply('Não estou tocando nada agora')

            voter = ctx.message.author
            if voter == ctx.voice_state.current.requester:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()

            elif voter.id not in ctx.voice_state.skip_votes:
                ctx.voice_state.skip_votes.add(voter.id)
                total_votes = len(ctx.voice_state.skip_votes)

                if total_votes >= 3:
                    await ctx.message.add_reaction('⏭')
                    ctx.voice_state.skip()
                else:
                    await ctx.reply('Votos para pular **{}/3**'.format(total_votes))

            else:
                await ctx.reply('Você já votou para pular essa musica')

    @commands.command(name='queue', aliases = ['q'])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            if len(ctx.voice_state.songs) == 0:
                return await ctx.reply('Empty queue.')

            items_per_page = 10
            pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

            start = (page - 1) * items_per_page
            end = start + items_per_page

            queue = ''
            for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
                queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

            embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                    .set_footer(text='Vendo a pagina {}/{}'.format(page, pages)))
            await ctx.reply(embed=embed)

    @commands.command(name='remove', aliases = ['r'])
    async def _remove(self, ctx: commands.Context, index: int):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return

            if len(ctx.voice_state.songs) == 0:
                return await ctx.reply('Lista vazia')

            ctx.voice_state.songs.remove(index - 1)
            await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return

            if not ctx.voice_state.is_playing:
                return await ctx.reply('Não estou tocando nada no momento')

            ctx.voice_state.loop = not ctx.voice_state.loop
            await ctx.message.add_reaction('✅')

    @commands.command(name='play', aliases = ['p'])
    async def _play(self, ctx: commands.Context, *, search: str = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.reply('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
                
            if search == None:
                search = 'Joji - SLOW DANCING IN THE DARK'

            if not ctx.voice_state.voice:
                ctx.voice_state.songs.clear()

            if not ctx.voice_state.voice:
                await ctx.invoke(self._join)

            async with ctx.typing():
                try:
                    source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                except YTDLError as e:
                    await ctx.reply('Ocorreu um erro: {}'.format(str(e)))
                else:
                    song = Song(source)

                    await ctx.voice_state.songs.put(song)
                    await ctx.reply('Adicionado a lista {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('Você não está conectado a nenhum canal.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Eu já estou em um canal de voz.')

def setup(bot:commands.Bot):
    bot.add_cog(Music(bot))
