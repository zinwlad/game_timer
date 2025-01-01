import os
import time
import random
import tkinter as tk
from tkinter import simpledialog, messagebox
import psutil
import ctypes
from block_screen import BlockScreen

class GameBlocker:
    def __init__(self, root, monitored_processes=None):
        self.root = root
        self.monitored_processes = monitored_processes or ["game.exe", "test_game.exe"]  # Список процессов для мониторинга
        self.block_screen = None
        self.password = "1234"  # Пароль для разблокировки
        self.is_monitoring = False  # Флаг активности мониторинга
        self.timer_expired = False  # Флаг окончания таймера
        self.block_delay = 15  # Задержка в секундах перед блокировкой
        self.block_timer = None  # Время, когда нужно заблокировать
        
    def is_game_running(self):
        """Проверяет, запущена ли игра"""
        if not self.is_monitoring:  # Если мониторинг не активен, считаем что игра не запущена
            return False
            
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                process_name = proc.info['name'].lower()
                # Проверяем каждый процесс из списка
                for game in self.monitored_processes:
                    if game.lower() in process_name:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
            
    def block_game(self):
        """Блокирует игру"""
        if self.block_screen is None:
            self.block_screen = BlockScreen(self.root, self.password)
            self.block_screen.block_window.lift()  # Поднимаем окно поверх всех окон
            self.block_screen.block_window.focus_force()  # Принудительно фокусируем окно
            
    def monitor_games_once(self):
        """Выполняет один цикл мониторинга"""
        if self.is_game_running() and self.timer_expired:
            current_time = time.time()
            
            # Если таймер блокировки еще не установлен - устанавливаем
            if self.block_timer is None:
                print(f"Timer expired and game running, blocking in {self.block_delay} seconds")
                self.block_timer = current_time + self.block_delay
                
            # Если время блокировки пришло - блокируем
            elif current_time >= self.block_timer:
                print("Blocking delay expired, blocking game")
                self.block_game()
                
    def monitor_games(self):
        """Мониторит запущенные игры"""
        import time
        
        # Даем системе время на инициализацию
        time.sleep(5)  # Ждем 5 секунд перед началом мониторинга
        self.is_monitoring = True  # Активируем мониторинг
        
        while self.is_monitoring:  # Проверяем флаг мониторинга
            if self.is_game_running() and self.timer_expired:
                current_time = time.time()
                
                # Если таймер блокировки еще не установлен - устанавливаем
                if self.block_timer is None:
                    print(f"Timer expired and game running, blocking in {self.block_delay} seconds")
                    self.block_timer = current_time + self.block_delay
                    
                # Если время блокировки пришло - блокируем
                elif current_time >= self.block_timer and self.block_screen is None:
                    print("Blocking delay expired, blocking game")
                    self.block_game()
            else:
                # Если игра не запущена или таймер не истек - сбрасываем таймер блокировки и убираем блокировку
                self.block_timer = None
                if self.block_screen:
                    self.block_screen.block_window.destroy()
                    self.block_screen = None
                    
            time.sleep(1)  # Проверяем каждую секунду
            
        # Очищаем все окна при остановке мониторинга
        if self.block_screen:
            self.block_screen.block_window.destroy()
            self.block_screen = None
        self.block_timer = None  # Сбрасываем таймер блокировки

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    blocker = GameBlocker(root)
    blocker.monitor_games()
