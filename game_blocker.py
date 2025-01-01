import os
import time
import random
import tkinter as tk
from tkinter import simpledialog, messagebox
import psutil
import ctypes
from block_screen import BlockScreen
from PIL import Image, ImageTk
import json
from logger import Logger
from countdown_window import CountdownWindow

class GameBlocker:
    def __init__(self, root, monitored_processes=None):
        self.root = root
        self.monitored_processes = monitored_processes or []  # Список процессов для мониторинга
        self.block_screen = None
        self.password = "1234"  # Пароль для разблокировки
        self.is_monitoring = False  # Флаг активности мониторинга
        self.timer_expired = False  # Флаг окончания таймера
        self.block_delay = 15  # Задержка в секундах перед блокировкой
        self.block_timer = None  # Время, когда нужно заблокировать
        self.logger = Logger("GameBlocker")
        self.countdown_window = None  # Добавляем хранение окна обратного отсчета
        
    def is_game_running(self):
        """Проверяет, запущена ли игра"""
        if not self.monitored_processes:  # Если список процессов пуст
            self.logger.warning("No monitored processes configured")
            return False
            
        for proc in psutil.process_iter(['name']):
            try:
                process_name = proc.info['name'].lower()
                # Проверяем каждый процесс из списка
                for game in self.monitored_processes:
                    if game.lower() in process_name:
                        self.logger.info(f"Found running game process: {process_name}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        self.logger.info("No monitored games are running")
        return False
            
    def block_game(self):
        """Блокирует игру"""
        if self.block_screen is None:
            self.block_screen = BlockScreen(self.root, self.password)
            self.block_screen.block_window.lift()  # Поднимаем окно поверх всех окон
            self.block_screen.block_window.focus_force()  # Принудительно фокусируем окно
            
            # Добавляем отслеживание закрытия окна блокировки
            self.block_screen.block_window.bind("<<BlockScreenClose>>", lambda e: self.on_block_screen_close())
            
    def on_block_screen_close(self):
        """Обработчик закрытия окна блокировки"""
        self.block_screen = None
        self.block_timer = None
        self.timer_expired = False  # Сбрасываем флаг истечения таймера
        
    def monitor_games_once(self):
        """Выполняет один цикл мониторинга"""
        if not self.is_game_running():
            # Если игра не запущена, сбрасываем таймер блокировки
            self.block_timer = None
            return
            
        if self.timer_expired:
            current_time = time.time()
            
            # Если таймер блокировки еще не установлен - устанавливаем
            if self.block_timer is None:
                print(f"Timer expired and game running, blocking in {self.block_delay} seconds")
                self.block_timer = current_time + self.block_delay
                
            # Если время блокировки пришло - блокируем
            elif current_time >= self.block_timer:
                print("Blocking delay expired, blocking game")
                self.show_block_screen()
                
    def monitor_games(self):
        """Мониторит запущенные игры"""
        self.is_monitoring = True
        self.logger.info("Game monitoring started")
        
        while self.is_monitoring:
            if self.timer_expired:  # Если таймер истек
                if self.is_game_running():  # Проверяем запущенные игры
                    current_time = time.time()
                    
                    # Если таймер блокировки еще не установлен - устанавливаем
                    if self.block_timer is None:
                        self.logger.info(f"Timer expired and game running, blocking in {self.block_delay} seconds")
                        self.block_timer = current_time + self.block_delay
                        
                    # Если время блокировки пришло - блокируем
                    elif current_time >= self.block_timer and self.block_screen is None:
                        self.logger.info("Blocking delay expired, blocking game")
                        self.show_block_screen()
                else:
                    # Если игра не запущена - сбрасываем таймер блокировки
                    if self.block_timer is not None:
                        self.logger.info("No games running, resetting block timer")
                        self.block_timer = None
                        self.remove_block()
            
            time.sleep(1)  # Проверяем каждую секунду
        
        self.logger.info("Game monitoring stopped")
        # Очищаем все окна при остановке мониторинга
        self.remove_block()
        
    def show_block_screen(self):
        """Показывает экран блокировки"""
        try:
            # Если окно обратного отсчета уже показано, ничего не делаем
            if self.countdown_window is not None:
                return
                
            # Показываем окно с обратным отсчетом
            self.countdown_window = CountdownWindow(self.root)
            self.countdown_window.show()
            
            # Ждем 15 секунд перед показом экрана блокировки
            self.root.after(15000, self._show_block_window)
            
        except Exception as e:
            self.logger.error(f"Error showing block screen: {str(e)}")
            
    def _show_block_window(self):
        """Показывает окно блокировки и очищает окно обратного отсчета"""
        if self.countdown_window:
            try:
                self.countdown_window.window.destroy()
            except:
                pass
            self.countdown_window = None
        self.block_game()
        
    def remove_block(self):
        """Убирает блокировку"""
        if self.countdown_window:
            try:
                self.countdown_window.window.destroy()
            except:
                pass
            self.countdown_window = None
            
        if self.block_screen:
            self.block_screen.block_window.destroy()
            self.block_screen = None
        self.block_timer = None  # Сбрасываем таймер блокировки
        
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    blocker = GameBlocker(root)
    blocker.monitor_games()
