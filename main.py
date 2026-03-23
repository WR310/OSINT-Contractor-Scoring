import logging
from dotenv import load_dotenv
from src.collector import DataCollector
from src.analyzer import RiskAnalyzer

# Загружаем переменные из .env
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    print("=" * 50)
    print(" 🕵️‍♂️ OSINT Contractor Scoring System (AI Powered)")
    print("=" * 50)

    inn = input("\nВведите ИНН компании для проверки (или нажмите Enter для теста): ")
    if not inn:
        inn = "7736326159"  # Тестовый ИНН

    print("\n[1/2] Собираем цифровой след компании...")
    collector = DataCollector()
    raw_data = collector.collect(inn)

    print("\n[2/2] Передаем данные ИИ-аналитику для оценки рисков...\n")
    analyzer = RiskAnalyzer()
    report = analyzer.analyze(raw_data)

    print("=" * 50)
    print(" 📄 РЕЗУЛЬТАТЫ АУДИТА КОНТРАГЕНТА")
    print("=" * 50)
    print(report)
    print("=" * 50)


if __name__ == "__main__":
    main()
