import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from logger import Logger

class ThemeManager:
    """Менеджер тем оформления приложения"""
    
    def __init__(self, root: tk.Tk, style: ttk.Style):
        self.logger = Logger("ThemeManager")
        self.root = root
        self.style = style
        self.themes: Dict[str, Dict[str, Any]] = {
            "dark": {
                "background": "#2b2b2b",
                "foreground": "white",
                "button_bg": "#404040",
                "button_fg": "white"
            },
            "light": {
                "background": "#f0f0f0",
                "foreground": "black",
                "button_bg": "#e0e0e0",
                "button_fg": "black"
            }
        }
        
    def apply_theme(self, theme_name: str) -> None:
        """Применяет выбранную тему к приложению"""
        try:
            if theme_name not in self.themes:
                self.logger.warning(f"Unknown theme: {theme_name}, using light theme")
                theme_name = "light"
                
            theme = self.themes[theme_name]
            
            # Настройка основного окна
            self.root.configure(bg=theme["background"])
            
            # Настройка стилей виджетов
            self.style.configure("TFrame", background=theme["background"])
            self.style.configure("TLabel", 
                               background=theme["background"], 
                               foreground=theme["foreground"])
            self.style.configure("TButton", 
                               background=theme["button_bg"], 
                               foreground=theme["button_fg"])
            self.style.configure("TCheckbutton", 
                               background=theme["background"], 
                               foreground=theme["foreground"])
            self.style.configure("TRadiobutton", 
                               background=theme["background"], 
                               foreground=theme["foreground"])
            self.style.configure("TLabelframe", 
                               background=theme["background"], 
                               foreground=theme["foreground"])
            self.style.configure("TLabelframe.Label", 
                               background=theme["background"], 
                               foreground=theme["foreground"])
            self.style.configure("Horizontal.TProgressbar", 
                               background=theme["button_bg"], 
                               troughcolor=theme["background"])
                               
            self.logger.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Error applying theme {theme_name}: {str(e)}")
            
    def add_theme(self, name: str, theme_config: Dict[str, Any]) -> None:
        """Добавляет новую тему"""
        try:
            required_keys = {"background", "foreground", "button_bg", "button_fg"}
            if not all(key in theme_config for key in required_keys):
                raise ValueError(f"Theme config must contain all required keys: {required_keys}")
                
            self.themes[name] = theme_config
            self.logger.info(f"Added new theme: {name}")
            
        except Exception as e:
            self.logger.error(f"Error adding theme {name}: {str(e)}")
            
    def get_available_themes(self) -> list:
        """Возвращает список доступных тем"""
        return list(self.themes.keys())
