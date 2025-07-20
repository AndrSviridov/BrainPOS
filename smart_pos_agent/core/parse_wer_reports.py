import os
import csv
import re
import logging
from datetime import datetime

logging.basicConfig(filename="wer_parser.log", level=logging.INFO, format="%(asctime)s - %(message)s")

WER_DIRS = [
    r"C:\ProgramData\Microsoft\Windows\WER\ReportQueue",
    r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive"
]

CSV_PATH = "wer_diagnostics.csv"
FIELDS = ["Report ID", "Date", "Application Name", "Fault Module Name", "Exception Code", "Path"]

summary = {}

def parse_wer_file(path):
    result = {f: "" for f in FIELDS}
    result["Path"] = path

    # Определение кодировки
    encodings = ["utf-16", "utf-8", "cp1251"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                lines = f.readlines()
            break
        except Exception:
            continue
    else:
        logging.warning(f"{path}: не удалось прочитать")
        return None

    for line in lines:
        for field in FIELDS[:-1]:
            if line.lower().startswith(field.lower()):
                sep = "=" if "=" in line else ":"
                val = line.split(sep, 1)[-1].strip()
                result[field] = val

    # Фильтрация: должна быть Application Name и хотя бы Exception или Fault Module
    if result["Application Name"] and (result["Exception Code"] or result["Fault Module Name"]):
        return result
    else:
        return None

def collect_wer_reports():
    records = []
    for wer_dir in WER_DIRS:
        if not os.path.exists(wer_dir):
            continue
        for root, _, files in os.walk(wer_dir):
            for file in files:
                if file.endswith(".wer"):
                    full_path = os.path.join(root, file)
                    record = parse_wer_file(full_path)
                    if record:
                        app = record["Application Name"]
                        summary.setdefault(app, []).append(record)
                        records.append(record)

    # CSV вывод
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    # Сводка в лог
    logging.info("📊 Сводка по сбоям EXE (WER):")
    for app, items in summary.items():
        modules = set(i["Fault Module Name"] for i in items if i["Fault Module Name"])
        logging.info(f"{app:25} — {len(items)} сб., модули: {', '.join(modules)}")

if __name__ == "__main__":
    collect_wer_reports()
