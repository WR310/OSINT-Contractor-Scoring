import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Имитация сбора данных из открытых источников (OSINT).
    """
    
    def get_company_data(self, inn: str) -> Dict[str, Any]:
        logger.info(f"Запрос данных по ИНН: {inn}...")
        
        # Имитируем ответ от системы мониторинга (Контур.Фокус, ФНС и т.д.)
        mock_data = {
            "company_name": "ООО 'СтройМонтажХолдинг'",
            "inn": inn,
            "founded_year": 2023, 
            "authorized_capital": 10000, 
            "arbitration_cases": [
                {"type": "ответчик", "amount": 1500000, "status": "в процессе"},
                {"type": "истец", "amount": 200000, "status": "завершено"}
            ],
            "tax_debts": 45000,
            "government_contracts": 0,
            "last_year_revenue": "данные отсутствуют"
        }
        
        return mock_data