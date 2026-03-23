import sqlite3
import logging

logger = logging.getLogger(__name__)

# База данных будет лежать в корне проекта
DB_PATH = "osint_bot.db"


def init_db():
    """Создает таблицу пользователей для учета лимитов."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # У каждого юзера по умолчанию 3 бесплатные проверки
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    checks_left INTEGER DEFAULT 3
                )
            """
            )
            conn.commit()
            logger.info("База данных SQLite успешно инициализирована.")
    except Exception as e:
        logger.error(f"Критическая ошибка при создании БД: {e}")


def get_user_checks(telegram_id: int) -> int:
    """Проверяет баланс пользователя. Если он новый — регистрирует его."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checks_left FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            result = cursor.fetchone()

            if result is None:
                # Регистрируем нового клиента и даем 3 триальные проверки
                cursor.execute(
                    "INSERT INTO users (telegram_id, checks_left) VALUES (?, 3)",
                    (telegram_id,),
                )
                conn.commit()
                return 3
            return result[0]
    except Exception as e:
        logger.error(f"Ошибка чтения из БД: {e}")
        return 0  # При сбое лучше заблокировать доступ, чем отдавать запросы бесплатно


def decrement_checks(telegram_id: int):
    """Списывает одну проверку с баланса."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET checks_left = checks_left - 1 
                WHERE telegram_id = ? AND checks_left > 0
            """,
                (telegram_id,),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при списании лимита: {e}")


def add_checks_to_user(telegram_id: int, amount: int):
    """Ручное начисление проверок клиенту."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checks_left FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO users (telegram_id, checks_left) VALUES (?, ?)",
                    (telegram_id, amount),
                )
            else:
                cursor.execute(
                    "UPDATE users SET checks_left = checks_left + ? WHERE telegram_id = ?",
                    (amount, telegram_id),
                )
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при начислении лимита: {e}")
