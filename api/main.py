import os
import json
import yt_dlp
import traceback
import tempfile
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
        print(traceback.format_exc()) # سيطبع الخطأ كاملاً في السجلات
        return {"error": "فشل التحليل، راجع السجلات"}

@app.get("/download")
async def download_video(url: str, format: str, type: str):
    try:
        temp_dir = tempfile.gettempdir()
        file_base = "downloaded_file"
        
        # إعدادات التحميل: بدون أي معالجة لاحقة (FFmpeg)
        ydl_opts = {
            'format': format if type == 'video' else 'bestaudio/best',
            'outtmpl': f'{temp_dir}/{file_base}.%(ext)s',
            'restrictfilenames': True,
            'postprocessors': [], # هذا السطر يمنع الخطأ تماماً
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp سيقوم بتسمية الملف بناءً على الامتداد المتوفر (m4a, webm, mp4)
            ext = info.get('ext')
            final_path = os.path.join(temp_dir, f"{file_base}.{ext}")
            
            return FileResponse(
                path=final_path, 
                media_type='audio/mpeg' if type == 'audio' else 'video/mp4', 
                filename=f"Tornado_Download.{ext}"
            )
        
    except Exception as e:
        print(traceback.format_exc())
        return {"error": f"خطأ في التحميل: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)