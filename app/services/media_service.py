import os, uuid
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from moviepy.editor import concatenate_videoclips
from fastapi import HTTPException   


import yt_dlp

TEMP_DIR = Path("/tmp/media")

def ensure_temp_dir():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def download_media(url: str, format_type: str) -> dict:
    ensure_temp_dir()
    file_id = str(uuid.uuid4())
    outtmpl = str(TEMP_DIR / f"{file_id}.%(ext)s")
    
    # Fixes: JS Runtime bypass & Timeouts
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 120,
        'retries': 10,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }

    if format_type == 'mp3':
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if format_type == 'mp3':
            filepath = str(TEMP_DIR / f"{file_id}.mp3")
            
        return {"title": info.get('title'), "filepath": filepath}

def trim_video(input_path: str, start: float, end: float) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
    clip = VideoFileClip(input_path).subclip(start, end)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return output_path

def extract_audio(input_path: str) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp3")
    clip = VideoFileClip(input_path)
    clip.audio.write_audiofile(output_path, logger=None)
    clip.close()
    return output_path

def add_watermark(input_path: str, image_path: str) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
    video = VideoFileClip(input_path)
    overlay = (ImageClip(image_path)
               .set_duration(video.duration)
               .resize(height=60)
               .margin(right=10, bottom=10, opacity=0)
               .set_pos(("right", "bottom")))
    final = CompositeVideoClip([video, overlay])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    video.close(); final.close()
    return output_path

def replace_audio(video_path: str, new_audio_path: str) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
    video = VideoFileClip(video_path)
    new_audio = AudioFileClip(new_audio_path)
    final = video.set_audio(new_audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    video.close(); new_audio.close(); final.close()
    return output_path

def merge_videos(video1_path: str, video2_path: str) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
    clip1 = VideoFileClip(video1_path)
    clip2 = VideoFileClip(video2_path)
    final = concatenate_videoclips([clip1, clip2])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip1.close(); clip2.close(); final.close()
    return output_path

def adjust_volume(input_path: str, multiplier: float) -> str:
    output_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
    clip = VideoFileClip(input_path)
    clip = clip.volumex(multiplier)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return output_path