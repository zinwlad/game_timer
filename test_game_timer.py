import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import threading
import time
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_timer import GameTimerApp
from game_blocker import GameBlocker
from notification_window import NotificationWindow
from block_screen import BlockScreen
from settings import Settings

class TestGameTimer(unittest.TestCase):
    def setUp(self):
        """Подготовка к каждому тесту"""
        self.root = tk.Tk()
        self.root.withdraw()  # Скрываем окно во время тестов
        self.game_blocker = GameBlocker(self.root)
        
    def tearDown(self):
        """Очистка после каждого теста"""
        if hasattr(self, 'game_blocker') and self.game_blocker.block_screen:
            try:
                self.game_blocker.block_screen.block_window.destroy()
            except:
                pass
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_initial_state(self):
        """Тест начального состояния GameBlocker"""
        # При создании мониторинг должен быть выключен
        self.assertFalse(self.game_blocker.is_monitoring)
        # При выключенном мониторинге игры не должны обнаруживаться
        self.assertFalse(self.game_blocker.is_game_running())
        
    @patch('psutil.process_iter')
    def test_monitoring_activation(self, mock_process_iter):
        """Тест активации мониторинга"""
        # Подготавливаем мок
        mock_process = MagicMock()
        mock_process.info = {'name': 'game.exe'}
        mock_process_iter.return_value = [mock_process]
        
        # Проверяем что при выключенном мониторинге игра не обнаруживается
        self.assertFalse(self.game_blocker.is_game_running())
        
        # Активируем мониторинг
        self.game_blocker.is_monitoring = True
        # Теперь игра должна обнаруживаться
        self.assertTrue(self.game_blocker.is_game_running())
            
    @patch('psutil.process_iter')
    def test_monitoring_deactivation(self, mock_process_iter):
        """Тест деактивации мониторинга"""
        # Подготавливаем мок
        mock_process = MagicMock()
        mock_process.info = {'name': 'game.exe'}
        mock_process_iter.return_value = [mock_process]
        
        # Активируем мониторинг
        self.game_blocker.is_monitoring = True
        # Проверяем что игра обнаруживается
        self.assertTrue(self.game_blocker.is_game_running())
        
        # Деактивируем мониторинг
        self.game_blocker.is_monitoring = False
        # Теперь игра не должна обнаруживаться
        self.assertFalse(self.game_blocker.is_game_running())

    @patch('psutil.process_iter')
    def test_notification_and_blocking(self, mock_process_iter):
        """Тест уведомлений и блокировки"""
        # Подготавливаем мок
        mock_process = MagicMock()
        mock_process.info = {'name': 'game.exe'}
        mock_process_iter.return_value = [mock_process]
        
        self.game_blocker.is_monitoring = True
        self.game_blocker.show_notification = MagicMock()
        self.game_blocker.block_game = MagicMock()
        
        # Запускаем один цикл мониторинга
        self.game_blocker.monitor_games_once()
        
        # Проверяем что было показано уведомление
        self.game_blocker.show_notification.assert_called_once()
        # Проверяем что была запущена блокировка
        self.game_blocker.block_game.assert_called_once()
            
    def test_cleanup_on_monitoring_stop(self):
        """Тест очистки при остановке мониторинга"""
        # Создаем мок для block_screen
        mock_block_screen = MagicMock()
        mock_block_window = MagicMock()
        mock_block_screen.block_window = mock_block_window
        self.game_blocker.block_screen = mock_block_screen
        
        # Запускаем и сразу останавливаем мониторинг
        self.game_blocker.is_monitoring = True
        
        def stop_monitoring():
            time.sleep(0.1)  # Даем время на запуск
            self.game_blocker.is_monitoring = False
            
        stop_thread = threading.Thread(target=stop_monitoring)
        stop_thread.start()
        
        # Запускаем мониторинг (он должен остановиться)
        self.game_blocker.monitor_games()
        
        # Ждем завершения
        stop_thread.join()
        
        # Проверяем что окно было уничтожено
        mock_block_window.destroy.assert_called_once()
        # Проверяем что block_screen был сброшен
        self.assertIsNone(self.game_blocker.block_screen)

    @patch('psutil.process_iter')
    def test_case_insensitive_process_detection(self, mock_process_iter):
        """Тест регистронезависимого обнаружения процессов"""
        self.game_blocker.is_monitoring = True
        
        # Проверяем разные варианты регистра
        test_cases = ['game.exe', 'GAME.EXE', 'Game.Exe', 'GAME.exe']
        
        for process_name in test_cases:
            mock_process = MagicMock()
            mock_process.info = {'name': process_name}
            mock_process_iter.return_value = [mock_process]
            
            self.assertTrue(
                self.game_blocker.is_game_running(),
                f"Failed to detect game process: {process_name}"
            )

    def test_timer_integration(self):
        """Тест интеграции с таймером"""
        app = GameTimerApp(self.root)
        
        # Проверяем что мониторинг изначально выключен
        self.assertFalse(app.game_blocker.is_monitoring)
        
        # Устанавливаем время
        app.hours.set(0)
        app.minutes.set(1)
        
        # Запускаем таймер
        app.start_timer()
        
        # Даем время на запуск потока
        time.sleep(0.1)
        
        # Проверяем что мониторинг включился
        self.assertTrue(hasattr(app, '_monitor_thread'))
        self.assertIsNotNone(app._monitor_thread)
        
        # Сбрасываем таймер
        app.reset_timer()
        
        # Даем время на остановку
        time.sleep(0.1)
        
        # Проверяем что мониторинг остановился
        self.assertFalse(app.game_blocker.is_monitoring)

if __name__ == '__main__':
    unittest.main()
