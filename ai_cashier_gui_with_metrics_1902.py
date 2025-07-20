...
import customtkinter as ctk
from tkinter import filedialog, StringVar, BooleanVar, IntVar, Toplevel
import subprocess
import os
import json
from pathlib import Path
import threading
import time
import psutil
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = str(BASE_DIR / "ai_assistant_config.json")
LOG_FILE = str(BASE_DIR / "llama_output.log")
METRICS_LOG_FILE = str(BASE_DIR / "metrics_log.txt")

def load_config():
    default_config = {
        "llama_path": "C:/AI/llama/llama-run.exe",
        "model_path": "C:/AI/models/SambaLingo-Russian-Chat.Q4_K_M.gguf"
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

ROLE_PROMPTS = {
    "Кассир": "Ты кассовый помощник. Отвечай кратко и понятно.",
    "Администратор": "Ты помощник администратора ресторана. Отвечай точно и профессионально.",
    "Техник": "Ты помощник по техническим вопросам. Помогай решать проблемы с оборудованием и ПО.",
    "Разработчик": "Ты помощник разработчика ПО. Объясняй внутренние функции и логику систем.",
    "Официант": "Ты помощник официанта. Отвечай вежливо и понятно по вопросам обслуживания гостей.",
    "Без шаблона": ""
}

class AIAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ИИ-помощник (обновлённый ввод в UTF-8)")
        self.geometry("840x600")

        self.role_var = StringVar(value="Кассир")
        self.save_to_file = BooleanVar(value=True)
        self.timeout = IntVar(value=60)

        self.label = ctk.CTkLabel(self, text="Введите вопрос:", font=("Arial", 16))
        self.label.pack(pady=(15, 8))

        self.role_menu = ctk.CTkOptionMenu(self, values=list(ROLE_PROMPTS.keys()), variable=self.role_var)
        self.role_menu.pack(pady=5)

        self.entry = ctk.CTkEntry(self, width=700, font=("Arial", 14))
        self.entry.pack(pady=10)
        self.entry.bind("<Control-v>", self.paste_from_clipboard)

        self.ask_button = ctk.CTkButton(self, text="Спросить", command=self.ask_ai_thread)
        self.ask_button.pack(pady=8)

        self.output = ctk.CTkTextbox(self, width=760, height=160, font=("Consolas", 12), wrap="word")
        self.output.pack(pady=(8, 0))
        self.copy_button = ctk.CTkButton(self, text="Копировать ответ", command=self.copy_full_output)
        self.copy_button.pack(pady=(4, 8))
        self.output.insert("0.0", "Ответ появится здесь...\n")
        self.output.bind("<Control-c>", self.copy_to_clipboard)

        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.set(0)
        self.progress.pack(pady=(0, 10))

        self.timeout_slider = ctk.CTkSlider(self, from_=15, to=180, number_of_steps=33, variable=self.timeout, command=self.update_timeout_label)
        self.timeout_slider.pack()
        self.timeout_label = ctk.CTkLabel(self, text="Таймаут: 60 секунд")
        self.timeout_label.pack()

        self.save_checkbox = ctk.CTkCheckBox(self, text="Сохранять в файл", variable=self.save_to_file)
        self.save_checkbox.pack(pady=(8, 10))

        self.model_btn = ctk.CTkButton(self, text="Выбрать модель (.gguf)", command=self.select_model)
        self.model_btn.pack(pady=(5, 0))

        self.llama_btn = ctk.CTkButton(self, text="Выбрать llama-run.exe", command=self.select_llama)
        self.llama_btn.pack(pady=(5, 10))

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(10, 10))
        self.history_button = ctk.CTkButton(button_frame, text="Показать историю", command=self.show_history)
        self.metrics_button = ctk.CTkButton(button_frame, text="Показать метрики", command=self.show_metrics)
        self.history_button.pack(side="left", padx=10)
        self.metrics_button.pack(side="left", padx=10)

        self.config_label = ctk.CTkLabel(self, text=self.get_config_text(), font=("Arial", 10), wraplength=700, justify="center")
        self.config_label.pack()

    def update_timeout_label(self, value):
        self.timeout_label.configure(text=f"Таймаут: {int(float(value))} секунд")

    def get_config_text(self):
        return f"Модель: {config['model_path']} | llama-run: {config['llama_path']}"

    def select_model(self):
        path = filedialog.askopenfilename(filetypes=[("GGUF Models", "*.gguf")])
        if path:
            config["model_path"] = path
            save_config(config)
            self.config_label.configure(text=self.get_config_text())

    def select_llama(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            config["llama_path"] = path
            save_config(config)
            self.config_label.configure(text=self.get_config_text())

    def build_prompt(self, question, role):
        system_text = ROLE_PROMPTS.get(role, "")
        return f"<|system|>{system_text}<|user|>{question}<|assistant|>" if system_text else question

    def ask_ai_thread(self):
        self.progress.set(0.1)
        threading.Thread(target=self.ask_ai).start()

    def paste_from_clipboard(self, event=None):
        try:
            self.entry.insert("insert", self.clipboard_get())
        except Exception as e:
            self.output.insert("0.0", f"Ошибка вставки из буфера: {e}")

    def ask_ai(self):
        question = self.entry.get().strip()
        if not question:
            self.output.delete("0.0", "end")
            self.output.insert("0.0", "Введите вопрос, пожалуйста.")
            return

        prompt = self.build_prompt(question, self.role_var.get())
        self.output.delete("0.0", "end")
        self.output.insert("0.0", "Ждём ответ от модели...\n")
        self.progress.set(0.3)

        try:
            start_time = time.time()
            memory_usage = 0.0
            if self.save_to_file.get():
                with open(LOG_FILE, "wb") as f:
                    pass
                log_file = open(LOG_FILE, "ab")
                process = subprocess.Popen(
                    [config["llama_path"], "--threads", "4", "--context-size", "2048", config["model_path"]],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=log_file
                )
            else:
                process = subprocess.Popen(
                    [config["llama_path"], "--threads", "4", "--context-size", "2048", config["model_path"]],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            input_text = ('\ufeff' + prompt + ' ')
            try:
                memory_usage = psutil.Process(process.pid).memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
                memory_usage = 0.0

            stdout, stderr = process.communicate(input=input_text.encode("utf-8"), timeout=self.timeout.get())
            end_time = time.time()
            duration = end_time - start_time

            output = stdout.decode("utf-8", errors="replace").replace('\x1b[0m', '').replace('\x1b[K', '').strip() if stdout else ""

            if not output and os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                        file_output = f.read()
                        cleaned_output = file_output.replace('\x1b[0m', '').replace('\x1b[K', '').strip()
                        if file_output.rstrip().endswith('\x1b[0m'):
                            output = cleaned_output
                        else:
                            output = cleaned_output + "\nℹ️ Ответ получен из лога, т.к. модель завершилась преждевременно."
                except Exception as e:
                    output = f"Ошибка при чтении лога: {e}"

            self.progress.set(1.0)
            self.output.delete("0.0", "end")
            self.output.insert("0.0", output)

        except Exception as e:
            self.output.delete("0.0", "end")
            self.output.insert("0.0", f"Ошибка выполнения: {e}")
        finally:
            try:
                end_time = time.time()
                duration = end_time - start_time
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session_id = str(int(time.time() * 1000))
                with open(METRICS_LOG_FILE, "a", encoding="utf-8") as log:
                    log.write(f"Дата и время: {timestamp}\n")
                    log.write(f"ID сессии: {session_id}\n")
                    log.write(f"Модель: {config['model_path']}\n")
                    log.write(f"Роль: {self.role_var.get()}\n")
                    log.write(f"Вопрос: {question}\n")
                    log.write(f"Время ответа: {duration:.2f} сек\n")
                    log.write(f"Память: {memory_usage:.2f} МБ\n")
                    log.write("-" * 40 + "\n")
            except Exception as log_err:
                self.output.insert("0.0", f"Ошибка сохранения метрик: {log_err}\n")

    def show_metrics(self):
        try:
            if os.path.exists(METRICS_LOG_FILE):
                top = Toplevel(self)
                top.title("Метрики")
                top.geometry("720x400")
                textbox = ctk.CTkTextbox(top, wrap="word", font=("Consolas", 11))
                textbox.pack(expand=True, fill="both")
                with open(METRICS_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    textbox.insert("1.0", f.read())
        except Exception as e:
            self.output.delete("0.0", "end")
            self.output.insert("0.0", f"Ошибка показа метрик: {e}")

    def show_history(self):
        try:
            if os.path.exists(LOG_FILE):
                top = Toplevel(self)
                top.title("История из файла llama_output.log")
                top.geometry("720x400")
                textbox = ctk.CTkTextbox(top, wrap="word", font=("Consolas", 11))
                textbox.pack(expand=True, fill="both")
                with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    textbox.insert("1.0", f.read())
        except Exception as e:
            self.output.delete("0.0", "end")
            self.output.insert("0.0", f"Ошибка показа истории: {e}")

    def copy_full_output(self):
        try:
            full_text = self.output.get("1.0", "end").strip()
            self.clipboard_clear()
            self.clipboard_append(full_text)
        except Exception as e:
            self.output.insert("0.0", f"Ошибка копирования всего ответа: {e}")

    def copy_to_clipboard(self, event=None):
        try:
            selection = self.output.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(selection)
        except Exception as e:
            self.output.insert("0.0", f"Ошибка копирования: {e}")

if __name__ == "__main__":
    app = AIAssistantApp()
    app.mainloop()

