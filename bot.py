import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Подключаем наш готовый ИИ-движок
from src.analyzer import RiskAnalyzer
from src.collector import DataCollector

# Загружаем переменные окружения из .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ БЕЗОПАСНОСТИ ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = [1652878568]  # Твой Telegram ID для закрытого доступа

if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: Токен Telegram-бота не найден в файле .env!")

# Инициализируем компоненты
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
analyzer = RiskAnalyzer()
collector = DataCollector()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Реакция на команду /start с проверкой доступа."""
    if message.from_user.id not in ALLOWED_USERS:
        logger.warning(f"Несанкционированный доступ от ID: {message.from_user.id}")
        await message.answer(
            "⛔️ **Доступ запрещен.**\n\nЭто закрытая корпоративная система OSINT-скоринга контрагентов. Для приобретения доступа обратитесь к администратору: @salomaWR."
        )
        return

    await message.answer(
        "🕵️‍♂️ **OSINT Contractor Scoring System**\n\n"
        "Система искусственного интеллекта готова к работе. Отправьте мне ИНН компании (10 или 12 цифр), и я выдам полный аудиторский отчет."
    )


@dp.message(F.text)
async def process_inn(message: Message):
    """Принимаем ИНН и запускаем аналитику с защитой от лимитов Telegram."""
    if message.from_user.id not in ALLOWED_USERS:
        return

    inn = message.text.strip()

    if not inn.isdigit() or len(inn) not in (10, 12):
        await message.answer("⚠️ Ошибка: ИНН должен состоять из 10 или 12 цифр.")
        return

    status_msg = await message.answer(
        f"⏳ Начинаю сбор данных по ИНН `{inn}`...\n\n[1/2] Собираю цифровой след из баз данных..."
    )

    try:
        # Собираем реальные данные (ФНС + суды + долги)
        company_data = await asyncio.to_thread(collector.collect, inn)

        # Если вернулась ошибка от сборщика (например, ИНН не найден)
        if "Ошибка" in company_data:
            await status_msg.edit_text(
                f"❌ **Сбой при поиске:**\n{company_data['Ошибка']}"
            )
            return

        await status_msg.edit_text(
            f"🧠 [2/2] Данные собраны.\n\nПередаю в нейросеть (OpenRouter Balancer) для оценки рисков. Пожалуйста, подождите..."
        )

        report = await asyncio.to_thread(analyzer.analyze, company_data)

        # --- ИНЖЕНЕРНОЕ РЕШЕНИЕ ПРОТИВ ЛИМИТОВ TELEGRAM ---
        full_text = f"📄 **РЕЗУЛЬТАТ АУДИТА:**\n\n{report}"
        max_length = 4000  # Берем с запасом до 4096

        if len(full_text) <= max_length:
            # Если влезает - обновляем наше старое сообщение
            await status_msg.edit_text(full_text)
        else:
            # Если отчет гигантский - первое сообщение обновляем, остальные шлем вдогонку
            await status_msg.edit_text(full_text[:max_length])
            for i in range(max_length, len(full_text), max_length):
                await message.answer(full_text[i : i + max_length])

    except Exception as e:
        logger.error(f"Сбой при обработке ИНН {inn}: {e}")
        await status_msg.edit_text(
            "❌ Произошла внутренняя ошибка при формировании отчета."
        )


async def main():
    logger.info("Запуск Telegram-бота OSINT Scoring...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запуск асинхронного цикла
    asyncio.run(main())
