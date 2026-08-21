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
            print(f"✅ Envío exitoso a Telegram: {pub['titulo'][:30]}...")
        else:
            print(f"⚠️ Error Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Error conectando a Telegram: {e}")

def procesar_rss(url, origen):
    publicaciones = []
    try:
        print(f"📡 Procesando {origen} desde: {url}")
        resp = requests.get(url, timeout=10)
        print(f"   → Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                print(f"   → Encontrados {len(items)} items en el feed")
                
                for i, item in enumerate(items):
                    try:
                        title = item.find("title").text if item.find("title") is not None else ""
                        desc = item.find("description").text if item.find("description") is not None else ""
                        link = item.find("link").text if item.find("link") is not None else ""

                        texto_completo = f"{title} {desc}".lower()
                        is_local = any(k in texto_completo for k in KEYWORDS_LOCAL)
                        is_general = any(k in texto_completo for k in KEYWORDS_GENERAL)

                        if is_local or is_general:
                            pub = {
                                "origen": origen,
                                "titulo": title,
                                "resumen": desc[:220] + "..." if len(desc) > 220 else desc,
                                "enlace": link,
                                "prioridad": "Alta" if is_local else "Media",
                                "fecha": datetime.now().strftime("%Y-%m-%d")
                            }
                            publicaciones.append(pub)
                            print(f"   ✓ Item {i+1}: Relevante - {title[:40]}...")
                    except Exception as e:
                        print(f"   ⚠️ Error procesando item {i+1}: {e}")
                        continue
                
                print(f"   → Total publicaciones relevantes: {len(publicaciones)}")
                
            except ET.ParseError as e:
                print(f"❌ Error parseando XML de {origen}: {e}")
                print(f"   Primeros 200 caracteres de la respuesta: {resp.content[:200]}")
        else:
            print(f"❌ Error HTTP {resp.status_code} para {origen}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout conectando a {origen}")
    except Exception as e:
        print(f"❌ Error procesando {origen}: {e}")
    
    return publicaciones

def main():
    print("=" * 60)
    print("🚀 Iniciando actualización de boletines oficiales")
    print("=" * 60)
    
    enviados = cargar_enviados()
    print(f"📋 Publicaciones previamente enviadas: {len(enviados)}\n")
    
    todas_pub = []

    # Canales RSS oficiales
    print("📰 PROCESANDO FUENTES RSS:")
    print("-" * 60)
    todas_pub.extend(procesar_rss("https://bocyl.jcyl.es/rss/sumario.xml", "BOCyL"))
    print()
    todas_pub.extend(procesar_rss("https://www.boe.es/rss/canal.php?c=1", "BOE"))
    print("-" * 60)
    print(f"\n📊 Total de publicaciones encontradas: {len(todas_pub)}\n")

    # Actualizar JSON para la web
    print(f"💾 Guardando en {JSON_OUTPUT}...")
    try:
        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(todas_pub, f, ensure_ascii=False, indent=2)
        print(f"✅ Archivo JSON actualizado exitosamente")
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return

    # Notificar alertas de alta prioridad por Telegram
    print(f"\n📲 NOTIFICACIONES TELEGRAM:")
    print("-" * 60)
    alertas_enviadas = 0
    for pub in todas_pub:
        if pub["prioridad"] == "Alta" and pub["enlace"] not in enviados:
            enviar_telegram(pub)
            registrar_enviado(pub["enlace"])
            alertas_enviadas += 1
    
    if alertas_enviadas == 0:
        print("ℹ️ No hay nuevas alertas de alta prioridad para notificar")
    else:
        print(f"\n✅ Se enviaron {alertas_enviadas} alertas por Telegram")
    
    print("=" * 60)
    print("✅ Proceso completado exitosamente")
    print("=" * 60)

if __name__ == "__main__":
    main()
