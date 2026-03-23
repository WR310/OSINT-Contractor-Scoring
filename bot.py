import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.analyzer import RiskAnalyzer
from src.collector import DataCollector
from src.database import init_db, get_user_checks, decrement_checks, add_checks_to_user

# Загружаем переменные окружения из .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ БЕЗОПАСНОСТИ И БИЗНЕС-ЛОГИКИ ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 1652878568  # Твой ID для безлимитного доступа

if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: Токен Telegram-бота не найден в файле .env!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
analyzer = RiskAnalyzer()
collector = DataCollector()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Реакция на команду /start с проверкой лимитов."""
    telegram_id = message.from_user.id
    checks = get_user_checks(telegram_id)

    # Если это ты, показываем статус владельца
    if telegram_id == ADMIN_ID:
        await message.answer(
            "👑 **Добро пожаловать, Администратор!**\n\n"
            "Система OSINT-скоринга готова. У вас безлимитный доступ."
        )
        return

    # Для обычных клиентов показываем счетчик
    await message.answer(
        "🕵️‍♂️ **OSINT Contractor Scoring System**\n\n"
        "Система искусственного интеллекта готова к работе. Отправьте мне ИНН компании (10 или 12 цифр).\n\n"
        f"🎁 Доступно бесплатных проверок: **{checks}**"
    )


@dp.message(Command("add_limit"))
async def cmd_add_limit(message: Message):
    """Секретная команда админа: /add_limit <id> <количество>"""
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("⚠️ Формат: `/add_limit <telegram_id> <количество>`")
        return

    try:
        target_id = int(args[1])
        amount = int(args[2])
        add_checks_to_user(target_id, amount)
        await message.answer(
            f"✅ Баланс пользователя {target_id} пополнен на {amount} проверок."
        )
    except ValueError:
        await message.answer("⚠️ Ошибка: ID и количество должны быть числами.")


@dp.message(F.text)
async def process_inn(message: Message):
    """Принимаем ИНН, проверяем баланс и запускаем аналитику."""
    telegram_id = message.from_user.id
    inn = message.text.strip()

    if not inn.isdigit() or len(inn) not in (10, 12):
        await message.answer("⚠️ Ошибка: ИНН должен состоять из 10 или 12 цифр.")
        return

    # Проверка баланса (админа пропускаем без проверки)
    if telegram_id != ADMIN_ID:
        checks = get_user_checks(telegram_id)
        if checks <= 0:
            # Генерируем красивую Inline-кнопку для оплаты
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💳 Оплатить безлимит", url="https://t.me/salomaWR"
                        )
                    ]
                ]
            )
            await message.answer(
                "⛔️ **Лимит бесплатных проверок исчерпан.**\n\n"
                "Для продолжения работы и безлимитного доступа к OSINT-аналитике, оформите Premium-подписку.",
                reply_markup=kb,
            )
            return

    status_msg = await message.answer(
        f"⏳ Начинаю сбор данных по ИНН `{inn}`...\n\n[1/2] Собираю цифровой след из баз данных..."
    )

    try:
        company_data = await asyncio.to_thread(collector.collect, inn)

        if "Ошибка" in company_data:
            await status_msg.edit_text(
                f"❌ **Сбой при поиске:**\n{company_data['Ошибка']}"
            )
            return

        await status_msg.edit_text(
            "🧠 [2/2] Данные собраны.\n\nПередаю в нейросеть (OpenRouter Balancer) для оценки рисков. Пожалуйста, подождите..."
        )

        report = await asyncio.to_thread(analyzer.analyze, company_data)

        # Списываем 1 проверку только после успешного отчета (чтобы не списывать за ошибки ФНС)
        if telegram_id != ADMIN_ID:
            decrement_checks(telegram_id)
            checks_left = get_user_checks(telegram_id)
            footer = f"\n\n---\n📉 Осталось бесплатных проверок: **{checks_left}**"
        else:
            footer = f"\n\n---\n👑 *Безлимитный режим*"

        full_text = f"📄 **РЕЗУЛЬТАТ АУДИТА:**\n\n{report}{footer}"
        max_length = 4000

        if len(full_text) <= max_length:
            await status_msg.edit_text(full_text)
        else:
            await status_msg.edit_text(full_text[:max_length])
            for i in range(max_length, len(full_text), max_length):
                await message.answer(full_text[i : i + max_length])

    except Exception as e:
        logger.error(f"Сбой при обработке ИНН {inn}: {e}")
        await status_msg.edit_text(
            "❌ Произошла внутренняя ошибка при формировании отчета."
        )


async def main():
    # Обязательно создаем файл базы данных при старте
    init_db()
    logger.info("Запуск Telegram-бота OSINT Scoring...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
