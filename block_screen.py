import tkinter as tk
from tkinter import messagebox
import time

class BlockScreen:
    def __init__(self, root, password):
        self.root = root
        self.password = password
        self.block_window = tk.Toplevel(self.root)
        self.block_window.attributes('-fullscreen', True)
        self.block_window.configure(bg='black')
        self.create_widgets()

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

        password_label = tk.Label(
            self.block_window,
            text="Введите пароль для разблокировки:",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        password_label.pack()

        self.password_entry = tk.Entry(
            self.block_window,
            font=("Arial", 24),
            show="*"
        )
        self.password_entry.pack()

        unlock_button = tk.Button(
            self.block_window,
            text="Разблокировать",
            font=("Arial", 24),
            command=self.check_password
        )
        unlock_button.pack(pady=20)

        self.start_timer()

    def start_timer(self):
        self.remaining_time = 30 * 60  # 30 minutes
        self.update_timer()

    def update_timer(self):
        if self.remaining_time > 0:
            minutes, seconds = divmod(self.remaining_time, 60)
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.remaining_time -= 1
            self.block_window.after(1000, self.update_timer)
        else:
            messagebox.showinfo("Время истекло", "Время блокировки истекло.")

    def check_password(self):
        if self.password_entry.get() == self.password:
            self.block_window.destroy()
        else:
            messagebox.showwarning("Ошибка", "Неверный пароль.")
