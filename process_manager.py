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
        # Время жизни кэша берём из настроек проверки процессов (в секундах)
        self._cache_lifetime = max(1, int(self.settings.get('process_check_interval_ms', 5000) / 1000))
        self._usage_db = "usage_stats.db"
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600
        self._write_buffer = []
        self._buffer_size = 100
        self._last_flush = time.time()
        self._flush_interval = 300
        self._monitored_set = None  # кэш множества целевых процессов (lowercase)
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

    def _get_monitored_set(self):
        """Возвращает множество имён процессов в lowercase для быстрого сравнения."""
        procs = self.settings.get("processes", []) or []
        try:
            return set(p.strip().lower() for p in procs if p and isinstance(p, str))
        except Exception:
            return set()

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

    # --- Aggregations for per-game details ---
    def get_usage_by_process(self, date=None):
        """Возвращает словарь {process_name: seconds} за указанный день (по умолчанию сегодня)."""
        if date is None:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date, '%Y-%m-%d').date() if isinstance(date, str) else date
        result = {}
        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT process_name, SUM(duration) as total
                    FROM usage_stats
                    WHERE date(timestamp) = ?
                    GROUP BY process_name
                ''', (date.strftime('%Y-%m-%d'),))
                for name, total in cursor.fetchall():
                    result[name] = int(total or 0)
        except Exception as e:
            self.logger.error(f"Error getting usage by process: {e}")
        return result

    def get_usage_by_process_range(self, start_date, end_date=None):
        """Возвращает словарь {process_name: seconds} за период [start_date, end_date).
        Если end_date не указан, берется start_date + 7 дней.
        Принимает даты как date или 'YYYY-MM-DD'.
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        result = {}
        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT process_name, SUM(duration) as total
                    FROM usage_stats
                    WHERE date(timestamp) >= ? AND date(timestamp) < ?
                    GROUP BY process_name
                ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                for name, total in cursor.fetchall():
                    result[name] = int(total or 0)
        except Exception as e:
            self.logger.error(f"Error getting usage by process range: {e}")
        return result

    def get_last_seen_and_sessions(self, start_date=None, end_date=None, gap_minutes=15):
        """Эвристически вычисляет последнее появление и число сессий по процессам за период.
        Сессия считается прерванной, если между соседними записями > gap_minutes.
        Возвращает словарь: {proc: {last_seen: 'YYYY-MM-DD HH:MM:SS', sessions: int}}
        """
        if start_date is None:
            start_date = datetime.now().date()
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date is None:
            end_date = start_date + timedelta(days=1)
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        info = {}
        try:
            with sqlite3.connect(self._usage_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT process_name, timestamp
                    FROM usage_stats
                    WHERE date(timestamp) >= ? AND date(timestamp) < ?
                    ORDER BY process_name, timestamp
                ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                rows = cursor.fetchall()
            from collections import defaultdict
            grouped = defaultdict(list)
            for name, ts in rows:
                grouped[name].append(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S'))
            for name, times in grouped.items():
                sessions = 0
                prev = None
                for t in times:
                    if prev is None or (t - prev).total_seconds() > gap_minutes * 60:
                        sessions += 1
                    prev = t
                info[name] = {
                    'last_seen': times[-1].strftime('%Y-%m-%d %H:%M:%S') if times else None,
                    'sessions': sessions
                }
        except Exception as e:
            self.logger.error(f"Error computing last_seen/sessions: {e}")
        return info

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
        """Проверяет, запущен ли хотя бы один из отслеживаемых процессов (быстро через пересечение множеств)."""
        monitored = self._get_monitored_set()
        if not monitored:
            return False
        active = set(self.get_active_processes())
        if active & monitored:
            return True
        # Если прямого совпадения по имени нет, делаем более дорогую проверку по путям (редкий случай)
        for name in monitored:
            if self.is_process_running(name):
                return True
        return False


    def is_process_running(self, process_name):
        """Проверяет, запущен ли указанный процесс. Сначала по кэшу имён, затем (если нужно) по путям."""
        process_lower = (process_name or "").lower()
        if not process_lower:
            return False
        # Быстрая проверка по кэшу имён
        if process_lower in self._cache:
            return True
        # Медленная проверка по путям
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_info = proc.info
                if not proc_info:
                    continue
                name = (proc_info.get('name') or '').lower()
                exe = (proc_info.get('exe') or '').lower()
                if process_lower in name or (exe and process_lower in exe):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
