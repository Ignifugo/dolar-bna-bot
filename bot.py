import requests
from bs4 import BeautifulSoup
import json
import os
from twilio.rest import Client
from datetime import datetime
import pytz

URL = "https://www.bna.com.ar/Personas"
DATA_FILE = "last_value.json"


def is_business_hours():
    argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now = datetime.now(argentina_tz)
    return 9 <= now.hour < 18


def get_dolar():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.find_all("tr")

    for row in rows:
        if "Dolar U.S.A" in row.text:
            tds = row.find_all("td")
            compra = float(tds[1].text.strip().replace(",", "."))
            venta = float(tds[2].text.strip().replace(",", "."))
            return compra, venta

    return None, None


def load_last():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_last(compra, venta):
    with open(DATA_FILE, "w") as f:
        json.dump({"compra": compra, "venta": venta}, f)


def send_whatsapp(message):
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_='whatsapp:+14155238886',
        to=os.environ["MY_PHONE"]
    )


def main():

    if not is_business_hours():
        print("Fuera de horario")
        return

    compra, venta = get_dolar()
    last = load_last()

    if last is None:
        save_last(compra, venta)
        print("Primer guardado")
        return

    diff_compra = compra - float(last["compra"])
    diff_venta = venta - float(last["venta"])

    if diff_compra != 0 or diff_venta != 0:

        emoji_compra = "📈" if diff_compra > 0 else "📉"
        emoji_venta = "📈" if diff_venta > 0 else "📉"

        message = f"""💵 Cambio en dólar BNA

Compra: {compra:.2f} ({emoji_compra} {abs(diff_compra):.2f})
Venta: {venta:.2f} ({emoji_venta} {abs(diff_venta):.2f})
"""

        send_whatsapp(message)
        save_last(compra, venta)
        print("Cambio detectado y guardado")

    else:
        print("Sin cambios")


if __name__ == "__main__":
    main()
