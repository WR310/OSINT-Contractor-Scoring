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
        2. Если открыты исполнительные производства (open_enforcement_proceedings > 0) или есть долги (total_debt_amount > 0) — это КРИТИЧЕСКИЙ КРАСНЫЙ ФЛАГ. Жестко снижай Индекс надежности до 1-3 баллов.
        
        Данные:
        {company_data}
        
        ВЫДАЙ ОТВЕТ СТРОГО ПО ЭТОМУ ШАБЛОНУ. 
        ОЧЕНЬ ВАЖНО: Делай двойной перенос строки (Enter) перед каждым новым блоком, чтобы текст не слипался!
        ШКАЛА НАДЕЖНОСТИ: 10 - идеальная компания (надежный партнер, риск минимален), 1 - мошенники или банкроты (опасность).

        📊 ИНДЕКС НАДЕЖНОСТИ: [Укажи цифру от 1 до 10] / 10

        🚩 КРАСНЫЕ ФЛАГИ:
        [Если негативных факторов нет, строго напиши "Не обнаружено". Если есть - перечисли через дефис, каждый с новой строки]

        ✅ ПОЗИТИВНЫЕ ФАКТОРЫ:
        [Перечисли факторы надежности через дефис, каждый с новой строки]

        ⚖️ СУДЫ И ДОЛГИ (ФССП):
        [Проанализируй данные КАД и ФССП. Если там нули, напиши: "Судебных обременений и открытых долгов ФССП не обнаружено."]

        📋 ИТОГОВЫЙ ВЕРДИКТ:
        [Твой краткий вывод: можно ли работать с этим контрагентом]
        """

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
