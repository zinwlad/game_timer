import pystray
from PIL import Image, ImageDraw
from threading import Thread
from logger import Logger
from typing import Callable, Tuple

class TrayManager:
    """Менеджер системного трея"""
    
    def __init__(self, show_window_callback: Callable, quit_callback: Callable):
        self.logger = Logger("TrayManager")
        self.show_window_callback = show_window_callback
        self.quit_callback = quit_callback
        self.tray_icon = None
        self._setup_tray_icon()
        
    def _create_tray_icon(self) -> Image.Image:
        """Создание иконки для трея"""
        try:
            # Создаем простую иконку
            width = 64
            height = 64
            color1 = 'blue'
            color2 = 'white'
            
            image = Image.new('RGB', (width, height), color1)
            dc = ImageDraw.Draw(image)
            dc.ellipse([10, 10, width-10, height-10], fill=color2)
            
            return image
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {str(e)}")
            return None

    def _setup_tray_icon(self) -> None:
        """Настройка иконки в трее"""
        try:
            self.tray_icon = pystray.Icon("Game Timer")
            self.tray_icon.icon = self._create_tray_icon()
            menu_items = (
                pystray.MenuItem("Show", self.show_window_callback),
                pystray.MenuItem("Exit", self.quit_callback)
            )
            self.tray_icon.menu = pystray.Menu(*menu_items)
            Thread(target=self.tray_icon.run, daemon=True).start()
            self.logger.info("Tray icon setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup tray icon: {str(e)}")

    def stop(self) -> None:
        """Остановка иконки в трее"""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
                self.logger.info("Tray icon stopped")
        except Exception as e:
            self.logger.error(f"Error stopping tray icon: {str(e)}")
