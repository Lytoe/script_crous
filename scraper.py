import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Updated URL for Île-de-France
URL = "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=1.4462445_49.241431_3.5592208_48.1201456&locationName=%C3%8Ele-de-France"
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

        # Extract size from the specific <p> tag containing "m²"
        size_node = None
        for p in card.find_all('p', class_='fr-card__detail'):
            if 'm²' in p.text:
                size_node = p
                break

        if price_node and link_node and size_node:
            # Clean and format price
            raw_price = str(price_node)
            clean_price = (
                raw_price.replace('€', '')
                .replace('\xa0', '')
                .replace(' ', '')
                .replace(',', '.')
                .strip()
            )

            # Clean and format size
            raw_size = size_node.text.replace(
                'm²', '').replace(',', '.').strip()

            try:
                price = float(clean_price)
                size = float(raw_size)
                title = link_node.text.strip() or "Logement CROUS"
                link = f"https://trouverunlogement.lescrous.fr{link_node['href']}"

                # Apply new filters: Price 200-500€ AND Size 10-20m²
                if 200 <= price <= 500 and 10 <= size <= 20:
                    matches.append(
                        f"✅ <b>{title}</b>\n💰 {price}€ | 📏 {size}m²\n🔗 <a href='{link}'>Voir le logement</a>"
                    )
            except ValueError:
                # Skips card if float conversion fails on weird data
                continue

    if matches:
        unique_matches = list(set(matches))
        message = f"🚨 <b>{len(unique_matches)} Logement(s) en Île-de-France dispo(s)!</b>\n\n" + \
            "\n\n".join(unique_matches)
        send_alert(message)
        print("Alert sent to Telegram!")
    else:
        print("No housing found matching criteria (200-500€, 10-20m²).")


if __name__ == "__main__":
    main()
