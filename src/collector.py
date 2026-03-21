import logging
import requests
from typing import Dict, Any
from src.config import settings

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Боевой модуль OSINT-сбора данных.
    Интеграция с API DaData (официальные данные ФНС).
    """
    def __init__(self):
        # Безопасно достаем ключ
        self.dadata_token = settings.DADATA_API_KEY.strip().replace('"', '').replace("'", "")
        self.timeout = 10
        logger.info("Модуль DataCollector (ФНС) инициализирован.")

    def collect(self, inn: str) -> Dict[str, Any]:
        logger.info(f"OSINT: Начинаем сбор цифрового следа по ИНН {inn}")
        
        url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
        headers = {
            "Authorization": f"Token {self.dadata_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {"query": inn}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Проверка, нашла ли база ФНС такую компанию
            if not data.get("suggestions"):
                logger.warning(f"Компания с ИНН {inn} не найдена в ФНС.")
                return {"ИНН": inn, "Ошибка": "Компания не найдена в официальной базе ФНС. Возможно, фирма-однодневка или неверный ИНН."}

            # Вытаскиваем "грязные" данные из API
            company = data["suggestions"][0]["data"]
            
            # Собираем чистый, структурированный профиль для нашей нейросети
            result = {
                "ИНН": inn,
                "Официальное название": company.get("name", {}).get("full_with_opf", "Нет данных"),
                "Статус компании": company.get("state", {}).get("status", "Нет данных"),
                "КПП": company.get("kpp", "Нет данных"),
                "ОГРН": company.get("ogrn", "Нет данных"),
                "Руководитель (ФИО)": company.get("management", {}).get("name", "Нет данных") if company.get("management") else "Нет данных",
                "Должность руководителя": company.get("management", {}).get("post", "Нет данных") if company.get("management") else "Нет данных",
                "Уставной капитал (руб)": company.get("capital", {}).get("value", 0) if company.get("capital") else "Нет данных",
                "Основной вид деятельности (ОКВЭД)": company.get("okved", "Нет данных"),
                "Юридический адрес": company.get("address", {}).get("value", "Нет данных")
            }
            
            logger.info(f"OSINT: Данные ФНС успешно получены для {result['Официальное название']}.")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при обращении к DaData: {e}")
            return {"ИНН": inn, "Ошибка": "Временный сбой при подключении к государственным базам данных."}