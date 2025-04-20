import PyInstaller.__main__
import os

# Список всех Python файлов проекта
project_files = [
    'game_timer.py',
    'timer_manager.py',
    'game_blocker.py',
    'block_screen.py',
    'activity_monitor.py',
    'achievement_manager.py',
    'autostart_manager.py',
    'hotkey_manager.py',
    'logger.py',
    'notification_window.py',
    'process_monitor.py',
    'settings.py',
    'timer_notifications.py',
    'tray_manager.py',
    'ui_manager.py'
]

# Создаем строку с данными для добавления
data_files = [
    '--add-data=timer.ico;.',
    '--add-data=timer_settings.json;.',
    '--add-data=achievements.json;.',
    '--add-data=README.md;.',
    '--add-data=requirements.txt;.',
    '--add-data=logs;logs'  # Добавляем папку с логами
]

# Скрытые импорты
hidden_imports = [
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=pystray._win32',
    '--hidden-import=win32com.client',
    '--hidden-import=keyboard',
    '--hidden-import=psutil',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageDraw',
    '--hidden-import=win32gui',
    '--hidden-import=win32con',
    '--hidden-import=win32api',
    '--hidden-import=win32com',
    '--hidden-import=winreg',
    '--hidden-import=sqlite3',
    '--hidden-import=concurrent.futures',
    '--hidden-import=threading',
    '--hidden-import=queue',
    '--hidden-import=json',
    '--hidden-import=datetime',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=tkinter.messagebox'
]

# Опции сборки
build_options = [
    'game_timer.py',  # Основной файл
    '--onefile',      # Собрать в один файл
    '--windowed',     # Без консольного окна
    '--name=GameTimer',  # Имя выходного файла
    '--icon=timer.ico',  # Иконка приложения
    '--clean',        # Очистить временные файлы после сборки
    '--noconfirm',    # Не спрашивать подтверждения при очистке
    '--uac-admin',    # Запрашивать права администратора
    '--log-level=INFO'  # Уровень логирования
]

# Объединяем все опции
options = (
    build_options +
    hidden_imports +
    data_files
)

# Запускаем сборку
PyInstaller.__main__.run(options)
