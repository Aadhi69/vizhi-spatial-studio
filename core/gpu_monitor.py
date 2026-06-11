import os
import sys
import platform
import winreg
import ctypes
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

# Structure for GlobalMemoryStatusEx
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_cpu_name():
    """Returns the clean CPU name on Windows, falling back to platform.processor()"""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        return name.strip()
    except Exception:
        return platform.processor() or "Generic CPU"

def get_ram_info():
    """Returns (total_gb, used_gb, percent_used) using ctypes GlobalMemoryStatusEx"""
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_ram = stat.ullTotalPhys / (1024**3)
        free_ram = stat.ullAvailPhys / (1024**3)
        used_ram = total_ram - free_ram
        percent = stat.dwMemoryLoad
        return total_ram, used_ram, percent
    except Exception:
        # Fallback to standard platform checks or fixed value
        return 16.0, 4.0, 25.0

def get_cuda_version():
    """Retrieves system CUDA version dynamically"""
    # 1. Try env variable
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        ver = os.path.basename(cuda_path)
        if ver.startswith("v"):
            return ver[1:]
            
    # 2. Try nvcc --version
    try:
        out = subprocess.check_output("nvcc --version", shell=True, stderr=subprocess.STDOUT, text=True)
        for line in out.splitlines():
            if "release" in line:
                parts = line.split("release")[-1].strip().split(",")
                if parts:
                    return parts[0].strip()
    except Exception:
        pass
        
    # 3. Fallback to torch's CUDA version
    try:
        import torch
        if torch.cuda.is_available():
            return torch.version.cuda
    except Exception:
        pass
        
    return "N/A"

def get_os_version():
    """Retrieves clean OS name (e.g. Windows 11 Pro)"""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        product_name, _ = winreg.QueryValueEx(key, "ProductName")
        
        display_version = ""
        try:
            display_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
        except Exception:
            pass
            
        build_number = 0
        try:
            build_str, _ = winreg.QueryValueEx(key, "CurrentBuild")
            build_number = int(build_str)
        except Exception:
            pass
            
        winreg.CloseKey(key)
        
        # Fix Windows 10 name if it actually is Windows 11
        if "Windows 10" in product_name and build_number >= 22000:
            product_name = product_name.replace("Windows 10", "Windows 11")
            
        if display_version:
            return f"{product_name} {display_version}"
        return product_name
    except Exception:
        return f"{platform.system()} {platform.release()}"

def get_gpu_info():
    """Retrieves list of GPU details. Returns at least one GPU dict representation."""
    gpus_list = []
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for g in gpus:
            gpus_list.append({
                "name": g.name,
                "load": g.load * 100.0,
                "vram_total": g.memoryTotal / 1024.0, # GB
                "vram_used": g.memoryUsed / 1024.0,   # GB
                "vram_free": g.memoryFree / 1024.0    # GB
            })
    except Exception:
        pass
        
    if not gpus_list:
        try:
            import torch
            if torch.cuda.is_available():
                for idx in range(torch.cuda.device_count()):
                    name = torch.cuda.get_device_name(idx)
                    properties = torch.cuda.get_device_properties(idx)
                    total_mem = properties.total_memory / (1024**3)
                    allocated_mem = torch.cuda.memory_allocated(idx) / (1024**3)
                    gpus_list.append({
                        "name": name,
                        "load": 0.0,
                        "vram_total": total_mem,
                        "vram_used": allocated_mem,
                        "vram_free": total_mem - allocated_mem
                    })
        except Exception:
            pass
            
    if not gpus_list:
        gpus_list.append({
            "name": "Intel/AMD Integrated Graphics",
            "load": 0.0,
            "vram_total": 0.0,
            "vram_used": 0.0,
            "vram_free": 0.0
        })
        
    return gpus_list


class GPUMonitorThread(QThread):
    """Periodically queries hardware telemetry and emits updates"""
    telemetry_updated = pyqtSignal(dict)

    def __init__(self, interval_ms=1500, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.running = True

    def run(self):
        import time
        while self.running:
            try:
                gpus = get_gpu_info()
                gpu = gpus[0]
                ram_total, ram_used, ram_pct = get_ram_info()
                
                # We can construct a telemetry payload
                payload = {
                    "gpu_name": gpu["name"],
                    "gpu_load": gpu["load"],
                    "vram_total": gpu["vram_total"],
                    "vram_used": gpu["vram_used"],
                    "ram_total": ram_total,
                    "ram_used": ram_used,
                    "ram_pct": ram_pct
                }
                self.telemetry_updated.emit(payload)
            except Exception as e:
                print(f"Error in GPUMonitorThread: {e}")
            
            time.sleep(self.interval_ms / 1000.0)

    def stop(self):
        self.running = False
        self.wait()
