import webview
import os
import shutil
import threading

class Api:
    def __init__(self):
        self.downloads_dir = os.path.join(os.getcwd(), 'Downloads')
        os.makedirs(self.downloads_dir, exist_ok=True)
        self.window = None

    def check_ffmpeg(self):
        return shutil.which('ffmpeg') is not None

    def get_downloads_dir(self):
        return self.downloads_dir

    def open_dir(self):
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir, exist_ok=True)
        os.startfile(self.downloads_dir)

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/sannchar/YouTube_downloader")

    def change_dir(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            new_dir = filedialog.askdirectory(initialdir=self.downloads_dir, title="Select Download Folder")
            root.destroy()
            if new_dir:
                self.downloads_dir = new_dir
            return self.downloads_dir
        except Exception as e:
            return self.downloads_dir

    def log(self, message):
        if self.window:
            safe_message = str(message).replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
            self.window.evaluate_js(f"window.addLogMessage('{safe_message}');")

    def start_download(self, url, format_choice):
        if not url:
            self.log("ERROR: NO_URL_PROVIDED")
            if self.window:
                self.window.evaluate_js("window.downloadComplete();")
            return
            
        if format_choice == "audio" and not self.check_ffmpeg():
            self.log("ERROR: FFMPEG_MISSING. REQUIRED FOR MP3.")
            if self.window:
                self.window.evaluate_js("window.downloadComplete();")
            return
            
        self.log(f"INITIATING DOWNLOAD_SEQUENCE_FOR: {url}")
        threading.Thread(target=self.download_thread, args=(url, format_choice), daemon=True).start()

    def download_thread(self, url, format_choice):
        try:
            import yt_dlp
            
            def my_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', 'N/A').strip()
                    speed_str = d.get('_speed_str', 'N/A').strip()
                    eta_str = d.get('_eta_str', 'N/A').strip()
                    
                    import re
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', percent_str)
                    
                    self.log(f"DOWNLOADING... {percent_str} (ETA: {eta_str})")
                    if self.window:
                        try:
                            clean_percent = percent_str.replace('%', '').strip()
                            self.window.evaluate_js(f"window.updateProgress({clean_percent});")
                        except:
                            pass
                            
                elif d['status'] == 'finished':
                    self.log("DOWNLOAD_FINISHED_PROCESSING...")
            
            ydl_opts = {
                'outtmpl': os.path.join(self.downloads_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [my_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            if format_choice == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                })
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self.log("SEQUENCE_COMPLETE")
            if self.window:
                self.window.evaluate_js("window.updateProgress(100); window.downloadComplete();")
            
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 60:
                error_msg = error_msg[:57] + "..."
            self.log(f"ERROR: {error_msg}")
            if self.window:
                self.window.evaluate_js("window.downloadComplete();")

if __name__ == '__main__':
    import sys
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, 'web', 'index.html')
    
    api = Api()
    
    window = webview.create_window(
        'YTdownload', 
        url=html_path,
        js_api=api,
        width=1000, 
        height=700,
        resizable=True,
        min_size=(800, 600)
    )
    api.window = window
    webview.start()
