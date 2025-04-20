"""Менеджер достижений"""
import json
"""
Файл: achievement_manager.py

Модуль для управления достижениями пользователя: загрузка, сохранение, обработка прогресса и отображение уведомлений.
Используется в приложении Game Timer.
"""

import os
from datetime import datetime
from typing import Dict, Optional, List
import logging
from achievements import Achievement, ACHIEVEMENTS
from notification_window import NotificationWindow

class AchievementManager:
    def __init__(self, settings, notification_callback=None):
        """
        Инициализация менеджера достижений
        
        Args:
            settings: Менеджер настроек
            notification_callback: Функция для показа уведомлений
        """
        self.settings = settings
        self.notification_callback = notification_callback
        self.logger = logging.getLogger('AchievementManager')
        
        # Загружаем сохраненные достижения
        self.achievements: Dict[str, Achievement] = ACHIEVEMENTS.copy()
        self._load_achievements()
        
        # Статистика для достижений
        self.stats = {
            'daily_uses': [],  # даты использования
            'session_duration': 0,  # длительность текущей сессии
            'daily_duration': 0,  # длительность за день
            'consecutive_days': 0,  # дней подряд
            'hotkeys_used': set(),  # использованные горячие клавиши
            'notifications_received': 0,  # полученные уведомления
            'breaks_taken': 0,  # сделанные перерывы
            'last_active_date': None  # последняя дата активности
        }
        
    def _load_achievements(self):
        """Загрузка сохраненных достижений"""
        try:
            saved = self.settings.get('achievements', {})
            for ach_id, data in saved.items():
                if ach_id in self.achievements:
                    # Обновляем существующее достижение сохраненными данными
                    achievement = self.achievements[ach_id]
                    achievement.progress = data.get('progress', 0)
                    achievement.completed = data.get('completed', False)
                    achievement.completed_date = data.get('completed_date', None)
        except Exception as e:
            self.logger.error(f"Error loading achievements: {str(e)}")
            
    def _save_achievements(self):
        """Сохранение достижений"""
        try:
            saved_data = {}
            for ach_id, achievement in self.achievements.items():
                saved_data[ach_id] = {
                    'progress': achievement.progress,
                    'completed': achievement.completed,
                    'completed_date': achievement.completed_date
                }
            self.settings.set('achievements', saved_data)
            self.settings.save()
        except Exception as e:
            self.logger.error(f"Error saving achievements: {str(e)}")
            
    def _notify_achievement(self, achievement: Achievement):
        """Показывает уведомление о получении достижения"""
        try:
            title = "🏆 Новое достижение!"
            message = f"{achievement.title}\n{achievement.description}"
            
            if self.notification_callback:
                self.notification_callback(title, message)
                
            self.logger.info(f"Achievement unlocked: {achievement.title}")
        except Exception as e:
            self.logger.error(f"Error showing achievement notification: {str(e)}")
            
    def update_achievement(self, achievement_id: str, progress: int = 1):
        """
        Обновляет прогресс достижения
        
        Args:
            achievement_id: ID достижения
            progress: Прогресс для добавления
        """
        try:
            if achievement_id not in self.achievements:
                return
                
            achievement = self.achievements[achievement_id]
            if achievement.completed:
                return
                
            achievement.progress += progress
            if achievement.progress >= achievement.max_progress:
                achievement.completed = True
                achievement.completed_date = datetime.now().isoformat()
                self._notify_achievement(achievement)
                
            self._save_achievements()
        except Exception as e:
            self.logger.error(f"Error updating achievement: {str(e)}")
            
    def check_time_achievements(self):
        """Проверяет достижения, связанные со временем"""
        try:
            current_hour = datetime.now().hour
            
            # Ночная сова (3 часа ночи)
            if current_hour == 3:
                self.update_achievement('night_owl')
                
            # Ранняя пташка (6 утра)
            if current_hour == 6:
                self.update_achievement('early_bird')
                
        except Exception as e:
            self.logger.error(f"Error checking time achievements: {str(e)}")
            
    def on_timer_start(self):
        """Вызывается при запуске таймера"""
        self.update_achievement('first_timer')
        self.update_achievement('time_master')
        
    def on_timer_tick(self, elapsed_seconds: int):
        """Вызывается каждую секунду работы таймера"""
        # Обновляем статистику
        self.stats['session_duration'] = elapsed_seconds
        self.stats['daily_duration'] += 1
        
        # Проверяем достижения за длительность
        if elapsed_seconds >= 3600:  # 1 час
            self.update_achievement('hour_warrior')
            
        if self.stats['daily_duration'] >= 10800:  # 3 часа
            self.update_achievement('marathon_runner')
            
    def on_hotkey_used(self, hotkey: str):
        """Вызывается при использовании горячей клавиши"""
        self.stats['hotkeys_used'].add(hotkey)
        if len(self.stats['hotkeys_used']) >= 3:
            self.update_achievement('hotkey_master')
            
    def on_notification_shown(self):
        """Вызывается при показе уведомления"""
        self.stats['notifications_received'] += 1
        self.update_achievement('notification_lover')
        
    def on_break_taken(self):
        """Вызывается когда пользователь делает перерыв вовремя"""
        self.stats['breaks_taken'] += 1
        self.update_achievement('break_champion')
        
    def on_daily_check(self):
        """Проверяет ежедневные достижения"""
        try:
            today = datetime.now().date()
            
            # Проверяем последнюю активность
            if self.stats['last_active_date']:
                last_date = datetime.fromisoformat(self.stats['last_active_date']).date()
                if (today - last_date).days == 1:
                    self.stats['consecutive_days'] += 1
                else:
                    self.stats['consecutive_days'] = 1
            else:
                self.stats['consecutive_days'] = 1
                
            # Обновляем дату последней активности
            self.stats['last_active_date'] = today.isoformat()
            
            # Проверяем достижения
            if self.stats['consecutive_days'] >= 5:
                self.update_achievement('daily_hero')
                
            if self.stats['consecutive_days'] >= 7:
                self.update_achievement('weekly_master')
                
            # Сохраняем статистику
            self.settings.set('achievement_stats', self.stats)
            self.settings.save()
            
        except Exception as e:
            self.logger.error(f"Error checking daily achievements: {str(e)}")
            
    def get_all_achievements(self) -> List[Achievement]:
        """Возвращает список всех достижений"""
        return list(self.achievements.values())
        
    def get_completed_achievements(self) -> List[Achievement]:
        """Возвращает список выполненных достижений"""
        return [a for a in self.achievements.values() if a.completed]
        
    def get_achievement_progress(self, achievement_id: str) -> tuple[int, int]:
        """Возвращает прогресс достижения"""
        if achievement_id in self.achievements:
            ach = self.achievements[achievement_id]
            return (ach.progress, ach.max_progress)
        return (0, 0)
