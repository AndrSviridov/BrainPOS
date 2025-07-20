"""
Smart POS Agent (pybox): чтение SMART-отчёта из лога
- Без прав администратора
- Поддерживает парсинг всех ключевых атрибутов
- Совместим с дампом от smartctl /dev/sdX
"""

import os
import json
import time
from datetime import datetime, timezone

LOG_PATH = "C:/AI/SmartPos/logs/storage_monitor.json"
DEBUG_LOG_PATH = "C:/AI/SmartPos/logs/logs/agent_debug.log"
SMART_DUMP_PATH = "C:/AI/SmartPos/logs/smart_latest.txt"

# --- THRESHOLDS ---
CRIT_TEMP = 70
CRIT_REALLOC = 1
CRIT_UNSAFE = 10
CRIT_WEAR = 10

# --- LOGGING ---
def log_event(event):
    timestamp = datetime.now(timezone.utc).isoformat()
    event['timestamp'] = timestamp
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)

    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
        prefix = f"[{timestamp}] {event.get('level','INFO').upper()}: {event.get('type','?')} - "
        f.write(prefix + event.get('message','') + "\n")

# --- SMART PARSE ---
def parse_smart():
    if not os.path.exists(SMART_DUMP_PATH):
        log_event({"type": "smart_log_missing", "level": "error", "message": "Файл smart_latest.txt не найден"})
        return

    try:
        with open(SMART_DUMP_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 10:
                continue
            attr = parts[0].strip()
            raw = parts[9].strip()

            try:
                val = int(raw.split()[0]) if raw.split() else 0

                if attr == '5' and val >= CRIT_REALLOC:
                    log_event({"type": "smart_realloc", "level": "warning", "message": f"Reallocated sectors: {val}"})

                elif attr == '192' and val >= CRIT_UNSAFE:
                    log_event({"type": "smart_unsafe_shutdowns", "level": "warning", "message": f"Unsafe shutdowns: {val}"})

                elif attr in ('231', '233') and val <= CRIT_WEAR:
                    log_event({"type": "smart_wear", "level": "warning", "message": f"Оставшийся ресурс SSD: {val}%"})

                elif attr == '194' and val >= CRIT_TEMP:
                    log_event({"type": "smart_temp", "level": "warning", "message": f"Температура: {val}°C"})

                elif attr == '9':
                    log_event({"type": "smart_uptime", "level": "info", "message": f"Наработка: {val} ч"})

            except Exception as e:
                log_event({"type": "smart_line_parse_error", "level": "error", "message": str(e)})

    except Exception as e:
        log_event({"type": "smart_file_read_error", "level": "error", "message": str(e)})

# --- MAIN LOOP ---
def monitor_loop(interval_sec=600):
    while True:
        try:
            parse_smart()
        except Exception as e:
            log_event({"type": "agent_error", "level": "error", "message": str(e)})
        time.sleep(interval_sec)

if __name__ == '__main__':
    monitor_loop(600)
