import tkinter as tk
from tkinter import ttk
import time
from typing import Optional, Dict, Any
from logger import Logger

class UIManager:
    """Менеджер обновлений пользовательского интерфейса"""
    
    def __init__(self, root: tk.Tk):
        self.logger = Logger("UIManager")
        self.root = root
        self.update_queue: Dict[str, Any] = {}
        self.last_update: Dict[str, float] = {}
        self.update_intervals: Dict[str, float] = {
            'timer': 1.0,  # Обновление таймера каждую секунду
            'progress': 1.0,  # Обновление прогресс-бара каждую секунду
            'status': 0.5,  # Обновление статуса каждые 500мс
            'process_list': 2.0,  # Обновление списка процессов каждые 2 секунды
        }
        self.widgets: Dict[str, tk.Widget] = {}
        self.running = True
        self._schedule_updates()
        self.logger.info("UIManager initialized")

    def register_widget(self, widget_id: str, widget: tk.Widget, update_interval: Optional[float] = None):
        """Регистрация виджета для управляемого обновления"""
        self.widgets[widget_id] = widget
        if update_interval is not None:
            self.update_intervals[widget_id] = update_interval
        self.last_update[widget_id] = 0
        self.logger.debug(f"Registered widget: {widget_id}")

    def queue_update(self, widget_id: str, update_data: Any):
        """Добавление обновления в очередь"""
        self.update_queue[widget_id] = update_data

    def _should_update(self, widget_id: str) -> bool:
        """Проверка необходимости обновления виджета"""
        current_time = time.time()
        if widget_id not in self.last_update:
            return True
        
        interval = self.update_intervals.get(widget_id, 1.0)
        return current_time - self.last_update[widget_id] >= interval

    def _update_timer_display(self, widget: tk.Label, remaining_time: int):
        """Оптимизированное обновление отображения таймера"""
        hours, remainder = divmod(remaining_time, 3600)
        mins, secs = divmod(remainder, 60)
        widget.config(text=f"Оставшееся время: {int(hours):02}:{int(mins):02}:{int(secs):02}")

    def _update_progress_bar(self, widget: ttk.Progressbar, value: float):
        """Оптимизированное обновление прогресс-бара"""
        widget.config(value=value)

    def _update_status_label(self, widget: tk.Label, status: str):
        """Оптимизированное обновление статуса"""
        widget.config(text=f"Статус: {status}")

    def _update_process_list(self, widget: tk.Label, processes: str):
        """Оптимизированное обновление списка процессов"""
        widget.config(text=f"Активные процессы: {processes}")

    def _process_updates(self):
        """Обработка очереди обновлений"""
        try:
            for widget_id, update_data in list(self.update_queue.items()):
                if not self._should_update(widget_id):
                    continue

                widget = self.widgets.get(widget_id)
                if not widget:
                    continue

                try:
                    if widget_id == 'timer':
                        self._update_timer_display(widget, update_data)
                    elif widget_id == 'progress':
                        self._update_progress_bar(widget, update_data)
                    elif widget_id == 'status':
                        self._update_status_label(widget, update_data)
                    elif widget_id == 'process_list':
                        self._update_process_list(widget, update_data)

                    self.last_update[widget_id] = time.time()
                    del self.update_queue[widget_id]

                except Exception as e:
                    self.logger.error(f"Error updating widget {widget_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error in update processing: {e}")

    def _schedule_updates(self):
        """Планирование регулярных обновлений"""
        if self.running:
            self._process_updates()
            self.root.after(50, self._schedule_updates)  # Проверка обновлений каждые 50мс

    def stop(self):
        """Остановка менеджера обновлений"""
        self.running = False
