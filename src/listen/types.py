from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import time
from typing import Any, Literal, NewType, Optional, Self, Type, Union

AlbumID = NewType('AlbumID', int)
ArtistID = NewType('ArtistID', int)
CharacterID = NewType('CharacterID', int)
SongID = NewType('SongID', int)
SourceID = NewType('SourceID', int)


@dataclass
class Link:
    name: str
    url: str

    @classmethod
    def from_name(
        cls: Type[Self],
        type: Literal[
            'albums',
            'artists',
            'sources'
        ],
        value: Optional[str] = None
    ) -> Self | None:

        if not value:
            return None

        cdn = "https://cdn.listen.moe"
        match type:
            case 'albums':
                url = f'{cdn}/covers/{value}'
            case 'artists':
                url = f'{cdn}/artists/{value}'
            case 'sources':
                url = f'{cdn}/source/{value}'

        return cls(name=value, url=url)


@dataclass
class User:
    uuid: str
    username: str
    display_name: str
    bio: str | None
    favorites: int
    uploads: int
    requests: int
    feed: list["SystemFeed"]
    link: str = field(init=False)

    def __post_init__(self):
        self.link = f'https://listen.moe/u/{self.username}'


@dataclass
class CurrentUser(User):
    token: str


@dataclass
class Album:
    id: AlbumID
    name: str | None
    name_romaji: str | None
    image: Link | None
    link: str = field(init=False)

    def __post_init__(self):
        self.link = f'https://listen.moe/albums/{self.id}'


@dataclass
class Artist:
    id: ArtistID
    name: str | None
    name_romaji: str | None
    image: Link | None
    character: list["Character"] | None
    link: str = field(init=False)

    def __post_init__(self):
        self.link = f'https://listen.moe/artists/{self.id}'


@dataclass
class Character:
    id: CharacterID
    name: Optional[str] = None
    name_romaji: Optional[str] = None
    link: str = field(init=False)

    def __post_init__(self):
        self.link = f'https://listen.moe/characters/{self.id}'


@dataclass
class Source:
    id: SourceID
    name: str | None
    name_romaji: str | None
    image: Link | None
    link: str = field(init=False)

    def __post_init__(self):
        self.link = f'https://listen.moe/sources/{self.id}'


@dataclass
class Requester:
    uuid: str
    username: str
    display_name: str
    link: str = field(init=False)

    @classmethod
    def from_data(cls: Type[Self], data: dict[str, Any] | None) -> Self | None:
        if not data:
            return None
        return cls(
            uuid=data['uuid'],
            username=data['username'],
            display_name=data['displayName']
        )

    def __post_init__(self):
        self.link = f'https://listen.moe/u/{self.username}'


@dataclass
class Song:
    @classmethod
    def from_data(cls: Type[Self], data: dict[str, Any]) -> Self:
        duration = data.get('duration', None)
        kwargs = {
            'id': data['id'],
            'duration': duration,
            'time_end': round(time() + duration) if duration else round(time()),
            'title': Song._get_title(data),
            'sources': Song._get_sources(data),
            'artists': Song._get_artists(data),
            'albums': Song._get_albums(data),
            'characters': Song._get_characters(data),
        }
        if (p := data.get('played', None)):
            kwargs.update({'played': p})
        if (p := data.get('titleRomaji', None)):
            kwargs.update({'title_romaji': p})

        return cls(**kwargs)  # pyright: ignore

    @staticmethod
    def _sanitise(word: str | None) -> str | None:
        if not word:
            return None
        return word.replace('\u3099', '\u309B').replace('\u309A', '\u309C').replace('\u200b', '')

    @staticmethod
    def _get_title(song: dict[str, Any]) -> str:
        title: str = song.get('title', None)
        if title:
            title = Song._sanitise(title)  # pyright: ignore[reportGeneralTypeIssues]
        return title

    @staticmethod
    def _get_sources(song: dict[str, Any]) -> list[Source] | None:
        sources = song.get('sources')
        if not sources:
            return None

        return [Source(
            id=source['id'],
            name=Song._sanitise(source.get('name')),
            name_romaji=source.get('nameRomaji'),
            image=Link.from_name('sources', source.get('image'))
        ) for source in sources]

    @staticmethod
    def _get_artists(song: dict[str, Any]) -> list[Artist] | None:
        artists = song.get('artists')
        if not artists:
            return None
        return [Artist(
            id=artist['id'],
            name=Song._sanitise(artist.get('name')),
            name_romaji=Song._sanitise(artist.get('nameRomaji')),
            image=Link.from_name('artists', artist.get('image')),
            character=[
                Character(character['id']) for character in artist.get('characters')
            ] if len(artist.get('characters')) != 0 else None
        ) for artist in artists]

    @staticmethod
    def _get_albums(song: dict[str, Any]) -> list[Album] | None:
        albums = song.get('albums')
        if not albums:
            return None
        return [Album(
            id=album['id'],
            name=Song._sanitise(album.get('name')),
            name_romaji=Song._sanitise(album.get('nameRomaji')),
            image=Link.from_name('albums', album.get('image'))
        ) for album in albums]

    @staticmethod
    def _get_characters(song: dict[str, Any]) -> list[Character] | None:
        characters = song.get('characters')
        if not characters:
            return None
        return [Character(
            id=character['id'],
            name=Song._sanitise(character.get('name')),
            name_romaji=Song._sanitise(character.get('nameRomaji'))
        ) for character in characters]

    @staticmethod
    def _list_to_string(lst: list[Artist] | list[Source] | list[Album] | None,
                        romaji_first: bool = True, sep: str = ', ') -> str | None:
        if not lst:
            return None
        lst_string: list[str] = []
        for item in lst:
            if romaji_first:
                name = item.name_romaji if item.name_romaji else item.name
            else:
                name = item.name
            if name:
                lst_string.append(name)
        return f"{sep}".join(lst_string)

    def artists_to_string(self, romaji_first: bool = True, sep: str = ', ') -> str | None:
        if not self.artists:
            return None
        name = None
        char_name = None
        lst_string: list[str] = []
        character_map: dict[int, Character] = {}

        if self.characters:
            for character in self.characters:
                character_map[character.id] = character

        for artist in self.artists:
            if romaji_first:
                name = artist.name_romaji if artist.name_romaji else artist.name
            else:
                name = artist.name

            if self.characters and artist.character:
                for character in artist.character:
                    if (char := character_map.get(character.id)):
                        if romaji_first:
                            char_name = char.name_romaji if char.name_romaji else char.name
                        else:
                            char_name = char.name

                if name and char_name:
                    lst_string.append(f'{char_name} (CV: {name})')
            elif name:
                lst_string.append(name)

        return f"{sep}".join(lst_string)

    def sources_to_string(self, romaji_first: bool = True, sep: str = ', ') -> str | None:
        return self._list_to_string(self.sources, romaji_first=romaji_first, sep=sep)

    def albums_to_string(self, romji_first: bool = True, sep: str = ', ') -> str | None:
        return self._list_to_string(self.albums, romaji_first=romji_first, sep=sep)

    @staticmethod
    def _get_image(lst: list[Artist] | list[Source] | list[Album] | None, url: bool) -> str | None:
        if not lst:
            return None
        for item in lst:
            if not item.image:
                break
            if url:
                return item.image.url
            else:
                return item.image.name
        return None

    def artist_image(self, url: bool = False) -> str | None:
        return self._get_image(self.artists, url)

    def source_image(self, url: bool = False) -> str | None:
        return self._get_image(self.sources, url)

    def album_image(self, url: bool = False) -> str | None:
        return self._get_image(self.albums, url)

    id: int
    title: str | None
    sources: list["Source"] | None
    artists: list["Artist"] | None
    characters: list["Character"] | None
    albums: list["Album"] | None
    duration: int | None
    time_end: int
    played: Optional[int] = None
    title_romaji: Optional[str] = None


@dataclass
class SystemFeed:
    type: int
    created_at: str
    song: Song

    @classmethod
    def from_data(cls: Type[Self], data: dict[str, Any]) -> Self:
        return cls(
            type=data['type'],
            created_at=data['createdAt'],
            song=Song.from_data(data['song'])
        )


@dataclass
class ListenWsData:
    @classmethod
    def from_data(cls: Type[Self], data: dict[str, Any]) -> Self:
        """
        A dataclass representation of listen.moe websocket data

        Args:
            data `dict`: The websocket data
        Return:
            Self `ListenWsData`
        """
        return cls(
            _op=data['op'],
            _t=data['t'],
            start_time=datetime.fromisoformat(data['d']['startTime']),
            listener=data['d']['listeners'],
            requester=Requester.from_data(data['d'].get('requester')),
            event=data['d'].get('event'),
            song=Song.from_data(data['d']['song']),
            last_played=[Song.from_data(song) for song in data['d']['lastPlayed']]
        )

    _op: int
    _t: str
    song: Song
    requester: Requester | None
    event: str | None
    start_time: datetime
    last_played: list["Song"]
    listener: int
    last_heartbeat: float = time()


@dataclass
class DemuxerCacheState:
    """
    For more information, see https://mpv.io/manual/master/#command-interface-demuxer-cache-state
    """
    cache_end: float
    """`cache_end`: total demuxer cache time (seconds)"""
    cache_duration: float
    """`cache_duration`: amount of cache (seconds)"""
    fw_byte: int
    """`fw_byte`: no. bytes buffered size from current decoding pos"""
    total_bytes: int
    """`total_bytes`: sum of cached seekable range"""
    seekable_start: float
    """`seekable_start`: approx timestamp of start of buffered range"""
    seekable_end: float | None
    """`seekable_end`: approx timestamp of end of buffered range"""

    @classmethod
    def from_cache_state(cls: Type[Self], data: dict[str, Any]) -> Self:
        cache_end = float(data.get('cache-end', -1))
        cache_duration = float(data.get('cache-duration', -1))
        fw_byte = int(data.get('fw-bytes', -1))
        total_bytes = int(data.get('total-bytes', -1))
        seekable_start = float(data.get('reader-pts', -1))
        seekable_ranges = data.get('seekable-ranges')

        if seekable_ranges:
            seekable_end = float(seekable_ranges[0].get('end', -1))
        else:
            seekable_end = None

        return cls(cache_end, cache_duration, fw_byte, total_bytes, seekable_start, seekable_end)


@dataclass
class MPVData:
    start: datetime
    track: str | None
    genre: str | None
    title: str | None
    artist: str | None
    year: str | None
    date: str | None
    album: str | None
    comment: str | None
    _ENCODER: str
    _icy_br: str
    _icy_genre: str
    _icy_name: str
    _icy_pub: str
    _icy_url: str

    @classmethod
    def from_metadata(cls: Type[Self], data: dict[str, Any]) -> Self:
        return cls(
            start=datetime.now(timezone.utc),
            track=data.get('track'),
            genre=data.get('genre'),
            title=data.get('title'),
            artist=data.get('artist'),
            year=data.get('year'),
            date=data.get('date'),
            album=data.get('album'),
            comment=data.get('comment'),
            _ENCODER=data['ENCODER'],
            _icy_br=data['icy-br'],
            _icy_genre=data['icy-genre'],
            _icy_name=data['icy-name'],
            _icy_pub=data['icy-pub'],
            _icy_url=data['icy-url'],
        )


if __name__ == "__main__":
    import asyncio
    import json

    import websockets.client as websocket
    from rich.pretty import pprint

    async def get_data():
        async for ws in websocket.connect('wss://listen.moe/gateway_v2', ping_interval=None, ping_timeout=None):
            while True:
                data = json.loads(await ws.recv())

                if data['op'] == 1:
                    await ws.close()
                    return data
    loop = asyncio.new_event_loop()
    data = loop.run_until_complete(get_data())
    e = ListenWsData.from_data(data)  # pyright: ignore[reportGeneralTypeIssues]
    pprint(e)
    pprint(e.song.sources_to_string())
    pprint(e.song.artists_to_string())
