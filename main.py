import os
import json
import yt_dlp
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# إعدادات الواجهة
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# دالة مراقبة التحميل
def progress_hook(d):
    if d['status'] == 'downloading':
        # طباعة معلومات التحميل في الـ Terminal للمتابعة
        print(f"تحميل: {d.get('_percent_str')} | السرعة: {d.get('_speed_str')} | المتبقي: {d.get('_eta_str')}")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze")
async def analyze_video(url: str):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # إضافة خيار الصوت فقط
            formats.append({'format_id': 'bestaudio', 'note': 'MP3 (Audio Only)', 'type': 'audio'})
            
            # إضافة خيارات الفيديو
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('height'):
                    formats.append({
                        'format_id': f['format_id'],
                        'note': f"{f.get('height')}p - {f.get('ext')}",
                        'type': 'video'
                    })
            return {"title": info.get('title'), "formats": formats}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download")
async def download_video(url: str, format: str, type: str):
    try:
        ydl_opts = {
            'format': format if type == 'video' else 'bestaudio/best',
            'progress_hooks': [progress_hook], # ربط دالة المراقبة
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
        
        if type == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
        return FileResponse(path=filename, media_type='application/octet-stream', filename=os.path.basename(filename))
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)