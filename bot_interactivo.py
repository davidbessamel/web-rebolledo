import os
import telebot

# Recupera el token guardado en los Secret Keys / Variables de entorno
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Verificación de seguridad por si no se encuentra la variable
if not TOKEN:
    raise ValueError("❌ No se encontró la variable TELEGRAM_BOT_TOKEN en el entorno.")

# Inicializar el bot
bot = telebot.TeleBot(TOKEN)

# Comando /start
@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    texto = (
        "👋 *¡Hola! Bienvenido al bot oficial de Rebolledo de la Torre.*\n\n"
        "Puedes usar los siguientes comandos para consultar información:\n"
        "• /transporte - Horarios y reserva del transporte gratuito\n"
        "• /eventos - Próximas actividades en el pueblo\n"
        "• /teleclub - Horario del centro social"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# Comando /transporte
@bot.message_handler(commands=['transporte'])
def responder_transporte(message):
    texto = (
        "🚌 *Transporte a la Demanda - Rebolledo de la Torre*\n\n"
        "• *Horarios:* Lunes a Viernes por la mañana.\n"
        "• *Reserva:* Es obligatorio solicitar plaza el día anterior antes de las 20:00h.\n\n"
        "📞 *Teléfono gratuito de reserva:* 900 20 40 20"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# Comando /eventos
@bot.message_handler(commands=['eventos'])
def responder_eventos(message):
    texto = (
        "📅 *Próximos Eventos*\n\n"
        "• *Observación Astronómica:* Sábado a las 22:30h en el Castillo.\n"
        "• *Taller Cultural:* Domingo a las 18:00h en el Teleclub."
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# Bucle principal para escuchar mensajes de los vecinos
if __name__ == "__main__":
    print("🤖 Bot interactivo de Rebolledo de la Torre iniciado y escuchando...")
    bot.infinity_polling()
