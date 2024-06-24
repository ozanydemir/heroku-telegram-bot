# Project Overview: Telegram Crypto Price Alert Bot

This project is a Telegram bot that provides real-time cryptocurrency price alerts using the BingX API. Users can set up price alerts for specific cryptocurrency pairs, and the bot will notify them via Telegram when the prices reach the specified levels. The bot is implemented using Python and leverages the `telegram` and `requests` libraries.

## Key Features

- **Real-Time Price Alerts**: Set up alerts for specific cryptocurrency pairs. The bot will notify you when the prices cross the specified thresholds.
- **BingX API Integration**: Fetches real-time market data from the BingX API.
- **Telegram Notifications**: Sends notifications to a specified Telegram chat using the Telegram Bot API.
- **Easy to Use Commands**: Users can set and stop alerts using simple Telegram commands.

## How to Use

1. **Setting an Alert**:
   - Command: `/setalert COIN PRICE LEVEL`
   - Example: `/setalert BTC-USDT 50000 +`
   - This will notify the user when the price of BTC-USDT goes above 50000.

2. **Stopping an Alert**:
   - Command: `/stop COIN LEVEL`
   - Example: `/stop BTC-USDT +`
   - This will stop the alert for BTC-USDT going above the specified price.

## Project Structure

- **API Integration**: The bot uses the BingX API to fetch real-time cryptocurrency prices.
- **Telegram Bot**: The bot interacts with users through Telegram, receiving commands and sending notifications.
- **Asynchronous Execution**: Utilizes Python's `asyncio` for non-blocking operations, ensuring the bot remains responsive.

## Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/crypto-price-alert-bot.git
   cd crypto-price-alert-bot

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt

3. **Configure API Keys**:
   ```bash
   Replace YOUR_API_KEY, YOUR_SECRET_KEY, YOUR_TELEGRAM_BOT_TOKEN, and YOUR_CHAT_ID with your actual API keys and Telegram bot details.

4.**Run the Bot**:
   ```bash
    python bot.py
