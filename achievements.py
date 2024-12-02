import json
import os
from datetime import datetime, timedelta
from logger import Logger

class Achievements:
    def __init__(self, settings):
        # Создаем директорию для логов если её нет
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        self.logger = Logger("Achievements", "logs/achievements.log")
        self.settings = settings
        self.achievements_file = "achievements.json"
        self.achievements_data = self.load_achievements()
        
        # Определение достижений
        self.available_achievements = {
            "early_bird": {
                "name": "Ранняя пташка",
                "description": "Сделайте перерыв до 9 утра",
                "icon": "🌅"
            },
            "consistent_breaks": {
                "name": "Постоянство",
                "description": "Сделайте перерывы 5 дней подряд",
                "icon": "🎯"
            },
            "perfect_timing": {
                "name": "Точность",
                "description": "Завершите таймер вовремя 10 раз",
                "icon": "⏰"
            },
            "health_master": {
                "name": "Мастер здоровья",
                "description": "Накопите 24 часа перерывов",
                "icon": "🏆"
            }
        }

    def load_achievements(self):
        """Загрузка прогресса достижений"""
        try:
            if os.path.exists(self.achievements_file):
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "unlocked": {},
                "progress": {
                    "consecutive_days": 0,
                    "last_break_date": None,
                    "total_breaks": 0,
                    "total_break_time": 0,
                    "perfect_timers": 0
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to load achievements: {str(e)}")
            return {"unlocked": {}, "progress": {}}

    def save_achievements(self):
        """Сохранение прогресса достижений"""
        try:
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(self.achievements_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save achievements: {str(e)}")

    def check_early_bird(self):
        """Проверка достижения 'Ранняя пташка'"""
        current_hour = datetime.now().hour
        if current_hour < 9 and "early_bird" not in self.achievements_data["unlocked"]:
            self.unlock_achievement("early_bird")

    def check_consistent_breaks(self):
        """Проверка достижения 'Постоянство'"""
        today = datetime.now().date()
        last_break = self.achievements_data["progress"].get("last_break_date")
        
        if last_break:
            last_break = datetime.strptime(last_break, "%Y-%m-%d").date()
            if (today - last_break).days == 1:
                self.achievements_data["progress"]["consecutive_days"] += 1
            elif (today - last_break).days > 1:
                self.achievements_data["progress"]["consecutive_days"] = 1
        else:
            self.achievements_data["progress"]["consecutive_days"] = 1
            
        self.achievements_data["progress"]["last_break_date"] = today.strftime("%Y-%m-%d")
        
        if (self.achievements_data["progress"]["consecutive_days"] >= 5 and 
            "consistent_breaks" not in self.achievements_data["unlocked"]):
            self.unlock_achievement("consistent_breaks")
        
        self.save_achievements()

    def check_perfect_timing(self):
        """Проверка достижения 'Точность'"""
        self.achievements_data["progress"]["perfect_timers"] += 1
        if (self.achievements_data["progress"]["perfect_timers"] >= 10 and 
            "perfect_timing" not in self.achievements_data["unlocked"]):
            self.unlock_achievement("perfect_timing")
        self.save_achievements()

    def check_health_master(self, break_duration):
        """Проверка достижения 'Мастер здоровья'"""
        self.achievements_data["progress"]["total_break_time"] += break_duration
        if (self.achievements_data["progress"]["total_break_time"] >= 24*60*60 and 
            "health_master" not in self.achievements_data["unlocked"]):
            self.unlock_achievement("health_master")
        self.save_achievements()

    def unlock_achievement(self, achievement_id):
        """Разблокировка достижения"""
        if achievement_id not in self.achievements_data["unlocked"]:
            achievement = self.available_achievements[achievement_id]
            self.achievements_data["unlocked"][achievement_id] = {
                "name": achievement["name"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_achievements()
            return True
        return False

    def get_all_achievements(self):
        """Получение всех достижений с их статусом"""
        all_achievements = {}
        for ach_id, ach_data in self.available_achievements.items():
            all_achievements[ach_id] = {
                **ach_data,
                "unlocked": ach_id in self.achievements_data["unlocked"],
                "unlocked_at": self.achievements_data["unlocked"].get(ach_id, {}).get("unlocked_at")
            }
        return all_achievements

    def get_progress(self):
        """Получение прогресса достижений"""
        return self.achievements_data["progress"]
