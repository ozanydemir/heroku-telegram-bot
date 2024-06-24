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

TELEGRAM_BOT_TOKEN = "-"
CHAT_ID = "-"

# Değişkenler
alert_prices = {}
active_alerts = {}


def get_prices(symbols):
    """
    Belirtilen semboller için piyasa verilerini BingX API'sinden alır.
    """
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
    """
    API istekleri için HMAC SHA256 imzası oluşturur.
    """
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature

def send_request(method, path, urlpa, payload):
    """
    API isteklerini gönderir ve yanıtı JSON formatında döndürür.
    """
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.json()

def parseParam(paramsMap):
    """
    API parametrelerini uygun formatta birleştirir.
    """
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "":
        return paramsStr + "&timestamp=" + str(int(time.time() * 1000))
    else:
        return "timestamp=" + str(int(time.time() * 1000))

async def send_telegram_message(bot, message):
    """
    Telegram botu aracılığıyla mesaj gönderir.
    """
    await bot.send_message(chat_id=CHAT_ID, text=message)

async def set_alert(update: Update, context: CallbackContext) -> None:
    """
    Kullanıcıdan gelen /setalert komutunu işler ve alarm ayarlarını yapar.
    """
    global alert_prices, active_alerts   # Global değişkenleri kullanmak için global bildirimi yapılır
    print("set_alert komutu alındı")  # Komutun alındığını doğrulamak için bir mesaj yazdırılır
    
    # Kullanıcıdan gelen argüman sayısı kontrol edilir. İki argüman (coin ve seviye) beklenir.
    if len(context.args) != 3:
        # Eğer argüman sayısı yanlışsa, kullanıcıya doğru kullanım hakkında bilgi verilir.
        await update.message.reply_text('Hatalı komut!! \n Kullanım: /setalert COIN SEVIYE +/- \n Örneğin: /setalert BTC-USDT 50000 -')
        return  # Fonksiyon sonlandırılır
    
    coin = context.args[0].upper()  # İlk argüman olan coin sembolü büyük harfe dönüştürülerek alınır
    price = float(context.args[1])  # İkinci argüman olan seviye (fiyat) float (ondalık sayı) olarak alınır
    priceLevel = str(context.args[2]) #Üçüncü argüman olan fiyatın belirlenen değerinin altında mı yoksa üstünde mi olduğunda alarm çalacağı belirlenir
    

    # Alarm ayarları global değişkenlerde saklanır
    alert_key = f"{coin}_{priceLevel}"  # Coin ve fiyat seviyesini birleştirerek benzersiz bir anahtar oluşturulur
    active_alerts[alert_key] = True  # Coin ve belirlenen seviye (fiyat) alert_prices sözlüğüne eklenir
    alert_prices[alert_key] = price # Alarmın aktif olduğunu belirten bayrak active_alerts sözlüğüne eklenir
    
    # Güncel fiyatı al
    current_price_data = get_prices([coin])
    current_price = None
    if 'data' in current_price_data:
        for coin_data in current_price_data['data']:
            if coin_data['symbol'] == coin:
                current_price = float(coin_data['lastPrice'])
                break

    #Kullanıcıya güncel fiyatı gönder
    if current_price is not None:
        await update.message.reply_text(f'{coin} güncel fiyatı {current_price}')
    else:
        await update.message.reply_text(f'{coin} güncel fiyatı alınamadı!')
     
     # Kullanıcıya alarmın ayarlandığını bildiren bir mesaj gönderilir
    if priceLevel == "+":
        await update.message.reply_text(f'Alarm ayarlandı: {coin} - {price} üzerine çıkarsa haber verilecek!')

    elif priceLevel == "-":
        await update.message.reply_text(f'Alarm ayarlandı: {coin} - {price} altına düşerse haber verilecek!')


async def stop_alert(update: Update, context: CallbackContext) -> None:
    """
    Kullanıcıdan gelen /stop komutunu işler ve belirli bir coinin alarmını durdurur.
    """
    global active_alerts  # Global değişkeni kullanmak için global bildirimi yapılır
    print("stop komutu alındı")  # Komutun alındığını doğrulamak için bir mesaj yazdırılır
    
    # Kullanıcıdan gelen argüman sayısı kontrol edilir. Bir argüman (coin adı) beklenir.
    if len(context.args) != 2:
        # Eğer argüman sayısı yanlışsa, kullanıcıya doğru kullanım hakkında bilgi verilir.
        await update.message.reply_text('Kullanım: /stop COINADI +/- (örneğin: /stop BTC-USDT +)')
        return  # Fonksiyon sonlandırılır
    
    coin = context.args[0].upper()  # İlk argüman olan coin adı büyük harfe dönüştürülerek alınır
    price_level = context.args[1]
    
    # Coin adı ve fiyat seviyesi aktif alarmlar arasında kontrol edilir
    alert_key = f"{coin}_{price_level}"
    if alert_key in active_alerts:
        active_alerts[alert_key] = False
        print(f'Alarm durduruldu: {coin} {price_level}')  # Durdurulduğunu doğrulamak için bir mesaj yazdırılır
        await update.message.reply_text(f'Alarm durduruldu: {coin} {price_level}')  # Kullanıcıya alarmın durdurulduğunu bildiren bir mesaj gönderilir
    else:
        await update.message.reply_text(f'Alarm bulunamadı: {coin} {price_level}')  # Alarm bulunamadıysa, kullanıcıya bilgi verilir


def start_bot():
    """
    Telegram botunu başlatır ve komutları dinler.
    """
    print("Bot başlatılıyor...")  # Botun başlatıldığını doğrulamak için bir mesaj yazdırılır
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()  # Bot uygulaması oluşturulur

    # Komut işleyicileri eklenir
    application.add_handler(CommandHandler("setalert", set_alert))  # /setalert komutu için işleyici eklenir
    application.add_handler(CommandHandler("stop", stop_alert))  # /stop komutu için işleyici eklenir

    application.run_polling()  # Bot komutları dinlemeye başlar

async def main():
    """
    Piyasa verilerini sürekli olarak kontrol eder ve belirlenen fiyat seviyelerine ulaşıldığında alarm verir.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)  
    print("Fiyat kontrolüne başlanıyor...") 

    while True: 
        if alert_prices:  # Eğer ayarlanmış herhangi bir alarm varsa (alert_prices sözlüğü boş değilse)
            symbols = list(set(key.split('_')[0] for key in alert_prices.keys()))  # Alarm ayarlanmış coinlerin sembollerini alır
            price_data = get_prices(symbols)  # Bu coinlerin piyasa verilerini API'den alır
            
            if 'data' in price_data:  # API'den gelen veride 'data' anahtarı varsa
                for coin_data in price_data['data']:  # 'data' içindeki her coin verisini işler
                    symbol = coin_data['symbol']  # Coinin sembolünü alır (örneğin BTC-USDT)
                    last_price = float(coin_data['lastPrice'])  # Coinin son fiyatını alır ve float türüne dönüştürür
                    
                    for price_level in ['-', '+']:
                        alert_key = f"{symbol}_{price_level}"
                        if alert_key in alert_prices and active_alerts.get(alert_key, False):  # Coinin alarm ayarları varsa ve alarm aktifse
                            if price_level == "-" and last_price <= alert_prices[alert_key]:  # Eğer fiyat seviyesi "-" ve son fiyat alarm seviyesine ulaştıysa veya altına düştüyse
                                message = f"{symbol} fiyatı {last_price} seviyesine düştü!"  # Bir mesaj oluşturur
                                print(message)  # Mesajı konsola yazdırır
                                await send_telegram_message(bot, message)  # Telegram botu aracılığıyla mesaj gönderir
                            
                            elif price_level == "+" and last_price >= alert_prices[alert_key]:  # Eğer fiyat seviyesi "+" ve son fiyat alarm seviyesine ulaştıysa veya üstüne çıktıysa
                                message = f"{symbol} fiyatı {last_price} seviyesine çıktı!"  # Bir mesaj oluşturur
                                print(message)  # Mesajı konsola yazdırır
                                await send_telegram_message(bot, message)  # Telegram botu aracılığıyla mesaj gönderir

        await asyncio.sleep(1)  # Döngünün her iterasyonundan sonra 1 saniye bekler, böylece API istekleri arasında bir gecikme olur
    

if __name__ == '__main__':
    # Fiyat kontrolünü ayrı bir iş parçacığında çalıştır
    from threading import Thread
    price_check_thread = Thread(target=lambda: asyncio.run(main()))  # Fiyat kontrolünü başlatır
    price_check_thread.start()  # Fiyat kontrolü iş parçacığını başlatır

    start_bot()  # Telegram botunu ana iş parçacığında çalıştır
