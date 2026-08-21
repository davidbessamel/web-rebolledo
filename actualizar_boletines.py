import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuración de Telegram desde variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # Ej: @rebolledodetorrenoticias

HISTORIAL_ENVIADOS = "enviados_telegram.txt"
JSON_OUTPUT = "publicaciones_oficiales.json"

KEYWORDS_LOCAL = ["rebolledo de la torre", "valdeolea", "peña amaya", "humada", "aguilar de campoo"]
KEYWORDS_GENERAL = ["subvencion", "subvenciones", "ayuda", "despoblacion", "desarrollo rural", "explotacion agraria", "patrimonio historico"]

def cargar_enviados():
    if not os.path.exists(HISTORIAL_ENVIADOS):
        return set()
    with open(HISTORIAL_ENVIADOS, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def registrar_enviado(enlace):
    with open(HISTORIAL_ENVIADOS, "a", encoding="utf-8") as f:
        f.write(f"{enlace}\n")

def enviar_telegram(pub):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Configuración de Telegram omitida (variables no definidas).")
        return

    mensaje = (
        f"🚨 *ALERTA OFICIAL: REBOLLEDO DE LA TORRE*\n\n"
        f"📌 *{pub['origen']}* - Prioridad Alta\n"
        f"📜 *{pub['titulo']}*\n\n"
        f"📝 {pub['resumen']}\n\n"
        f"🔗 [Consultar disposición en PDF]({pub['enlace']})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print(f" Envio exitoso a Telegram: {pub['titulo'][:30]}...")
        else:
            print(f"⚠️ Error Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Error conectando a Telegram: {e}")

def procesar_rss(url, origen):
    publicaciones = []
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""

                texto_completo = f"{title} {desc}".lower()
                is_local = any(k in texto_completo for k in KEYWORDS_LOCAL)
                is_general = any(k in texto_completo for k in KEYWORDS_GENERAL)

                if is_local or is_general:
                    publicaciones.append({
                        "origen": origen,
                        "titulo": title,
                        "resumen": desc[:220] + "..." if len(desc) > 220 else desc,
                        "enlace": link,
                        "prioridad": "Alta" if is_local else "Media",
                        "fecha": datetime.now().strftime("%Y-%m-%d")
                    })
    except Exception as e:
        print(f"Error procesando {origen}: {e}")
    return publicaciones

def main():
    enviados = cargar_enviados()
    todas_pub = []

    # Canales RSS oficiales
    todas_pub.extend(procesar_rss("https://bocyl.jcyl.es/rss/sumario.xml", "BOCyL"))
    todas_pub.extend(procesar_rss("https://www.boe.es/rss/canal.php?c=1", "BOE"))

    # Actualizar JSON para la web
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(todas_pub, f, ensure_ascii=False, indent=2)

    # Notificar alertas de alta prioridad por Telegram
    for pub in todas_pub:
        if pub["prioridad"] == "Alta" and pub["enlace"] not in enviados:
            enviar_telegram(pub)
            registrar_enviado(pub["enlace"])

if __name__ == "__main__":
    main()
