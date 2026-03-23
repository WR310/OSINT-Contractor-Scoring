import logging
import requests
from typing import Dict, Any
from src.config import settings

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Отказоустойчивый класс для работы с LLM через балансировщик OpenRouter.
    Обеспечивает доступ без VPN и позволяет менять нейросети "на лету".
    """

    from src.config import settings


class RiskAnalyzer:
    """
    Отказоустойчивый класс для работы с LLM через балансировщик OpenRouter.
    """

    def __init__(self):
        # Безопасно достаем ключ из переменных окружения и чистим от мусора Windows
        self.api_key = (
            settings.OPENROUTER_API_KEY.strip().replace('"', "").replace("'", "")
        )
        logger.info("Архитектура OpenRouter инициализирована. Ключ в безопасности.")

    def analyze(self, company_data: Dict[str, Any]) -> str:
        logger.info("Отправка данных на скоринг...")

        # Универсальный Endpoint (стандарт OpenAI), который понимают все системы
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/WR310",  # Требование OpenRouter
            "X-Title": "OSINT-Contractor-Scoring",  # Требование OpenRouter
        }

        prompt = f"""
        Ты — аналитик службы безопасности B2B-сектора. 
        Проведи OSINT-анализ контрагента.
        
        ОБРАТИ ОСОБОЕ ВНИМАНИЕ НА СУДЕБНЫЕ РИСКИ И ДОЛГИ (КАД и ФССП):
        1. В переданных данных теперь есть разделы "Судебные_риски_КАД" и "Долги_ФССП".
        2. Если открыты исполнительные производства (open_enforcement_proceedings > 0) или есть долги (total_debt_amount > 0) — это КРИТИЧЕСКИЙ КРАСНЫЙ ФЛАГ. Снижай оценку надежности минимум на 3-4 балла.
        3. Обязательно добавь в свой финальный ответ отдельный абзац: "⚖️ Суды и долги (ФССП)", где кратко опиши найденные риски. Если рисков нет, так и напиши: "Судебных обременений не найдено".
        
        Данные:
        {company_data}
        
        ВЫДАЙ ОТВЕТ СТРОГО ПО ЭТОМУ ШАБЛОНУ (сохраняй все переносы строк и эмодзи):

        📊 СКОРИНГ РИСКА: [Оценка] / 10

        🚩 КРАСНЫЕ ФЛАГИ:
        - [Флаг 1]
        - [Флаг 2]

        ✅ ПОЗИТИВНЫЕ ФАКТОРЫ:
        - [Фактор 1]
        - [Фактор 2]

        ⚖️ СУДЫ И ДОЛГИ (ФССП):
        - [Проанализируй данные из блоков Судебные_риски_КАД и Долги_ФССП. Обязательно выведи этот блок! Если там нули, напиши: "Судебных обременений и открытых долгов ФССП не обнаружено. Риск минимальный."]

        ⚖️ ИТОГОВЫЙ ВЕРДИКТ:
        - [Твой вывод]
        """

        # Меняя строчку 'model', мы можем переключаться между ChatGPT, Claude и Gemini за секунду
        payload = {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                logger.info("Отчет успешно получен.")
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(
                    f"Ошибка API агрегатора: {response.status_code} - {response.text}"
                )
                return f"❌ Ошибка API: {response.status_code}"

        except Exception as e:
            logger.error(f"Сетевая ошибка: {e}")
            return f"❌ Произошла сетевая ошибка: {str(e)}"
