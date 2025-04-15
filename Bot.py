import requests
import time
from flask import Flask
import threading

# === CONFIG ===
BOT_TOKEN = "7622828941:AAH5--aI5hfGKli0IvHlq3_5l3KFa7zsBz4"
API_KEY = "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"  # Neuer API-Key
MODEL = "gpt-3.5-turbo"  # Neuer Modellname

# Variable, um den Bot zu steuern
bot_active = True  # Der Bot ist standardmäßig aktiv


# === Telegram Funktionen ===
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        res = requests.post(url, data=data)
        if res.ok:
            return res.json()["result"]["message_id"]
    except Exception as e:
        print("Fehler beim Senden:", e)
    return None


def get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 10, "offset": offset}
    try:
        res = requests.get(url, params=params).json()
        if res["ok"]:
            return res["result"]
    except Exception as e:
        print("Fehler beim Empfangen:", e)
    return []


# === KI Antwort via OpenRouter ===
def ask_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{
            "role": "system",
            "content": "Du bist ein hilfreicher Assistent."
        }, {
            "role": "user",
            "content": prompt
        }]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=data)
        res.raise_for_status()  # Wenn der Statuscode nicht OK ist, wird eine Ausnahme ausgelöst
        response_data = res.json()
        return response_data['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        print(f"API-Fehler: {e}")
        return "❌ Fehler bei der KI-Antwort"


# === Befehlsfunktionen ===
def handle_command(chat_id, user_msg):
    global bot_active  # Zugriff auf die globale Variable bot_active

    if user_msg.startswith('/reset'):
        send_telegram(chat_id, "🔄 Der Bot wird zurückgesetzt!")
    elif user_msg.startswith('/zeit'):
        send_telegram(chat_id, time.strftime("%Y-%m-%d %H:%M:%S"))
    elif user_msg.startswith('/info'):
        send_telegram(
            chat_id,
            "🤖 Dies ist ein KI-Bot, der mit OpenRouter verbunden ist. Bitte stellen Sie Ihre Fragen!"
        )
    elif user_msg.startswith('/mathe'):
        send_telegram(
            chat_id,
            "🔢 Mathematik-Aufgaben werden hier bearbeitet. Geben Sie eine Aufgabe ein!"
        )
    elif user_msg.startswith('///off'):
        send_telegram(chat_id, "🛑 Der Bot wurde gestoppt.")
        bot_active = False  # Deaktiviert den Bot
    elif user_msg.startswith('///on'):
        send_telegram(chat_id, "✅ Der Bot wurde wieder aktiviert.")
        bot_active = True  # Aktiviert den Bot wieder
    elif user_msg.startswith('/help'):
        send_telegram(
            chat_id, """
        ✨ Verfügbare Befehle:
        /reset  - Setzt den Bot zurück
        /zeit   - Zeigt die aktuelle Zeit
        /info   - Zeigt Informationen über den Bot
        /mathe  - Für Mathematik-Aufgaben
        ///off   - Stoppt den Bot
        ///on    - Aktiviert den Bot wieder
        """)
    else:
        return False  # Kein Kommando, also lasse den Bot antworten
    return True


# === Funktion für das regelmäßige "Ping" an den Webserver ===
def keep_alive():
    while True:
        try:
            # Hier kannst du deinen Webserver regelmäßig pingen, um die Aktivität zu behalten
            time.sleep(30 * 60)  # Ping alle 30 Minuten (z.B. bei Replit, um den Timeout zu vermeiden)
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Pingen: {e}")
            time.sleep(60)  # Falls ein Fehler auftritt, warte eine Minute und versuche es erneut


# === Hauptloop für Telegram-Updates ===
def main():
    offset = 0
    print("🤖 KI-Bot läuft...")

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1

            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                user_msg = update["message"]["text"]
                print(f"[{chat_id}] Nutzer: {user_msg}")

                if not bot_active:
                    continue  # Wenn der Bot nicht aktiv ist, ignoriere alle Nachrichten

                # Wenn der Nutzer einen Befehl sendet, behandeln wir diesen
                if handle_command(chat_id, user_msg):
                    continue

                # Andernfalls antwortet die KI
                response = ask_openrouter(user_msg)
                send_telegram(chat_id, response)

        time.sleep(1)


# === Start des Programms ===
if __name__ == "__main__":
    # Starte den "Ping" Mechanismus in einem eigenen Thread (Falls nötig)
    threading.Thread(target=keep_alive).start()

    # Starte den Telegram-Bot
    main()
