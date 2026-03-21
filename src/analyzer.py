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
        self.api_key = settings.OPENROUTER_API_KEY.strip().replace('"', '').replace("'", "")
        logger.info("Архитектура OpenRouter инициализирована. Ключ в безопасности.")

    def analyze(self, company_data: Dict[str, Any]) -> str:
        logger.info("Отправка данных на скоринг...")
        
        # Универсальный Endpoint (стандарт OpenAI), который понимают все системы
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/WR310", # Требование OpenRouter
            "X-Title": "OSINT-Contractor-Scoring"       # Требование OpenRouter
        }
        
        prompt = f"""
        Ты — аналитик службы безопасности B2B-сектора. 
        Проведи OSINT-анализ контрагента.
        
        Данные:
        {company_data}
        
        Выведи жесткий бизнес-отчет:
        📊 СКОРИНГ РИСКА: [1-10]
        🚩 КРАСНЫЕ ФЛАГИ: [список]
        ✅ ПОЗИТИВНЫЕ ФАКТОРЫ: [список]
        ⚖️ ИТОГОВЫЙ ВЕРДИКТ: [Рекомендация: работать или нет]
        """
        
        # Меняя строчку 'model', мы можем переключаться между ChatGPT, Claude и Gemini за секунду
        payload = {
            "model": "openrouter/free", 
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info("Отчет успешно получен.")
                return response.json()['choices'][0]['message']['content']
            else:
                logger.error(f"Ошибка API агрегатора: {response.status_code} - {response.text}")
                return f"❌ Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Сетевая ошибка: {e}")
            return f"❌ Произошла сетевая ошибка: {str(e)}"