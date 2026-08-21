web-rebolledo

Portal de Rebolledo de la Torre.

Instrucciones rápidas:

    Generar JSON + snapshot localmente:
        python3 -m venv .venv && source .venv/bin/activate
        pip install requests
        python3 actualizar_boletines.py --emit-html
        Archivos generados: publicaciones_oficiales.json, boletines_snapshot.html

    Servir localmente:
        python3 -m http.server 8000
        Abrir: http://localhost:8000/boletines.html

    Configurar notificaciones Telegram (opcional):
        Añadir TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID a Settings → Secrets en GitHub para que la workflow pueda enviar notificaciones. EOF

