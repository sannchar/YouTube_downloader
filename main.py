import customtkinter as ctk
import os
import shutil
import threading

# Lazy import yt_dlp to make app open fast
# import yt_dlp

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("YouTube Downloader")
        self.geometry("500x320")
        self.resizable(False, False)
        
        # Windows taskbar icon fix when running directly via Python
        try:
            import ctypes
            myappid = 'sannchar.youtubedownloader.1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
        
        # Set Icon
        try:
            import sys
            
            # Support PyInstaller path resolution
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print("Could not load icon:", e)
        
        # Configure appearance
        ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create a frame
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Title Label
        self.title_label = ctk.CTkLabel(self.frame, text="YouTube Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(self.frame, placeholder_text="Paste YouTube URL here...", width=350)
        self.url_entry.grid(row=1, column=0, padx=20, pady=10)
        
        # Format Selection
        self.format_var = ctk.StringVar(value="video")
        self.radio_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.radio_frame.grid(row=2, column=0, padx=20, pady=10)
        
        self.radio_video = ctk.CTkRadioButton(self.radio_frame, text="Video (MP4)", variable=self.format_var, value="video")
        self.radio_video.grid(row=0, column=0, padx=20)
        
        self.radio_audio = ctk.CTkRadioButton(self.radio_frame, text="Audio (MP3)", variable=self.format_var, value="audio")
        self.radio_audio.grid(row=0, column=1, padx=20)
        
        # Download Button
        self.download_button = ctk.CTkButton(self.frame, text="Download", command=self.start_download, font=ctk.CTkFont(weight="bold"))
        self.download_button.grid(row=3, column=0, padx=20, pady=15)
        
        # Status Label
        self.status_label = ctk.CTkLabel(self.frame, text="Ready", text_color="gray")
        self.status_label.grid(row=4, column=0, padx=20, pady=(0, 20))
        
    def check_ffmpeg(self):
        """Check if FFmpeg is installed and accessible in the system PATH."""
        return shutil.which('ffmpeg') is not None
        
    def start_download(self):
        url = self.url_entry.get().strip()
        format_choice = self.format_var.get()
        
        if not url:
            self.status_label.configure(text="Error: Please enter a YouTube URL", text_color="#ff5555")
            return
            
        if format_choice == "audio" and not self.check_ffmpeg():
            self.status_label.configure(text="Error: FFmpeg is missing. Required for MP3 format.", text_color="#ff5555")
            return
            
        self.status_label.configure(text="Starting download...", text_color="#ffff55")
        self.download_button.configure(state="disabled")
        
        # Run download in a separate thread to keep UI responsive
        threading.Thread(target=self.download_thread, args=(url, format_choice), daemon=True).start()
        
    def download_thread(self, url, format_choice):
        try:
            # Lazy import to ensure the app starts up very fast
            import yt_dlp
            
            downloads_dir = os.path.join(os.getcwd(), 'Downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Helper function for progress hook
            def my_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', 'N/A').strip()
                    speed_str = d.get('_speed_str', 'N/A').strip()
                    eta_str = d.get('_eta_str', 'N/A').strip()
                    
                    # Remove ANSI escape codes from yt-dlp output
                    import re
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', percent_str)
                    
                    self.update_status(f"Downloading: {percent_str} (ETA: {eta_str})", "#55ffff")
                elif d['status'] == 'finished':
                    self.update_status("Download finished, processing...", "#ffff55")
            
            ydl_opts = {
                'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
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
                
            self.update_status("Download Complete!", "#55ff55")
            
        except ImportError:
            self.update_status("Error: yt-dlp is not installed.", "#ff5555")
        except Exception as e:
            error_msg = str(e)
            # Shorten the error message if it's too long
            if len(error_msg) > 60:
                error_msg = error_msg[:57] + "..."
            self.update_status(f"Error: {error_msg}", "#ff5555")
        finally:
            self.enable_button()
            
    def update_status(self, text, color):
        # Update the UI thread-safely via after
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))
        
    def enable_button(self):
        self.after(0, lambda: self.download_button.configure(state="normal"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
