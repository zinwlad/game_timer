import time
import sqlite3
from logger import Logger
import psutil
from datetime import datetime, timedelta

class ProcessMonitor:
    """Класс для мониторинга процессов"""
    def __init__(self):
        self.logger = Logger("ProcessMonitor")
        self._cache = {}
        self._cache_time = 0
        self._cache_lifetime = 30
        self._usage_db = "usage_stats.db"
        self._process_history = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = 600
        # Добавляем буфер для записей в БД
        self._write_buffer = []
        self._buffer_size = 50  # Максимальный размер буфера
        self._last_flush = time.time()
        self._flush_interval = 60  # Интервал принудительной записи в секундах
        self._init_db()
        self.logger.info("ProcessMonitor initialized")

    def _init_db(self):
        """Инициализация базы данных для статистики"""
        try:
            with sqlite3.connect(self._usage_db) as conn:
                # Добавляем индекс для оптимизации запросов
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS usage_stats (
                        timestamp TEXT,
                        process_name TEXT,
                        duration INTEGER,
                        PRIMARY KEY (timestamp, process_name)
                    )
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_process_time 
                    ON usage_stats(process_name, timestamp)
                ''')
            self.logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise

    def _flush_buffer(self, force=False):
        """Записывает буферизированные данные в БД"""
        current_time = time.time()

        # Проверяем необходимость записи
        if not force and len(self._write_buffer) < self._buffer_size and \
           current_time - self._last_flush < self._flush_interval:
            return

        if not self._write_buffer:
            return

        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    'INSERT OR REPLACE INTO usage_stats (timestamp, process_name, duration) VALUES (?, ?, ?)',
                    self._write_buffer
                )
                conn.commit()

            self.logger.debug(f"Flushed {len(self._write_buffer)} records to database")
            self._write_buffer.clear()
            self._last_flush = current_time

        except sqlite3.Error as e:
            self.logger.error(f"Error flushing buffer to database: {e}")

    def log_usage(self, process_name, duration):
        """Логирование использования процесса с буферизацией"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._write_buffer.append((timestamp, process_name, int(duration)))

        # Проверяем необходимость сброса буфера
        self._flush_buffer()

    def cleanup_old_data(self):
        """Очистка старых данных из БД"""
        try:
            # Определяем дату, старше которой данные будут удалены (например, 30 дней)
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM usage_stats WHERE timestamp < ?', (cutoff_date,))
                if cursor.rowcount > 0:
                    self.logger.info(f"Cleaned up {cursor.rowcount} old records")
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up old data: {e}")

    def __del__(self):
        """Деструктор для гарантированной записи данных при завершении"""
        self._flush_buffer(force=True)

    def get_active_processes(self):
        """Получение списка активных процессов с оптимизированным кэшированием"""
        current_time = time.time()

        # Проверяем актуальность кэша
        if current_time - self._cache_time <= self._cache_lifetime:
            return list(self._cache.keys())  # Возвращаем кэшированный результат

        try:
            new_cache = {}
            # Получаем все процессы одним вызовом
            processes = {p.info['name']: p for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])}

            for proc_name, p in processes.items():
                try:
                    proc_info = p.info
                    new_cache[proc_name] = {
                        'pid': p.pid,
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent'],
                        'last_update': current_time
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            self._cache = new_cache
            self._cache_time = current_time

            # Очистка старых данных
            if current_time - self._last_cleanup >= self._cleanup_interval:
                self._cleanup_old_data()
                self._last_cleanup = current_time

            return list(self._cache.keys())

        except Exception as e:
            self.logger.error(f"Error getting active processes: {e}")
            return list(self._cache.keys()) if self._cache else []

    # Additional methods and logic for ProcessMonitor class
