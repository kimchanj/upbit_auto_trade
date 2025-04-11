import requests

def get_top_krw_markets_by_volume(limit=10):
    # 전체 마켓 목록 가져오기
    url = 'https://api.upbit.com/v1/market/all'
    res = requests.get(url)
    all_markets = res.json()

    # KRW 마켓만 필터링
    krw_markets = [m['market'] for m in all_markets if m['market'].startswith('KRW-')]

    # 시세 정보 요청 (최대 100개씩)
    tickers_url = f'https://api.upbit.com/v1/ticker?markets={",".join(krw_markets)}'
    ticker_res = requests.get(tickers_url)
    tickers = ticker_res.json()

    # 거래대금 기준으로 정렬
    sorted_markets = sorted(
        tickers,
        key=lambda x: x['acc_trade_price_24h'],
        reverse=True
    )

    # 상위 N개 마켓 추출
    top_markets = [m['market'] for m in sorted_markets[:limit]]
    return top_markets

# 테스트 출력
top_10 = get_top_krw_markets_by_volume(10)
print("📈 거래량 상위 10개 KRW 마켓:")
for market in top_10:
    print(market)
