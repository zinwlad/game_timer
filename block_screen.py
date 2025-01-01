import tkinter as tk
from tkinter import messagebox
import time
from datetime import datetime, timedelta

class BlockScreen:
    def __init__(self, root, password):
        self.root = root
        self.password = password
        self.block_window = tk.Toplevel(self.root)
        self.block_window.attributes('-fullscreen', True)
        self.block_window.configure(bg='black')
        self.unblock_time = datetime.now() + timedelta(minutes=30)
        self.update_timer_id = None
        self.create_widgets()
        self.update_timer()

    def create_widgets(self):
        message_label = tk.Label(
            self.block_window,
            text="Игра заблокирована",
            font=("Arial", 36),
            fg="white",
            bg="black"
        )
        message_label.pack(expand=True)

        self.timer_label = tk.Label(
            self.block_window,
            text="30:00",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        self.timer_label.pack()

        info_label = tk.Label(
            self.block_window,
            text="Блокировка автоматически снимется через 30 минут\nили введите пароль для досрочной разблокировки:",
            font=("Arial", 16),
            fg="white",
            bg="black",
            justify=tk.CENTER
        )
        info_label.pack(pady=20)

        self.password_entry = tk.Entry(
            self.block_window,
            font=("Arial", 24),
            show="*"
        )
        self.password_entry.pack()

        unlock_button = tk.Button(
            self.block_window,
            text="Разблокировать",
            font=("Arial", 18),
            command=self.try_unlock
        )
        unlock_button.pack(pady=20)

    def update_timer(self):
        """Обновляет таймер и проверяет время для автоматической разблокировки"""
        now = datetime.now()
        if now >= self.unblock_time:
            self.auto_unlock()
            return

        remaining = self.unblock_time - now
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        # Обновляем каждую секунду
        self.update_timer_id = self.block_window.after(1000, self.update_timer)

    def try_unlock(self):
        """Проверяет пароль и разблокирует при правильном вводе"""
        if self.password_entry.get() == self.password:
            if self.update_timer_id:
                self.block_window.after_cancel(self.update_timer_id)
            # Вызываем обработчик закрытия окна перед уничтожением
            self.block_window.event_generate("<<BlockScreenClose>>")
            self.block_window.destroy()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль!")
            self.password_entry.delete(0, tk.END)

    def auto_unlock(self):
        """Автоматически разблокирует экран после истечения времени"""
        if self.update_timer_id:
            self.block_window.after_cancel(self.update_timer_id)
        messagebox.showinfo("Разблокировка", "Перерыв окончен! Блокировка снята.")
        # Вызываем обработчик закрытия окна перед уничтожением
        self.block_window.event_generate("<<BlockScreenClose>>")
        self.block_window.destroy()
