import os
import csv
import logging
import datetime
import win32evtlog
from collections import defaultdict

# Лог для ошибок
logging.basicConfig(
    filename="agent.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# CSV для детального разбора
CSV_PATH = "eventlog_crashes.csv"
SUMMARY_LOG = "eventlog_summary.log"
summary_logger = logging.getLogger("summary_logger")
summary_logger.setLevel(logging.INFO)
fh = logging.FileHandler(SUMMARY_LOG, mode="w", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(message)s"))
summary_logger.addHandler(fh)

EVENT_FILTER = {
    "System": {
        41: "Неправильное выключение",
        6008: "Неожиданный перезапуск",
        9: "Ошибка контроллера диска",
        11: "Ошибка чтения/записи диска",
        13: "Ошибка контроллера SCSI",
        15: "Контроллер недоступен",
        51: "Delayed Write Failed",
        129: "Таймаут устройства"
    },
    "Application": {
        1000: "Сбой приложения",
        1001: "Отчёт об ошибке"
    },
    "HardwareEvents": {
        1: "Аппаратная ошибка",
        2: "Критическая ошибка оборудования"
    }
}

def extract_exe(event):
    """Находит .exe в StringInserts или возвращает SourceName"""
    if event.StringInserts:
        for s in event.StringInserts:
            if ".exe" in s.lower():
                return os.path.basename(s.strip())
    return event.SourceName or "неизвестно"

def analyze_event_logs(hours_back=48):
    now = datetime.datetime.now()
    since = now - datetime.timedelta(hours=hours_back)
    crash_summary = defaultdict(lambda: {"count": 0, "first": None, "last": None})

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time", "Log", "EventID", "Type", "EXE", "Source", "Inserts"])

        for log_type, event_ids in EVENT_FILTER.items():
            try:
                hand = win32evtlog.OpenEventLog(None, log_type)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

                while True:
                    try:
                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                    except Exception as e:
                        logging.error(f"{log_type}: ошибка чтения — {e}")
                        break
                    if not events: break

                    for ev in events:
                        if ev.EventID in event_ids and ev.TimeGenerated >= since:
                            ts = ev.TimeGenerated
                            evt_type = EVENT_FILTER[log_type][ev.EventID]
                            exe = extract_exe(ev)
                            source = ev.SourceName
                            crash_summary[exe]["count"] += 1
                            crash_summary[exe]["first"] = crash_summary[exe]["first"] or ts
                            crash_summary[exe]["last"] = ts
                            inserts = "; ".join(ev.StringInserts) if ev.StringInserts else "-"
                            writer.writerow([ts, log_type, ev.EventID, evt_type, exe, source, inserts])

            except Exception as e:
                logging.error(f"{log_type}: не удалось открыть журнал — {e}")

    # Сводка
    summary_logger.info(f"СВОДКА по EXE-падениям за последние {hours_back} ч:")
    summary_logger.info(f"{'EXE':30} | {'COUNT':>5} | {'ПЕРВОЕ':19} | {'ПОСЛЕДНЕЕ':19}")
    summary_logger.info("-" * 80)
    for exe, info in sorted(crash_summary.items(), key=lambda x: -x[1]["count"]):
        summary_logger.info(
            f"{exe:30} | {info['count']:5d} | {info['first']:%Y-%m-%d %H:%M:%S} | {info['last']:%Y-%m-%d %H:%M:%S}"
        )

if __name__ == "__main__":
    analyze_event_logs()
