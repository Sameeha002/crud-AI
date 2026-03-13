from tools.chinook_db import get_session, get_classes
from langchain_core.tools import tool

@tool
def get_albums_by_artist(artist: str):
    """Get all albums by an artist from the music database."""
    session = get_session()
    try:
        classes = get_classes()
        Artist = classes.Artist
        Album = classes.Album

        results = (
            session.query(Album.Title, Artist.Name)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .filter(Artist.Name.ilike(f"%{artist}%"))
        )
        if not results:
            return f"No albums found for artist: {artist}"

        return [{"Album": r.Title, "Artist": r.Name} for r in results]
    finally:
        session.close()

@tool
def get_tracks_by_artist(artist: str):
    """Get all tracks/songs by an artist from the music database."""
    session = get_session()

    try:
        classes = get_classes()
        Artist = classes.Artist
        Album = classes.Album
        Track = classes.Track

        results  = (
            session.query(Track.Name, Artist.Name)
            .join(Artist, Album.ArtistId == Artist.ArtistId )
            .join(Track, Track.AlbumId == Album.AlbumId )
            .filter(Artist.Name.ilike(f"%{artist}%"))
            .all()
        )
        if not results:
            return f"No tracks found for artist: {artist}"

        return [{"Track": r[0], "Artist": r[1]} for r in results]
    finally:
        session.close()


@tool
def get_tracks_by_genre(genre: str):
    """Get all tracks belonging to a specific music genre."""
    session = get_session()
    try:
        classes = get_classes()
        Track = classes.Track
        Genre = classes.Genre
        Album = classes.Album
        Artist = classes.Artist

        results = (
            session.query(Track.Name, Artist.Name, Genre.Name)
            .join(Album, Track.AlbumId == Album.AlbumId)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .join(Genre, Track.GenreId == Genre.GenreId)
            .filter(Genre.Name.ilike(f"%{genre}%"))
            .limit(20)
            .all()
        )

        if not results:
            return f"No tracks found for genre: {genre}"

        return [{"Track": r[0], "Artist": r[1], "Genre": r[2]} for r in results]
    finally:
        session.close()


@tool
def check_for_songs(song_title: str):
    """Check if a song exists in the database by its title."""
    session = get_session()
    try:
        classes = get_classes()
        Track = classes.Track
        Album = classes.Album
        Artist = classes.Artist

        results = (
            session.query(Track.Name, Artist.Name, Album.Title)
            .join(Album, Track.AlbumId == Album.AlbumId)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .filter(Track.Name.ilike(f"%{song_title}%"))
            .all()
        )

        if not results:
            return f"No songs found with title: {song_title}"

        return [{"Track": r[0], "Artist": r[1], "Album": r[2]} for r in results]
    finally:
        session.close()

music_tools = [get_albums_by_artist, get_tracks_by_artist, get_tracks_by_genre, check_for_songs]
