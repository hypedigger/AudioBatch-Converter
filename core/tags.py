"""
Lecture / écriture des tags et pochettes via mutagen.

Formats éditables : MP3, FLAC, OGG Vorbis, Opus, M4A/AAC.
Les autres (WMA, MPC, APE, WV…) restent en lecture impossible → is_editable() = False.
"""
import base64
from typing import Dict, Optional

# Champs standards exposés à l'éditeur (clé mutagen "easy" → libellé UI)
TAG_FIELDS = [
    ("title",       "Titre"),
    ("artist",      "Artiste"),
    ("album",       "Album"),
    ("albumartist", "Artiste de l'album"),
    ("date",        "Année"),
    ("genre",       "Genre"),
    ("tracknumber", "Piste n°"),
]

_EDITABLE_EXTS = {"mp3", "flac", "ogg", "opus", "m4a"}


def is_editable(ext: str) -> bool:
    return ext.lower().lstrip(".") in _EDITABLE_EXTS


# ── Tags texte ────────────────────────────────────────────────────────────────

def read_tags(path: str) -> Dict[str, str]:
    """Return {champ: valeur} pour tous les TAG_FIELDS (chaîne vide si absent)."""
    from mutagen import File
    audio = File(path, easy=True)
    if audio is None:
        raise RuntimeError("Format non reconnu par mutagen")

    out = {}
    for key, _label in TAG_FIELDS:
        values = audio.get(key)
        out[key] = str(values[0]) if values else ""
    return out


def write_tags(path: str, tags: Dict[str, str]) -> None:
    """Écrit les champs donnés ; une valeur vide supprime le tag."""
    from mutagen import File
    audio = File(path, easy=True)
    if audio is None:
        raise RuntimeError("Format non reconnu par mutagen")

    for key, value in tags.items():
        value = value.strip()
        if value:
            audio[key] = [value]
        elif key in audio:
            del audio[key]
    audio.save()


# ── Pochette ──────────────────────────────────────────────────────────────────

def read_cover(path: str) -> Optional[bytes]:
    """Return les octets de la pochette embarquée, ou None."""
    ext = path.rsplit(".", 1)[-1].lower()

    if ext == "mp3":
        from mutagen.id3 import ID3, ID3NoHeaderError
        try:
            id3 = ID3(path)
        except ID3NoHeaderError:
            return None
        pics = id3.getall("APIC")
        return pics[0].data if pics else None

    if ext == "flac":
        from mutagen.flac import FLAC
        pics = FLAC(path).pictures
        return pics[0].data if pics else None

    if ext == "m4a":
        from mutagen.mp4 import MP4
        tags = MP4(path).tags
        covr = tags.get("covr") if tags else None
        return bytes(covr[0]) if covr else None

    if ext in ("ogg", "opus"):
        from mutagen import File
        from mutagen.flac import Picture
        audio = File(path)
        b64 = audio.get("metadata_block_picture")
        if not b64:
            return None
        try:
            return Picture(base64.b64decode(b64[0])).data
        except Exception:
            return None

    return None


def write_cover(path: str, data: bytes, mime: str) -> None:
    """Remplace la pochette embarquée (type 3 = front cover)."""
    ext = path.rsplit(".", 1)[-1].lower()

    if ext == "mp3":
        from mutagen.id3 import ID3, APIC, ID3NoHeaderError
        try:
            id3 = ID3(path)
        except ID3NoHeaderError:
            id3 = ID3()
        id3.delall("APIC")
        id3.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
        id3.save(path, v2_version=3)
        return

    if ext == "flac":
        from mutagen.flac import FLAC, Picture
        audio = FLAC(path)
        audio.clear_pictures()
        pic = Picture()
        pic.type = 3
        pic.mime = mime
        pic.data = data
        audio.add_picture(pic)
        audio.save()
        return

    if ext == "m4a":
        from mutagen.mp4 import MP4, MP4Cover
        fmt = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
        audio = MP4(path)
        audio["covr"] = [MP4Cover(data, imageformat=fmt)]
        audio.save()
        return

    if ext in ("ogg", "opus"):
        from mutagen import File
        from mutagen.flac import Picture
        audio = File(path)
        pic = Picture()
        pic.type = 3
        pic.mime = mime
        pic.data = data
        audio["metadata_block_picture"] = [
            base64.b64encode(pic.write()).decode("ascii")
        ]
        audio.save()
        return

    raise RuntimeError(f"Pochette non gérée pour le format .{ext}")
