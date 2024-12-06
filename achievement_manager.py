import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from logger import Logger
from notification_window import NotificationWindow

@dataclass
class Achievement:
    """Класс для хранения информации о достижении"""
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    progress: int = 0
    required_progress: int = 1

class AchievementManager:
    """Менеджер достижений приложения"""
    
    def __init__(self, settings: Dict[str, Any], root=None):
        """
        Инициализация менеджера достижений
        :param settings: Настройки приложения
        :param root: Корневое окно для уведомлений (опционально)
        """
        self.logger = Logger("AchievementManager")
        self.settings = settings
        self.root = root
        self.achievements_file = "achievements.json"
        
        # Определение достижений
        self.achievements: Dict[str, Achievement] = {
            "early_bird": Achievement(
                id="early_bird",
                name="Ранняя пташка",
                description="Сделайте перерыв до 9 утра",
                icon="🌅"
            ),
            "consistent_breaks": Achievement(
                id="consistent_breaks",
                name="Постоянство",
                description="Сделайте перерывы 5 дней подряд",
                icon="🎯",
                required_progress=5
            ),
            "perfect_timing": Achievement(
                id="perfect_timing",
                name="Точность",
                description="Завершите таймер вовремя 10 раз",
                icon="⏰",
                required_progress=10
            ),
            "health_master": Achievement(
                id="health_master",
                name="Мастер здоровья",
                description="Накопите 24 часа перерывов",
                icon="🏆",
                required_progress=24*60*60  # 24 часа в секундах
            ),
            "night_owl": Achievement(
                id="night_owl",
                name="Ночная сова",
                description="Сделайте перерыв после 22:00",
                icon="🦉"
            ),
            "weekend_warrior": Achievement(
                id="weekend_warrior",
                name="Воин выходного дня",
                description="Сделайте перерывы в субботу и воскресенье",
                icon="🎮",
                required_progress=2
            )
        }
        
        self._load_achievements()
        self.logger.info("AchievementManager initialized")
        
    def _load_achievements(self) -> None:
        """Загрузка прогресса достижений из файла"""
        try:
            if os.path.exists(self.achievements_file):
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Обновляем состояние достижений
                    for ach_id, ach_data in data.get("achievements", {}).items():
                        if ach_id in self.achievements:
                            self.achievements[ach_id].unlocked = ach_data.get("unlocked", False)
                            self.achievements[ach_id].unlocked_at = ach_data.get("unlocked_at")
                            self.achievements[ach_id].progress = ach_data.get("progress", 0)
                            
                    self.logger.info("Achievements loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load achievements: {str(e)}")
            
    def _save_achievements(self) -> None:
        """Сохранение прогресса достижений в файл"""
        try:
            data = {
                "achievements": {
                    ach_id: {
                        "unlocked": ach.unlocked,
                        "unlocked_at": ach.unlocked_at,
                        "progress": ach.progress
                    }
                    for ach_id, ach in self.achievements.items()
                }
            }
            
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            self.logger.info("Achievements saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save achievements: {str(e)}")
            
    def check_achievements(self, context: Dict[str, Any] = None) -> None:
        """
        Проверка всех достижений
        :param context: Контекст для проверки достижений (время, дата и т.д.)
        """
        if context is None:
            context = {}
            
        current_time = context.get('current_time', datetime.now())
        
        # Проверяем каждое достижение
        self._check_early_bird(current_time)
        self._check_night_owl(current_time)
        self._check_weekend_warrior(current_time)
        self._check_consistent_breaks(current_time)
        self._check_perfect_timing()
        self._check_health_master()
        
        self._save_achievements()
        
    def _check_early_bird(self, current_time: datetime) -> None:
        """Проверка достижения 'Ранняя пташка'"""
        if (current_time.hour < 9 and 
            not self.achievements["early_bird"].unlocked):
            self._unlock_achievement("early_bird")
            
    def _check_night_owl(self, current_time: datetime) -> None:
        """Проверка достижения 'Ночная сова'"""
        if (current_time.hour >= 22 and 
            not self.achievements["night_owl"].unlocked):
            self._unlock_achievement("night_owl")
            
    def _check_weekend_warrior(self, current_time: datetime) -> None:
        """Проверка достижения 'Воин выходного дня'"""
        if current_time.weekday() >= 5:  # Суббота или воскресенье
            ach = self.achievements["weekend_warrior"]
            if not ach.unlocked:
                ach.progress += 1
                if ach.progress >= ach.required_progress:
                    self._unlock_achievement("weekend_warrior")
                    
    def _check_consistent_breaks(self, current_time: datetime) -> None:
        """Проверка достижения 'Постоянство'"""
        ach = self.achievements["consistent_breaks"]
        if not ach.unlocked:
            ach.progress += 1
            if ach.progress >= ach.required_progress:
                self._unlock_achievement("consistent_breaks")
                
    def _check_perfect_timing(self) -> None:
        """Проверка достижения 'Точность'"""
        ach = self.achievements["perfect_timing"]
        if not ach.unlocked:
            ach.progress += 1
            if ach.progress >= ach.required_progress:
                self._unlock_achievement("perfect_timing")
                
    def _check_health_master(self) -> None:
        """Проверка достижения 'Мастер здоровья'"""
        ach = self.achievements["health_master"]
        if not ach.unlocked:
            # Прогресс обновляется отдельно через add_break_time
            if ach.progress >= ach.required_progress:
                self._unlock_achievement("health_master")
                
    def add_break_time(self, duration: int) -> None:
        """
        Добавление времени перерыва
        :param duration: Длительность перерыва в секундах
        """
        ach = self.achievements["health_master"]
        if not ach.unlocked:
            ach.progress += duration
            self._check_health_master()
            self._save_achievements()
            
    def _unlock_achievement(self, achievement_id: str) -> None:
        """
        Разблокировка достижения
        :param achievement_id: ID достижения
        """
        if achievement_id in self.achievements:
            ach = self.achievements[achievement_id]
            if not ach.unlocked:
                ach.unlocked = True
                ach.unlocked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Показываем уведомление
                if self.root:
                    notification = NotificationWindow(
                        self.root,
                        "Новое достижение!",
                        f"{ach.icon} {ach.name}\n{ach.description}"
                    )
                    notification.show()
                    
                self.logger.info(f"Achievement unlocked: {achievement_id}")
                self._save_achievements()
                
    def get_all_achievements(self) -> List[Achievement]:
        """Получение списка всех достижений"""
        return list(self.achievements.values())
        
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Получение списка разблокированных достижений"""
        return [ach for ach in self.achievements.values() if ach.unlocked]
        
    def get_achievement_progress(self, achievement_id: str) -> tuple[int, int]:
        """
        Получение прогресса достижения
        :param achievement_id: ID достижения
        :return: (текущий прогресс, требуемый прогресс)
        """
        if achievement_id in self.achievements:
            ach = self.achievements[achievement_id]
            return ach.progress, ach.required_progress
        return 0, 0
        
    def reset_progress(self) -> None:
        """Сброс всего прогресса достижений"""
        try:
            for ach in self.achievements.values():
                ach.unlocked = False
                ach.unlocked_at = None
                ach.progress = 0
            self._save_achievements()
            self.logger.info("Achievement progress reset")
        except Exception as e:
            self.logger.error(f"Failed to reset achievements: {str(e)}")
