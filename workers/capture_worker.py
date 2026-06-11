import os
import cv2
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

class CaptureWorker(QThread):
    frame_captured = pyqtSignal(QPixmap, str)  # scaled pixmap for UI, filepath if saved
    status_msg = pyqtSignal(str)              # status updates
    finished = pyqtSignal()
    
    def __init__(self, rtsp_url, output_dir, save_interval=5, parent=None):
        super().__init__(parent)
        self.rtsp_url = rtsp_url
        self.output_dir = output_dir
        self.save_interval = save_interval
        self.running = True
        
    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        self.status_msg.emit(f"Connecting to RTSP stream: {self.rtsp_url}")
        
        # Determine starting index from existing images in datasets/<project>/images/
        try:
            existing = [f for f in os.listdir(self.output_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            frame_idx = len(existing)
        except Exception:
            frame_idx = 0
            
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        cap = cv2.VideoCapture(self.rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            self.status_msg.emit(f"Error: Failed to connect to stream {self.rtsp_url}")
            self.finished.emit()
            return
            
        self.status_msg.emit("RTSP stream connected successfully.")
        
        frame_count = 0
        while self.running:
            ret, frame = cap.read()
            if not ret:
                self.status_msg.emit("Warning: Frame drop or stream disconnected.")
                time.sleep(0.1)
                continue
                
            frame_count += 1
            
            # Convert OpenCV frame to QPixmap
            height, width, channel = frame.shape
            bytesPerLine = 3 * width
            # OpenCV captures BGR, convert to RGB for QImage
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qImg = QImage(rgb_frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg)
            
            saved_path = ""
            if frame_count % self.save_interval == 0:
                frame_idx += 1
                filename = f"{frame_idx:05d}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                try:
                    cv2.imwrite(filepath, frame)
                    saved_path = filepath
                except Exception as e:
                    self.status_msg.emit(f"Failed to save frame: {e}")
                
            self.frame_captured.emit(pixmap, saved_path)
            
            pass
            
        cap.release()
        self.status_msg.emit("Capture process terminated.")
        self.finished.emit()
        
    def stop(self):
        self.running = False
        self.wait()
