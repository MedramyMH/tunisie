import os, uuid, asyncio
from fastapi import APIRouter, Request, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.services.media_service import (
    download_media, trim_video, extract_audio, 
    add_watermark, replace_audio, merge_videos, adjust_volume, TEMP_DIR
)

router = APIRouter()

def cleanup_file(path: str):
    if os.path.exists(path):
        try: os.remove(path)
        except: pass

@router.get("/downloader")
async def downloader_page(request: Request):
    # Pass dummy request context for template
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("downloader.html", {"request": request})

@router.post("/api/download")
async def api_download(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    url = form["url"]
    fmt = form["format"]
    
    try:
        result = await asyncio.to_thread(download_media, url, fmt)
        filepath = result["filepath"]
        filename = f"{result['title'][:50]}.{fmt}"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '-', '_')).rstrip()
        
        background_tasks.add_task(cleanup_file, filepath)
        return FileResponse(filepath, filename=filename, background=background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/process-video")
async def api_process_video(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    tool = form.get("tool")
    
    video_file = form.get("video_file")
    if not video_file or not video_file.filename:
        raise HTTPException(400, "Upload a video file first.")
        
    video_path = str(TEMP_DIR / f"{uuid.uuid4()}_{video_file.filename}")
    with open(video_path, "wb") as f:
        f.write(await video_file.read())
        
    output_path = None
    out_filename = f"edited_{uuid.uuid4()}.mp4"
    
    try:
        if tool == "trim":
            start = float(form.get("start_time", 0))
            end = float(form.get("end_time", 60))
            output_path = await asyncio.to_thread(trim_video, video_path, start, end)
            
        elif tool == "extract_audio":
            output_path = await asyncio.to_thread(extract_audio, video_path)
            out_filename = f"audio_{uuid.uuid4()}.mp3"
            
        elif tool == "watermark":
            img_file = form.get("watermark_image")
            if not img_file: raise HTTPException(400, "Provide watermark image")
            img_path = str(TEMP_DIR / f"{uuid.uuid4()}_{img_file.filename}")
            with open(img_path, "wb") as f: f.write(await img_file.read())
            output_path = await asyncio.to_thread(add_watermark, video_path, img_path)
            cleanup_file(img_path)
            
        elif tool == "replace_audio":
            aud_file = form.get("new_audio")
            if not aud_file: raise HTTPException(400, "Provide new audio track")
            aud_path = str(TEMP_DIR / f"{uuid.uuid4()}_{aud_file.filename}")
            with open(aud_path, "wb") as f: f.write(await aud_file.read())
            output_path = await asyncio.to_thread(replace_audio, video_path, aud_path)
            cleanup_file(aud_path)
            
        elif tool == "merge":
            vid2 = form.get("video_file_2")
            if not vid2: raise HTTPException(400, "Provide second video")
            vid2_path = str(TEMP_DIR / f"{uuid.uuid4()}_{vid2.filename}")
            with open(vid2_path, "wb") as f: f.write(await vid2.read())
            output_path = await asyncio.to_thread(merge_videos, video_path, vid2_path)
            cleanup_file(vid2_path)

        elif tool == "volume":
            vol = float(form.get("volume_multiplier", 1.0))
            output_path = await asyncio.to_thread(adjust_volume, video_path, vol)

        if output_path:
            background_tasks.add_task(cleanup_file, video_path)
            background_tasks.add_task(cleanup_file, output_path)
            return FileResponse(output_path, filename=out_filename, background=background_tasks)
            
        raise HTTPException(500, "Processing failed")
    except HTTPException:
        raise
    except Exception as e:
        cleanup_file(video_path)
        raise HTTPException(status_code=500, detail=str(e))