import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuración de Telegram desde variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORIAL_ENVIADOS = "enviados_telegram.txt"
JSON_OUTPUT = "publicaciones_oficiales.json"

KEYWORDS_LOCAL = ["rebolledo de la torre", "valdeolea", "peña amaya", "humada", "aguilar de campoo"]
KEYWORDS_GENERAL = ["subvencion", "subvenciones", "ayuda", "despoblacion", "desarrollo rural", "explotacion agraria", "patrimonio historico"]

# Headers para simular navegador y evitar bloqueos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

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
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Envío exitoso a Telegram: {pub['titulo'][:30]}...")
        else:
            print(f"⚠️ Error Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Error conectando a Telegram: {e}")

def procesar_rss(url, origen):
    publicaciones = []
    try:
        print(f"📡 Procesando {origen}")
        print(f"   URL: {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        print(f"   → HTTP Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Error HTTP {resp.status_code}")
            return publicaciones
        
        # Detectar encoding
        if 'charset' in resp.headers.get('content-type', ''):
            encoding = resp.headers['content-type'].split('charset=')[-1]
            resp.encoding = encoding
        
        print(f"   → Encoding: {resp.encoding}")
        print(f"   → Content length: {len(resp.content)} bytes")
        
        try:
            # Intentar parsear XML
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            print(f"   → Items encontrados: {len(items)}")
            
            for i, item in enumerate(items, 1):
                try:
                    title_elem = item.find("title")
                    desc_elem = item.find("description")
                    link_elem = item.find("link")
                    
                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    link = link_elem.text if link_elem is not None and link_elem.text else ""
                    
                    if not title:
                        continue
                    
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
                        print(f"   ✓ Item {i}: RELEVANTE - {title[:50]}...")
                except Exception as e:
                    print(f"   ⚠️ Error item {i}: {str(e)[:100]}")
                    continue
            
            print(f"   → Total relevantes: {len(publicaciones)}")
            
        except ET.ParseError as e:
            print(f"❌ XML Parse Error: {str(e)}")
            print(f"   Primeros 300 chars: {resp.text[:300]}")
            return publicaciones
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: No respuesta de {origen}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
    
    return publicaciones

def crear_json_fallback(todas_pub):
    """Crea JSON fallback si no hay publicaciones"""
    if not todas_pub:
        print("\n⚠️ Sin publicaciones. Creando archivo de ejemplo...")
        todas_pub = [
            {
                "origen": "BOCyL",
                "titulo": "[EJEMPLO] Subvenciones para patrimonio rural",
                "resumen": "Sistema en mantenimiento. Se actualiza automáticamente cada día a las 08:30 UTC.",
                "enlace": "#",
                "prioridad": "Media",
                "fecha": datetime.now().strftime("%Y-%m-%d")
            }
        ]
    return todas_pub

def main():
    print("\n" + "=" * 70)
    print("🚀 ACTUALIZACIÓN DE BOLETINES OFICIALES")
    print("=" * 70)
    
    enviados = cargar_enviados()
    print(f"📋 Publicaciones previamente enviadas: {len(enviados)}\n")
    
    todas_pub = []

    print("📰 PROCESANDO FUENTES RSS:")
    print("-" * 70)
    
    # BOCyL
    todas_pub.extend(procesar_rss("https://bocyl.jcyl.es/rss/sumario.xml", "BOCyL"))
    print()
    
    # BOE - con URL alternativa si falla
    boe_pubs = procesar_rss("https://www.boe.es/rss/canal.php?c=1", "BOE")
    if not boe_pubs:
        print("⚠️ BOE no respondió. Intentando con URL alternativa...")
        boe_pubs = procesar_rss("https://www.boe.es/rss/canal.php?c=1&s=BOE", "BOE-ALT")
    todas_pub.extend(boe_pubs)
    
    print("-" * 70)
    print(f"\n📊 Total publicaciones recopiladas: {len(todas_pub)}")

    # Fallback si no hay nada
    todas_pub = crear_json_fallback(todas_pub)

    # Guardar JSON
    print(f"\n💾 Guardando en {JSON_OUTPUT}...")
    try:
        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(todas_pub, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON guardado correctamente ({len(todas_pub)} registros)")
        
        # Verificar que se escribió
        if os.path.exists(JSON_OUTPUT):
            size = os.path.getsize(JSON_OUTPUT)
            print(f"✅ Verificado: archivo existe ({size} bytes)")
        
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return False

    # Notificar por Telegram
    print(f"\n📲 NOTIFICACIONES TELEGRAM:")
    print("-" * 70)
    alertas_enviadas = 0
    for pub in todas_pub:
        if pub["prioridad"] == "Alta" and pub["enlace"] not in enviados:
            enviar_telegram(pub)
            registrar_enviado(pub["enlace"])
            alertas_enviadas += 1
    
    if alertas_enviadas == 0:
        print("ℹ️ No hay nuevas alertas de alta prioridad")
    else:
        print(f"\n✅ {alertas_enviadas} alertas enviadas por Telegram")
    
    print("\n" + "=" * 70)
    print("✅ PROCESO COMPLETADO")
    print("=" * 70 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
