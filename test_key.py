import requests

# ВСТАВЬ СВОЙ КЛЮЧ СЮДА (внутри кавычек):
API_KEY = "AIzaSyCZia43SPqGiijdN6EA5IDhGaTFt6ZrRi8"

def test_google_api():
    print(f"Тестируем ключ: {API_KEY[:5]}... (длина: {len(API_KEY)})")
    
    # Прямой URL к серверам Google (без библиотек)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    # Простейший промпт
    payload = {
        "contents": [{"parts": [{"text": "Скажи ровно одно слово: 'Работает'"}]}]
    }
    
    print("Отправляем прямой запрос к Google REST API...")
    response = requests.post(url, json=payload)
    
    print("-" * 40)
    print(f"HTTP Статус: {response.status_code}")
    print("-" * 40)
    
    if response.status_code == 200:
        print("✅ УСПЕХ! Ключ 100% рабочий. Значит, проблема в библиотеке google-genai.")
        print("Ответ ИИ:", response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print("❌ ОШИБКА! Google отказывается принимать этот ключ.")
        print("Ответ сервера:", response.text)

if __name__ == "__main__":
    test_google_api()