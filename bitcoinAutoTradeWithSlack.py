import time
import pyupbit
import datetime
import requests

access = "dwRuYdVuLWzji0v8srojGaOOPF6dcSxTzbHxSmJ8"
secret = "qpuLzXvPph4Cg4OQask7c5dyqMtaNI3g2SNnxLQk"
myToken = "xoxb-2025300039396-2004384039591-65UKSR2gnxxkOEPehXFMGvIL"
rate = 0.4
slackchannel = "#yuyumanupbit"

def post_message(token, channel, text):
    # print(text)
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(coin):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

upbit = None

registerdt = datetime.datetime.now()
while True:
    try:
        if upbit == None : 
            # 로그인
            upbit = pyupbit.Upbit(access, secret)
            print("autotrade start")
            # 시작 메세지 슬랙 전송
            post_message(myToken,slackchannel, "autotrade start")

        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)


        if (now - registerdt).seconds > 3600:
            registerdt = now
            post_message(myToken,slackchannel, "working")    

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-BTC", rate)
            ma15 = get_ma15("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            print("target_price : ", str(target_price), "ma15 : ", str(ma15), "current_price : ", str(current_price))
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    buy_result = upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    post_message(myToken,slackchannel, "BTC buy : " +str(buy_result))
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_result = upbit.sell_market_order("KRW-BTC", btc*0.9995)
                post_message(myToken,slackchannel, "BTC buy : " +str(sell_result))

        time.sleep(1)
    except Exception as e:
        upbit = None
        print(e)
        post_message(myToken,slackchannel, e)
        time.sleep(1)
