import importlib
import os
import sys
from pathlib import Path

print("🛠 Тест запуска smart_pos_agent\n")

# Добавляем smart_pos_agent в путь
sys.path.insert(0, str(Path(__file__).parent / "smart_pos_agent"))

# Блок 1: Проверка импорта модулей
print("[1] Импорт модулей:")
modules = ["core.diagnostics", "core.monitor", "gui.assistant_ui"]
for module in modules:
    try:
        importlib.import_module(module)
        print(f"  ✅ {module} — OK")
    except Exception as e:
        print(f"  ❌ {module} — ошибка импорта: {e}")
print("\n[4] Проверка smart_monitor.py:")
try:
    from core import smart_monitor
    if Path("smart_latest.txt").exists():
        print("  ✅ smart_latest.txt найден")
    else:
        print("  ❌ smart_latest.txt отсутствует")
    print("  ✅ smart_monitor импортирован")
except Exception as e:
    print(f"  ❌ Ошибка smart_monitor: {e}")

# Блок 2: Диагностика системы
print("\n[2] Диагностика системы:")
try:
    from core.diagnostics import get_diagnostics_summary
    print(get_diagnostics_summary())
except Exception as e:
    print(f"  ❌ Ошибка диагностики: {e}")

# Блок 3: Проверка конфигурации модели
print("\n[3] Проверка конфигурации LLM:")
try:
    import json
    config_path = Path("ai_assistant_config.json")
    if not config_path.exists():
        print("  ❌ Конфигурационный файл ai_assistant_config.json не найден.")
    else:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        llama_path = Path(config.get("llama_run_path", ""))
        model_path = Path(config.get("model_path", ""))
        if llama_path.exists():
            print(f"  ✅ llama-run: {llama_path}")
        else:
            print(f"  ❌ llama-run не найден по пути: {llama_path}")
        if model_path.exists():
            print(f"  ✅ Модель GGUF: {model_path}")
        else:
            print(f"  ❌ Модель GGUF не найдена по пути: {model_path}")
        if llama_path.exists() and model_path.exists():
            print("  ✅ Конфигурация модели выглядит корректной.")
except Exception as e:
    print(f"  ❌ Ошибка проверки конфигурации: {e}")

print("\n✅ Тестирование завершено.")