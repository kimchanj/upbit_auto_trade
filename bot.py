from flask import Flask
import threading
import time
import requests
import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 테스트용)
load_dotenv()

# 텔레그램 설정 (환경변수 또는 직접 입력)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id")

# 자동 매매 봇과 관련된 함수들
def send_telegram_message(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("텔레그램 전송 오류:", e)

def get_top_krw_markets_by_volume(limit=10):
    market_url = 'https://api.upbit.com/v1/market/all'
    res = requests.get(market_url)
    all_markets = res.json()
    krw_markets = [m['market'] for m in all_markets if m['market'].startswith('KRW-')]
    ticker_url = f'https://api.upbit.com/v1/ticker?markets={",".join(krw_markets)}'
    ticker_res = requests.get(ticker_url)
    tickers = ticker_res.json()
    sorted_markets = sorted(tickers, key=lambda x: x['acc_trade_price_24h'], reverse=True)
    return [m['market'] for m in sorted_markets[:limit]]

def get_candle_data(market):
    url = f'https://api.upbit.com/v1/candles/days?market={market}&count=2'
    res = requests.get(url)
    if res.status_code == 200:
        today, yesterday = res.json()
        return {
            'current_price': today['trade_price'],
            'low_price': today['low_price'],
            'high_price': today['high_price'],
            'prev_close': yesterday['trade_price']
        }
    else:
        raise Exception(f'{market} 시세 가져오기 실패')

def run_bot():
    # 초기 코인 상태: 거래량 상위 10개 KRW 코인
    markets = get_top_krw_markets_by_volume(10)
    coin_state = {m: {'buy_price': None, 'buy_sent': False, 'sell_sent': False} for m in markets}

    while True:
        print("")
        print("🔥 자동 코인 감시 시작 (상위 10개 KRW 코인)")
        send_telegram_message(".... new ....")
        send_telegram_message("🔥 자동 코인 감시 시작 (상위 10개 KRW 코인)")

        for market in markets:
            #if market != "":
            if market == "KRW-UXLINK":
                try:
                    data = get_candle_data(market)
                    curr = data['current_price']
                    low = data['low_price']
                    high = data['high_price']
                    prev_close = data['prev_close']
                    threshold = low * 1.01
                    sell_price = threshold * 1.03

                    msg = f"{market} [시세] 매수가: {round(threshold,2)}원 / 매도가: {round(sell_price,2)}원 / 현재가: {curr}원 / 당일저가: {low}원 / 당일고가: {high}원 / 전일종가: {prev_close}원"
                    print(msg)
                    send_telegram_message(msg)

                    # 매수 조건: 현재가가 전일 저가의 1% 이내
                    if curr <= threshold and not coin_state[market]['buy_sent']:
                        coin_state[market]['buy_price'] = curr
                        send_telegram_message(
                            f"[매수 조건] {market}\n전일 저가({low:.0f})의 1% 이내 도달\n매수가: {curr:.0f}"
                        )
                        coin_state[market]['buy_sent'] = True

                    # 매도 조건: 매수가 대비 +2% 수익 발생 시
                    if coin_state[market]['buy_price'] and not coin_state[market]['sell_sent']:
                        profit = (curr - coin_state[market]['buy_price']) / coin_state[market]['buy_price']
                        if profit >= 0.02:
                            send_telegram_message(
                                f"[매도 조건] {market}\n+3% 수익 발생!\n매수가: {coin_state[market]['buy_price']:.0f} → 현재가: {curr:.0f}"
                            )
                            coin_state[market]['sell_sent'] = True

                except Exception as e:
                    print(f"[{market}] 오류 발생: {e}")

        time.sleep(60)  # 1분 간격
        #time.sleep(180)  # 3분 간격

# Flask 앱 생성
app = Flask(__name__)

@app.route("/")
def index():
    return "Telegram Bot is Running!"

def start_flask():
    # Render는 할당된 PORT 환경변수를 사용합니다.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # 봇 로직을 백그라운드 스레드로 실행합니다.
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Flask 웹 서버 실행 (포트 바인딩 충족)
    start_flask()

    from keep_alive import keep_alive
    keep_alive()
