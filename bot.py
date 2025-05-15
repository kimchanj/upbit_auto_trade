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

def get_top_krw_markets_by_volume(limit, type):
    market_url = 'https://api.upbit.com/v1/market/all'
    res = requests.get(market_url)
    all_markets = res.json()
    krw_markets = [m['market'] for m in all_markets if m['market'].startswith('KRW-')]
    ticker_url = f'https://api.upbit.com/v1/ticker?markets={",".join(krw_markets)}'
    ticker_res = requests.get(ticker_url)
    tickers = ticker_res.json()

    if type == 'V':
        sorted_markets = sorted(tickers, key=lambda x: x['acc_trade_price_24h'], reverse=True)
        return sorted_markets[:limit]
    elif type == 'R':
        # 전일 대비 상승률 계산
        sorted_markets = sorted(
            tickers,
            key=lambda x: ((x['trade_price'] - x['prev_closing_price']) / x['prev_closing_price']),
            reverse=True
        )
        return sorted_markets[:limit]

def run_bot():

    while True:
        # 거래량 상위 10개 KRW 코인
        # ranked = get_top_krw_markets_by_volume(10, 'V')
        ranked = get_top_krw_markets_by_volume(100, 'V')
        title = '🔥 자동 코인 감시 시작 (거래량 상위 10개 KRW 코인)'

        # 상승률 상위 10개 종목 추출
        # ranked = get_top_krw_markets_by_volume(10, 'R')
        # title = '🔥 자동 코인 감시 시작 (상승률 상위 10개 KRW 코인)'

        markets = [m['market'] for m in ranked]
        coin_state = {m: {'buy_price': None, 'buy_sent': False, 'sell_sent': False} for m in markets}

        print("")
        print(title)
        send_telegram_message(".... new ....")
        #send_telegram_message(title)

        for rank in ranked:
            market = rank['market']
            #if market != "":
            if market == "KRW-VIRTUAL":
                try:
                    data = rank
                    curr = data['trade_price']
                    open_price = data['opening_price']
                    low = data['low_price']
                    high = data['high_price']
                    prev_close = data['prev_closing_price']
                    change_percent = round((curr - prev_close) / prev_close * 100, 2)

                    # 현재가가 시작가 보다 낮을 때 현재가의 1% 낮춰서 매수가 판단
                    if curr < open_price:
                        threshold = curr * 0.99
                    else:
                        threshold = open_price * 0.98 # 시작가의 98% (2% 하락한 지점)

                    sell_price = threshold * 1.03 # 매수가의 3% (수익률)

                    msg = f"{market} : {change_percent}% / [시세] 현재가: {curr}원 / 매수가: {round(threshold,2)}원 / 매도가: {round(sell_price,2)}원 / 시작가: {open_price}원  / 저가: {low}원 / 고가: {high}원"
                    print(msg)
                    send_telegram_message(msg)

                    # 매수 조건: 현재가가 시작가(open)의 -2%에 도달했을 때
                    if curr <= threshold and not coin_state[market]['buy_sent']:
                        coin_state[market]['buy_price'] = curr
                        send_telegram_message(
                            f"[매수 조건] {market}\n시작가의({open_price:.0f})의 2% 이내 도달\n매수가: {curr:.0f}"
                        )
                        coin_state[market]['buy_sent'] = True

                    # 매도 조건: 매수가 대비 +3% 수익 발생 시
                    if coin_state[market]['buy_price'] and not coin_state[market]['sell_sent']:
                        profit = (curr - coin_state[market]['buy_price']) / coin_state[market]['buy_price']
                        if profit >= 0.03:
                            send_telegram_message(
                                f"[매도 조건] {market}\n+3% 수익 발생!\n매수가: {coin_state[market]['buy_price']:.0f} → 현재가: {curr:.0f}"
                            )
                            coin_state[market]['sell_sent'] = True

                except Exception as e:
                    print(f"[{market}] 오류 발생: {e}")

        #time.sleep(60)  # 1분 간격
        time.sleep(10)  # 10초 간격

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
