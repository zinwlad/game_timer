import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'game_timer.py',
    '--onefile',
    '--windowed',
    '--name=GameTimer',
    '--icon=timer.ico',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=pystray._win32',
    '--hidden-import=win32com.client',
    '--hidden-import=keyboard',
    '--hidden-import=psutil',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageDraw',
    '--add-data=timer.ico;.',
    '--add-data=timer_settings.json;.',
    '--clean'
])
