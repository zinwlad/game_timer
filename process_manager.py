"""
Файл: process_manager.py

Модуль для мониторинга и учёта времени, проведённого в отслеживаемых процессах (играх) в приложении Game Timer.
"""

import psutil
import logging
from datetime import datetime, timedelta
import sqlite3
import time

class ProcessManager:
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger('ProcessManager')
        self._cache = {}
        self._cache_time = 0
        self._cache_lifetime = 60
        self._usage_db = "usage_stats.db"
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600
        self._write_buffer = []
        self._buffer_size = 100
        self._last_flush = time.time()
        self._flush_interval = 300
        self._init_db()

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
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_process_time 
                    ON usage_stats(process_name, timestamp)
                ''')
            self.logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise

    def get_monitored_processes(self):
        """Возвращает список отслеживаемых процессов из настроек"""
        return self.settings.get("processes", [])

    def get_active_processes(self):
        """Получение списка активных процессов с кэшированием"""
        current_time = time.time()
        if current_time - self._cache_time <= self._cache_lifetime:
            return list(self._cache.keys())
        try:
            new_cache = {}
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name:
                        new_cache[proc_name.lower()] = {
                            'pid': proc.pid,
                            'last_update': current_time
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self._cache = new_cache
            self._cache_time = current_time
            if current_time - self._last_cleanup >= self._cleanup_interval:
                self.cleanup_old_data()
                self._last_cleanup = current_time
            return list(self._cache.keys())
        except Exception as e:
            self.logger.error(f"Error getting active processes: {e}")
            return list(self._cache.keys()) if self._cache else []

    def log_usage(self, process_name, duration):
        """Логирование использования процесса с буферизацией"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._write_buffer.append((timestamp, process_name, int(duration)))
        self._flush_buffer()

    def get_daily_usage(self, date=None):
        """Возвращает суммарное время использования всех отслеживаемых процессов за день (секунды)"""
        if date is None:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date, '%Y-%m-%d').date() if isinstance(date, str) else date
        total = 0
        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT SUM(duration) FROM usage_stats
                    WHERE date(timestamp) = ?
                ''', (date.strftime('%Y-%m-%d'),))
                result = cursor.fetchone()
                total = result[0] if result and result[0] else 0
        except Exception as e:
            self.logger.error(f"Error getting daily usage: {e}")
        return total

    def get_weekly_usage(self, start_date=None):
        """Возвращает суммарное время использования всех отслеживаемых процессов за неделю (секунды)"""
        if start_date is None:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if isinstance(start_date, str) else start_date
        end_date = start_date + timedelta(days=7)
        total = 0
        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT SUM(duration) FROM usage_stats
                    WHERE date(timestamp) >= ? AND date(timestamp) < ?
                ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                result = cursor.fetchone()
                total = result[0] if result and result[0] else 0
        except Exception as e:
            self.logger.error(f"Error getting weekly usage: {e}")
        return total

    def _flush_buffer(self, force=False):
        """Записывает буферизированные данные в БД"""
        current_time = time.time()
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

    def cleanup_old_data(self):
        """Очистка старых данных из БД"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM usage_stats WHERE date(timestamp) < ?', (cutoff_date,))
                conn.commit()
            self.logger.info("Old data cleaned up")
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up old data: {e}")

    def is_any_monitored_process_running(self):
        """Проверяет, запущен ли хотя бы один из отслеживаемых процессов"""
        monitored_processes = self.get_monitored_processes()
        for process_name in monitored_processes:
            if self.is_process_running(process_name):
                return True
        return False


    def is_process_running(self, process_name):
        """Проверяет, запущен ли указанный процесс"""
        process_lower = process_name.lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_info = proc.info
                if not proc_info or 'name' not in proc_info:
                    continue
                proc_name = proc_info['name'].lower()
                proc_path = proc_info.get('exe', '')
                if proc_path:
                    proc_path = proc_path.lower()
                if process_lower in proc_name or (proc_path and process_lower in proc_path):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
