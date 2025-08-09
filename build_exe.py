"""
Файл: build_exe.py

Скрипт сборки и упаковки приложения Game Timer с помощью PyInstaller.
Делает устойчивой сборку: выбирает иконку по наличию, добавляет существующие ресурсы,
и использует актуальные скрытые импорты под текущий стек (PyQt5, psutil, keyboard, win32*).
"""

import os
import PyInstaller.__main__


def exist(path: str) -> bool:
    return os.path.exists(path)


def add_data_arg(src: str, dst: str = '.') -> str:
    return f"--add-data={src};{dst}"


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)

    # Динамический выбор иконки: prefer .ico
    icon_candidates = [
        os.path.join(base_dir, 'timer.ico'),
        os.path.join(base_dir, 'Icon_game_timer.png'),
    ]
    icon_arg = None
    for ico in icon_candidates:
        if exist(ico):
            icon_arg = f"--icon={ico}"
            break

    # Ресурсы (добавляем только существующие)
    maybe_data = [
        ('Icon_game_timer.png', '.'),
        ('timer.ico', '.'),
        ('achievements.json', '.'),
        ('settings.json', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
        ('logs', 'logs'),  # папка логов
    ]
    data_files = []
    for src, dst in maybe_data:
        full = os.path.join(base_dir, src)
        if exist(full):
            data_files.append(add_data_arg(full, dst))

    # Скрытые импорты под текущие зависимости
    hidden_imports = [
        '--hidden-import=keyboard',
        '--hidden-import=psutil',
        '--hidden-import=win32gui',
        '--hidden-import=win32con',
        '--hidden-import=win32api',
        '--hidden-import=win32com.client',
        '--hidden-import=winreg',
        '--hidden-import=sqlite3',
    ]

    build_args = [
        '--onefile',
        '--noconsole',
    ]

    if icon_arg:
        build_args.append(icon_arg)

    build_args.extend(data_files)
    build_args.extend(hidden_imports)

    # Главный модуль
    build_args.append(os.path.join(base_dir, 'game_timer.py'))

    # Необязательно: задать dist/build пути
    # build_args += [
    #     f"--distpath={os.path.join(base_dir, 'dist')}",
    #     f"--workpath={os.path.join(base_dir, 'build')}",
    #     '--clean',
    # ]

    PyInstaller.__main__.run(build_args)
