import requests
import time
import hmac
from hashlib import sha256
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
import asyncio

APIURL = "https://open-api.bingx.com"
APIKEY = "O97o84Mk0is9vFtB61TE9TqITEovwoQC4mEOl60Ixk8PDyo2qgOjhr3LKzYRyNDZhnFvkT56D623cK5XA"
SECRETKEY = "BbMimCmoDMz9zCzV8IAQhn0OG6ptFtEixEqoLSqQV5oQiklJ6M34Z0xql3ndP0T4Xgx82xewh8B2McAtw"

TELEGRAM_BOT_TOKEN = "7052097278:AAE0WQbMNlPegk8QqUPGm8D1TdAH7rRfCM4"
CHAT_ID = "6060798795"

# Değişkenler
alert_prices = {}
active_alerts = {}

def get_prices(symbols):
    payload = {}
    path = '/openApi/swap/v2/quote/ticker'
    method = "GET"
    paramsMap = {
        "symbols": ",".join(symbols)
    }
    paramsStr = parseParam(paramsMap)
    response = send_request(method, path, paramsStr, payload)
    return response

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.json()

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "": 
        return paramsStr + "&timestamp=" + str(int(time.time() * 1000))
    else:
        return "timestamp=" + str(int(time.time() * 1000))

async def send_telegram_message(bot, message):
    await bot.send_message(chat_id=CHAT_ID, text=message)

def set_alert(update: Update, context: CallbackContext) -> None:
    global alert_prices, active_alerts
    print("set_alert komutu alındı")  # Komutun alındığını doğrulamak için
    if len(context.args) != 2:
        update.message.reply_text('Kullanım: /setalert COIN SEVIYE (örneğin: /setalert BTC-USDT 50000)')
        return
    coin = context.args[0].upper()
    price = float(context.args[1])
    alert_prices[coin] = price
    active_alerts[coin] = True
    print(f'Alarm ayarlandı: {coin} - {price}')  # Ayarlandığını doğrulamak için
    update.message.reply_text(f'Alarm ayarlandı: {coin} - {price}')

def stop_alert(update: Update, context: CallbackContext) -> None:
    global active_alerts
    print("stop komutu alındı")  # Komutun alındığını doğrulamak için
    if len(context.args) != 1:
        update.message.reply_text('Kullanım: /stop COINADI (örneğin: /stop BTC-USDT)')
        return
    coin = context.args[0].upper()
    if coin in active_alerts:
        active_alerts[coin] = False
        print(f'Alarm durduruldu: {coin}')  # Durdurulduğunu doğrulamak için
        update.message.reply_text(f'Alarm durduruldu: {coin}')
    else:
        update.message.reply_text(f'Alarm bulunamadı: {coin}')

def start_bot():
    print("Bot başlatılıyor...")  # Botun başlatıldığını doğrulamak için
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("setalert", set_alert))
    application.add_handler(CommandHandler("stop", stop_alert))

    application.run_polling()

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    print("Fiyat kontrolüne başlanıyor...")  # Fiyat kontrolünün başlatıldığını doğrulamak için
    
    while True:
        if alert_prices:
            symbols = list(alert_prices.keys())
            price_data = get_prices(symbols)
            if 'data' in price_data:
                for coin_data in price_data['data']:
                    symbol = coin_data['symbol']
                    if symbol in alert_prices and active_alerts.get(symbol, False):
                        last_price = float(coin_data['lastPrice'])
                        if last_price <= alert_prices[symbol]:
                            message = f"{symbol} fiyatı {last_price} seviyesine ulaştı!"
                            print(message)
                            await send_telegram_message(bot, message)  # Metin mesajı gönder
                            # play_alarm()  # Sesli alarmı çal
        time.sleep(1)  # Her saniye fiyatları kontrol et

if __name__ == '__main__':
    # Ana iş parçacığında Telegram botunu çalıştır
    from threading import Thread
    price_check_thread = Thread(target=lambda: asyncio.run(main()))
    price_check_thread.start()

    start_bot()  # Bu, ana iş parçacığında çalışmalı
