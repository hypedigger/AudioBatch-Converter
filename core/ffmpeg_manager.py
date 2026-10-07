import os
import shutil
import zipfile
import urllib.request
import urllib.error
from core.config import FFMPEG_DIR, FFMPEG_DOWNLOAD_URL


class FFmpegManager:
    def __init__(self):
        self._ffmpeg_path  = None
        self._ffprobe_path = None
        self._locate()

    # ── Public ───────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        return self._ffmpeg_path is not None and os.path.isfile(self._ffmpeg_path)

    def get_ffmpeg_path(self) -> str:
        return self._ffmpeg_path

    def get_ffprobe_path(self) -> str:
        return self._ffprobe_path

    def download(self, progress_callback=None, status_callback=None):
        """
        Download FFmpeg zip, extract ffmpeg.exe + ffprobe.exe to FFMPEG_DIR.

        progress_callback(bytes_downloaded, total_bytes)
        status_callback(message: str)
        """
        os.makedirs(FFMPEG_DIR, exist_ok=True)
        zip_path = os.path.join(FFMPEG_DIR, "ffmpeg_download.zip")

        if status_callback:
            status_callback("Connexion au serveur…")

        def _reporthook(block_num, block_size, total_size):
            if progress_callback:
                downloaded = block_num * block_size
                progress_callback(downloaded, total_size)

        try:
            urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, zip_path, _reporthook)
        except urllib.error.URLError as e:
            raise RuntimeError(f"Erreur de téléchargement : {e}") from e

        if status_callback:
            status_callback("Extraction…")

        self._extract_zip(zip_path, status_callback)

        try:
            os.remove(zip_path)
        except OSError:
            pass

        self._locate()

        if not self.is_available():
            raise RuntimeError("FFmpeg introuvable après extraction.")

        if status_callback:
            status_callback("FFmpeg installé avec succès.")

    # ── Private ──────────────────────────────────────────────────────────────

    def _locate(self):
        # 1. Look in FFMPEG_DIR
        candidate = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
        if os.path.isfile(candidate):
            self._ffmpeg_path  = candidate
            self._ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")
            return

        # 2. Fall back to system PATH
        found = shutil.which("ffmpeg")
        if found:
            self._ffmpeg_path  = found
            self._ffprobe_path = shutil.which("ffprobe") or ""

    def _extract_zip(self, zip_path: str, status_callback=None):
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.namelist()
            for member in members:
                basename = os.path.basename(member)
                if basename in ("ffmpeg.exe", "ffprobe.exe"):
                    if status_callback:
                        status_callback(f"Extraction de {basename}…")
                    dest = os.path.join(FFMPEG_DIR, basename)
                    with zf.open(member) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
