import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# The specific residences you want to target (lowercase for easier matching)
TARGET_RESIDENCES = ["monbois", "boudonville"]

URL = "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=6.134292_48.7092349_6.2126188_48.666906&locationName=Nancy+%2854000%29"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def send_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram secrets.")
        return
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID,
               "text": message, "parse_mode": "HTML"}
    requests.post(telegram_url, json=payload)


def main():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        # Force UTF-8 to prevent mangled Euro symbols
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Target housing cards directly
    cards = soup.find_all(
        class_=lambda c: c and 'fr-card' in c) or soup.find_all('li')
    matches = []

    for card in cards:
        price_node = card.find(string=lambda t: t and '€' in t)
        link_node = card.find(
            'a', href=lambda h: h and '/accommodations/' in h)

        if price_node and link_node:
            raw_text = str(price_node)
            clean_price = (
                raw_text.replace('€', '')
                .replace('\xa0', '')
                .replace(' ', '')
                .replace(',', '.')
                .strip()
            )
            try:
                price = float(clean_price)
                title = link_node.text.strip() or "Logement CROUS"
                link = f"https://trouverunlogement.lescrous.fr{link_node['href']}"

                # Check if the title matches our target residences
                title_lower = title.lower()
                is_target = any(
                    residence in title_lower for residence in TARGET_RESIDENCES)

                # If it's Monbois, Monbois Libération, or Boudonville, add it to matches
                if is_target:
                    matches.append(
                        f"✅ <b>{title}</b>\n💰 {price}€\n🔗 <a href='{link}'>Voir le logement</a>")
            except ValueError:
                continue

    if matches:
        unique_matches = list(set(matches))
        message = f"🚨 <b>{len(unique_matches)} Logement(s) Monbois/Boudonville dispo(s)!</b>\n\n" + \
            "\n\n".join(unique_matches)
        send_alert(message)
        print("Alert sent to Telegram!")
    else:
        print("No target housing found (Monbois, Boudonville).")


if __name__ == "__main__":
    main()
