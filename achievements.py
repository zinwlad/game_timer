"""
Файл: achievements.py

Модуль для определения структуры достижений, хранения и сериализации информации о достижениях пользователя.
Содержит dataclass Achievement и словарь ACHIEVEMENTS с базовыми достижениями для Game Timer.
"""

from typing import Dict, List, Optional
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Achievement:
    id: str
    title: str
    description: str
    icon: str  # путь к иконке
    secret: bool = False  # скрытое достижение
    progress: int = 0  # текущий прогресс
    max_progress: int = 1  # максимальный прогресс
    completed: bool = False  # выполнено ли достижение
    completed_date: Optional[str] = None  # дата выполнения

# Определение всех достижений
ACHIEVEMENTS = {
    # Базовые достижения
    'first_timer': Achievement(
        id='first_timer',
        title='Первые шаги',
        description='Запустите таймер в первый раз',
        icon='🎯'
    ),
    'time_master': Achievement(
        id='time_master',
        title='Мастер времени',
        description='Используйте таймер 10 раз',
        icon='⏰',
        max_progress=10
    ),
    
    # Достижения за длительность
    'hour_warrior': Achievement(
        id='hour_warrior',
        title='Воин времени',
        description='Отыграйте 1 час без перерыва',
        icon='⚔️'
    ),
    'marathon_runner': Achievement(
        id='marathon_runner',
        title='Марафонец',
        description='Отыграйте 3 часа за день',
        icon='🏃'
    ),
    
    # Достижения за регулярность
    'daily_hero': Achievement(
        id='daily_hero',
        title='Ежедневный герой',
        description='Используйте таймер 5 дней подряд',
        icon='📅',
        max_progress=5
    ),
    'weekly_master': Achievement(
        id='weekly_master',
        title='Недельный мастер',
        description='Используйте таймер каждый день недели',
        icon='📆',
        max_progress=7
    ),
    
    # Секретные достижения
    'night_owl': Achievement(
        id='night_owl',
        title='Ночная сова',
        description='Играйте в 3 часа ночи',
        icon='🦉',
        secret=True
    ),
    'early_bird': Achievement(
        id='early_bird',
        title='Ранняя пташка',
        description='Играйте в 6 утра',
        icon='🐦',
        secret=True
    ),
    
    # Достижения за использование функций
    'hotkey_master': Achievement(
        id='hotkey_master',
        title='Мастер горячих клавиш',
        description='Используйте все горячие клавиши',
        icon='⌨️',
        max_progress=3
    ),
    'notification_lover': Achievement(
        id='notification_lover',
        title='Любитель уведомлений',
        description='Получите 10 уведомлений',
        icon='🔔',
        max_progress=10
    ),
    
    # Достижения за дисциплину
    'discipline_master': Achievement(
        id='discipline_master',
        title='Мастер дисциплины',
        description='Не нарушайте таймер 7 дней подряд',
        icon='🎓',
        max_progress=7
    ),
    'break_champion': Achievement(
        id='break_champion',
        title='Чемпион перерывов',
        description='Сделайте 10 перерывов вовремя',
        icon='🏆',
        max_progress=10
    )
}
