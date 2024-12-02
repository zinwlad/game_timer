import time
import sqlite3
from logger import Logger
import psutil

class ProcessMonitor:
    """Класс для мониторинга процессов"""
    def __init__(self):
        self.logger = Logger("ProcessMonitor")
        self._cache = {}
        self._cache_time = 0
        self._cache_lifetime = 5
        self._usage_db = "usage_stats.db"
        self._process_history = {}  # История процессов
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Очистка кэша каждые 5 минут
        self._init_db()
        self.logger.info("ProcessMonitor initialized")

    def _init_db(self):
        """Инициализация базы данных для статистики"""
        try:
            with sqlite3.connect(self._usage_db) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS usage_stats (
                        timestamp TEXT,
                        process_name TEXT,
                        duration INTEGER,
                        PRIMARY KEY (timestamp, process_name)
                    )
                ''')
            self.logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise

    def get_active_processes(self):
        """Получение списка активных процессов с оптимизированным кэшированием"""
        current_time = time.time()

        # Проверяем актуальность кэша
        if current_time - self._cache_time > self._cache_lifetime:
            try:
                new_cache = {}
                for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                    try:
                        proc_info = p.info
                        proc_name = proc_info['name']
                        new_cache[proc_name] = {
                            'pid': p.pid,
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent'],
                            'time': current_time
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Обновляем кэш и время
                self._cache = new_cache
                self._cache_time = current_time

            except Exception as e:
                self.logger.error(f"Failed to update process cache: {str(e)}")
                return self._cache.keys()  # Возвращаем старый кэш в случае ошибки

        return self._cache.keys()

    # Additional methods and logic for ProcessMonitor class
