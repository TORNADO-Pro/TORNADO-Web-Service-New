import os
import json
import yt_dlp
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import tempfile

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
        # استخدام مجلد مؤقت بدلاً من 'downloads/'
        temp_dir = tempfile.gettempdir()
        
        ydl_opts = {
            'format': format if type == 'video' else 'bestaudio/best',
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        }
        
        # تحذير: FFmpeg قد لا يعمل على Vercel بدون Static Build
        # إذا واجهت خطأ FFmpeg، ستحتاج لإزالة التحويل (Postprocessors)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        return FileResponse(path=filename, media_type='application/octet-stream', filename=os.path.basename(filename))
        
    except Exception as e:
        return {"error": f"خطأ في التحميل: {str(e)}"}

        # اجعل تشغيل uvicorn محصوراً فقط عند التشغيل المحلي
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)