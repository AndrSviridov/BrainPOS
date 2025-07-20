import logging
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
from smart_pos_agent.core.diagnostics import get_diagnostics_summary

def launch_ui():
    logging.debug("Launching GUI assistant...")
    try:
        root = tk.Tk()
        root.title("Помощник кассира")
        root.geometry("300x250")

        tk.Label(root, text="Что вы хотите сделать?").pack(pady=10)

        def handle_ai():
            try:
                path = os.path.join(os.getcwd(), "ai_cashier_gui_with_metrics_1902.py")
                subprocess.Popen(["python", path])
            except Exception as e:
                logging.error(f"Не удалось запустить ИИ-интерфейс: {e}")
                messagebox.showerror("Ошибка", f"Не удалось запустить ИИ-интерфейс:\n{e}")

        tk.Button(root, text="Спросить ИИ", command=handle_ai, width=25).pack(pady=5)
        tk.Button(root, text="Проблема с принтером", command=lambda: messagebox.showinfo("Сообщение", "Проверьте кабель и питание принтера"), width=25).pack(pady=5)
        tk.Button(root, text="Медленно работает", command=lambda: messagebox.showinfo("Диагностика", get_diagnostics_summary()), width=25).pack(pady=5)

        root.mainloop()
        logging.info("GUI assistant launched successfully.")
    except Exception as e:
        logging.exception("Failed to launch GUI assistant: %s", e)
