import os
import subprocess
import time

class MediaMTXManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MediaMTXManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.process = None
        return cls._instance
        
    def start(self):
        if self.process:
            return True
            
        mediamtx_dir = r"D:\vizhi-spatial-software\tools\mediamtx"
        mediamtx_exe = os.path.join(mediamtx_dir, "mediamtx.exe")
        
        if not os.path.exists(mediamtx_exe):
            print("MediaMTX server binary not found.")
            return False
            
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(
                [mediamtx_exe],
                cwd=mediamtx_dir,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)  # Allow port binding
            return True
        except Exception as e:
            print(f"Failed to start MediaMTX process: {e}")
            return False
            
    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
            
    def restart(self):
        self.stop()
        return self.start()
