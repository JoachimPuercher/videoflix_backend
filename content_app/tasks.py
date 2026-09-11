import subprocess
from pathlib import Path


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


def convert480p(source_path, playlist_path):
    convert_to_hls(source_path, playlist_path, 480)


def convert720p(source_path, playlist_path):
    convert_to_hls(source_path, playlist_path, 720)


def convert1080p(source_path, playlist_path):
    convert_to_hls(source_path, playlist_path, 1080)
