"""ffmpeg jobs run by the rq worker after a video upload.

Each job gets plain arguments (id or paths), never model instances, and
runs ffmpeg as an argument list with check=True so failures land in the
rq failed registry instead of leaving empty folders behind.
"""

import os
import subprocess
from pathlib import Path

from django.conf import settings


def create_thumbnail(video_id: int):
    """Grab one frame from the uploaded video and store its public URL in thumbnail_url.

    A URL entered by hand in the admin is kept; only an empty field is filled.
    """
    from content_app.models import Video  # local import: tasks is imported by signals.py

    video = Video.objects.get(pk=video_id)
    thumbnail = video.get_thumbnail_path()
    thumbnail.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", "00:00:06",                      # skip a possible black fade-in
        "-i", video.video_file.path,
        "-frames:v", "1",
        "-vf", "scale=640:-2",
        str(thumbnail),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    if not video.thumbnail_url:
        relative = thumbnail.relative_to(settings.MEDIA_ROOT).as_posix()
        video.thumbnail_url = f"{os.getenv('BACKEND_URL')}{settings.MEDIA_URL}{relative}"
        video.save(update_fields=["thumbnail_url"])


def convert_to_hls(source_path, playlist_path, height: int):
    """Transcode the source video into an HLS playlist plus .ts segments for one resolution.

    playlist_path is the target index.m3u8 (as returned by Video.get_path). The segments
    are written next to it as 000.ts, 001.ts, ... so the playlist can reference them
    by bare file name.
    """
    playlist = Path(playlist_path)
    folder = playlist.parent
    folder.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                                   # overwrite without asking (no tty in the worker)
        "-i", str(source_path),
        "-vf", f"scale=-2:{height}",            # keep aspect ratio, width stays divisible by 2
        "-c:v", "libx264",
        "-crf", "23",
        "-c:a", "aac",
        "-f", "hls",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(folder / "%03d.ts"),
        str(playlist),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


# One named job per resolution so the rq dashboard shows what is running.
def convert480p(source_path, playlist_path):
    """rq job: render the 480p HLS variant."""
    convert_to_hls(source_path, playlist_path, 480)


def convert720p(source_path, playlist_path):
    """rq job: render the 720p HLS variant."""
    convert_to_hls(source_path, playlist_path, 720)


def convert1080p(source_path, playlist_path):
    """rq job: render the 1080p HLS variant."""
    convert_to_hls(source_path, playlist_path, 1080)
