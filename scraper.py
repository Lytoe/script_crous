import os
import requests
from bs4 import BeautifulSoup

# Secrets fetched from GitHub Actions environment
TELEGRAM_BOT_TOKEN = os.environ.get("bot8800179716:AAHGRrOaPm5hV_-8GCDF3Gcfdy4ioJED-DE")
TELEGRAM_CHAT_ID = os.environ.get("8888921047")
MAX_PRICE = 400.0

URL = "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=6.134292_48.7092349_6.2126188_48.666906&locationName=Nancy+%2854000%29"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_alert(message):
    telegram_url = f"https://api.telegram.org/bot{Tbot8800179716:AAHGRrOaPm5hV_-8GCDF3Gcfdy4ioJED-DE}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(telegram_url, json=payload)

def main():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    matches = []

    # Find all anchor tags linking to specific accommodations
    for a_tag in soup.find_all('a', href=True):
        if '/accommodations/' in a_tag['href']:
            # Walk up the DOM to the parent list item containing both title and price
            container = a_tag.find_parent('li')
            if not container:
                continue
            
            # Find the text node containing the Euro symbol
            price_node = container.find(string=lambda t: t and '€' in t)
            if price_node:
                # Clean French number formatting (e.g., "350,50 €" -> 350.50)
                raw_price = price_node.replace('€', '').replace(',', '.').replace(' ', '').strip()
                try:
                    price = float(raw_price)
                    if price < MAX_PRICE:
                        name = a_tag.text.strip()
                        link = f"https://trouverunlogement.lescrous.fr{a_tag['href']}"
                        matches.append(f"✅ <b>{name}</b>\n💰 {price}€\n🔗 <a href='{link}'>Voir le logement</a>")
                except ValueError:
                    continue

    if matches:
        # Deduplicate matches (in case DOM has duplicate links for image + text)
        unique_matches = list(set(matches))
        message = f"🚨 <b>{len(unique_matches)} Logement(s) CROUS sous {MAX_PRICE}€ à Nancy!</b>\n\n" + "\n\n".join(unique_matches)
        send_alert(message)
    else:
        print("No housing found under budget.")

if __name__ == "__main__":
    main()