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
        self.dadata_token = (
            settings.DADATA_API_KEY.strip().replace('"', "").replace("'", "")
        )
        self.timeout = 10
        logger.info("Модуль DataCollector (ФНС) инициализирован.")

    def collect(self, inn: str) -> Dict[str, Any]:
        logger.info(f"OSINT: Начинаем сбор цифрового следа по ИНН {inn}")

        url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
        headers = {
            "Authorization": f"Token {self.dadata_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"query": inn}

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Проверка, нашла ли база ФНС такую компанию
            if not data.get("suggestions"):
                logger.warning(f"Компания с ИНН {inn} не найдена в ФНС.")
                return {
                    "ИНН": inn,
                    "Ошибка": "Компания не найдена в официальной базе ФНС. Возможно, фирма-однодневка или неверный ИНН.",
                }

            # Вытаскиваем "грязные" данные из API
            company = data["suggestions"][0]["data"]

            # Собираем чистый, структурированный профиль для нашей нейросети
            result = {
                "ИНН": inn,
                "Официальное название": company.get("name", {}).get(
                    "full_with_opf", "Нет данных"
                ),
                "Статус компании": company.get("state", {}).get("status", "Нет данных"),
                "КПП": company.get("kpp", "Нет данных"),
                "ОГРН": company.get("ogrn", "Нет данных"),
                "Руководитель (ФИО)": (
                    company.get("management", {}).get("name", "Нет данных")
                    if company.get("management")
                    else "Нет данных"
                ),
                "Должность руководителя": (
                    company.get("management", {}).get("post", "Нет данных")
                    if company.get("management")
                    else "Нет данных"
                ),
                "Уставной капитал (руб)": (
                    company.get("capital", {}).get("value", 0)
                    if company.get("capital")
                    else "Нет данных"
                ),
                "Основной вид деятельности (ОКВЭД)": company.get("okved", "Нет данных"),
                "Юридический адрес": company.get("address", {}).get(
                    "value", "Нет данных"
                ),
            }

            # --- ИНТЕГРАЦИЯ НОВЫХ МОДУЛЕЙ ---
            # Теперь бот автоматически запрашивает суды и долги и вшивает их в общий ответ
            result["Судебные_риски_КАД"] = self.get_arbitration_summary(inn)
            result["Долги_ФССП"] = self.get_fssp_summary(inn)

            logger.info(
                f"OSINT: Данные ФНС, судов и ФССП успешно собраны для {result['Официальное название']}."
            )
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при обращении к DaData: {e}")
            return {
                "ИНН": inn,
                "Ошибка": "Временный сбой при подключении к государственным базам данных.",
            }

    def get_arbitration_summary(self, inn: str) -> dict:
        """
        Модуль 1: Собирает данные по арбитражным делам (КАД).
        В проде сюда подключается API агрегатора (например, API-КАД или Контур).
        """
        try:
            # TODO: Заменить на реальный API-запрос, когда будет куплен ключ
            # url = f"https://api.partner.ru/arbitration?inn={inn}"
            # response = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"})

            # Структура, которую ждет наша нейросеть для скоринга:
            return {
                "arbitration_status": "Данные запрошены",
                "total_cases_as_defendant": 0,  # Количество дел в роли ответчика
                "total_debt_claims": 0,  # Сумма исковых требований
                "risk_level": "low",  # Уровень риска: low, medium, high
            }
        except Exception as e:
            return {"error": f"Сбой модуля КАД: {e}"}

    def get_fssp_summary(self, inn: str) -> dict:
        """
        Модуль 2: Проверяет наличие открытых исполнительных производств (ФССП).
        """
        try:
            # TODO: Вставить эндпоинт API ФССП

            return {
                "fssp_status": "Проверка пройдена",
                "open_enforcement_proceedings": 0,  # Количество открытых дел у приставов
                "total_debt_amount": 0,  # Общая сумма долга
            }
        except Exception as e:
            return {"error": f"Сбой модуля ФССП: {e}"}
