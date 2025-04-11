import requests
import time

# 업비트 시장 정보 설정
MARKET = 'KRW-UXLINK'
BASE_URL = 'https://api.upbit.com/v1'

# 텔레그램 봇 설정 (본인의 정보로 교체)
#https://api.telegram.org/bot7770405055:AAH_bsGQjzOGFXGgtyEGjducGbGysgPuEWQ/getUpdates
TELEGRAM_TOKEN = '7770405055:AAH_bsGQjzOGFXGgtyEGjducGbGysgPuEWQ'
TELEGRAM_CHAT_ID = '7912281061'

# 매매 기록 저장용 변수
buy_price = None
buy_sent = False
sell_sent = False

def send_telegram_message(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    requests.post(url, data=data)

def get_candle_data():
    url = f'{BASE_URL}/candles/days?market={MARKET}&count=2'
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
        raise Exception('Candle data fetch failed')

def run_strategy():
    global buy_price, buy_sent, sell_sent

    try:
        data = get_candle_data()
        curr = data['current_price']
        low = data['low_price']
        high = data['high_price']
        prev_close = data['prev_close']
        threshold = low * 1.01
        sell_price = threshold * 1.02

        print(f"{MARKET} [시세] 매수가: {threshold}원 / 매도가: {sell_price}원 / 현재가: {curr}원 / 당일저가: {low}원 / 당일고가: {high}원 / 전일종가: {prev_close}원")
        send_telegram_message(f"{MARKET} [시세] 매수가: {threshold}원 / 매도가: {sell_price}원 / 현재가: {curr}원 / 당일저가: {low}원 / 당일고가: {high}원 / 전일종가: {prev_close}원")

        # 매수 조건
        if curr <= threshold and not buy_sent:
            buy_price = curr
            send_telegram_message(f"[매수 조건 충족]\n현재가가 전일 저가({low})의 1% 이내!\n매수 추천가: {curr}원")
            buy_sent = True

        # 매도 조건
        if buy_price and not sell_sent:
            profit_rate = (curr - buy_price) / buy_price
            if profit_rate >= 0.02:
                send_telegram_message(f"[매도 조건 충족]\n수익률 +2% 이상 도달!\n매수가: {buy_price}원 → 현재가: {curr}원")
                sell_sent = True

    except Exception as e:
        print("⚠️ 오류 발생:", e)

# 1분마다 감시
while True:
    run_strategy()
    #time.sleep(60)  # 1분
    time.sleep(300)  # 5분
