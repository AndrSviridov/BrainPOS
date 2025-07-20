import platform
import ctypes
import time
import psutil
import logging

try:
    import winreg
    REG_AVAILABLE = True
except ImportError:
    REG_AVAILABLE = False

logging.basicConfig(filename='logs/debug_agent.log', level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_ulong),
                ("dwHighDateTime", ctypes.c_ulong)]

def filetime_to_int(filetime):
    return (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime

def get_cpu_usage_win32(interval=1.0):
    idle_time, kernel_time, user_time = FILETIME(), FILETIME(), FILETIME()
    if not hasattr(ctypes, 'windll'):
        raise EnvironmentError("ctypes.windll is not available (not Windows)")
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle_time),
                                          ctypes.byref(kernel_time),
                                          ctypes.byref(user_time))
    idle_1 = filetime_to_int(idle_time)
    kernel_1 = filetime_to_int(kernel_time)
    user_1 = filetime_to_int(user_time)

    time.sleep(interval)

    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle_time),
                                          ctypes.byref(kernel_time),
                                          ctypes.byref(user_time))
    idle_2 = filetime_to_int(idle_time)
    kernel_2 = filetime_to_int(kernel_time)
    user_2 = filetime_to_int(user_time)

    idle_delta = idle_2 - idle_1
    total_delta = (kernel_2 + user_2) - (kernel_1 + user_1)

    if total_delta == 0:
        return 0.0
    usage = 100.0 * (1.0 - (idle_delta / total_delta))
    return round(usage, 1)

def get_os_edition():
    edition = ""
    try:
        if REG_AVAILABLE:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            edition = product_name
            version = platform.version()
            try:
                build_number = int(version.split('.')[2])
                if build_number >= 22000:
                    edition = edition.replace("Windows 10", "Windows 11")
            except Exception:
                pass
    except Exception as e:
        logging.warning(f"OS edition detection failed: {e}")
    return edition

def get_diagnostics_summary():
    os_name = platform.system()
    os_version = platform.version()
    os_build = platform.release()
    source = "win32api"
    try:
        cpu_usage = get_cpu_usage_win32()
    except Exception as e:
        logging.warning(f"⚠ Win32 API недоступен: {e}")
        cpu_usage = psutil.cpu_percent(interval=1)
        source = "psutil"

    edition = get_os_edition()
    os_full = f"OS: {os_name}, Build: {os_version} ({edition})" if edition else f"OS: {os_name}, Build: {os_version} ({os_build})"
    return f"{os_full}\nCPU Usage: {cpu_usage}%, Source: {source}, Temperature: N/A"

if __name__ == '__main__':
    print(get_diagnostics_summary())