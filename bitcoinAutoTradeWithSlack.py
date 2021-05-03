import time
import pyupbit
import datetime
import requests
import sys

slackchannel = "#yuyumanupbit"

def getparam(paramname):
    value = ''
    
    idx = 0
    for param in sys.argv:
        if param.upper() == paramname.upper() :
            value = sys.argv[idx + 1]
            break
        idx = idx + 1

    return value        

upbit = None

access = getparam("access")
secret = getparam("secret")
myToken = getparam("slacktoken")
rate = float(getparam("rate"))

coin = getparam("coin")
coin = coin.upper()

coinR = "KRW-" + coin



def post_message(token, channel, text):
    # print(text)
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
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
    value = float(0)

    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                value =  float(b['balance'])
            else:
                value =  0
            break

    return value

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]







print
(
    "access : ", access, 
    "secret : ", secret, 
    "myToken : ", myToken, 
    "rate : ", rate, 
    "accecoinss : ", coin
)

registerdt = datetime.datetime.now()
while True:
    try:
        if upbit == None : 
            upbit = pyupbit.Upbit(access, secret)
            print("autotrade start")
            post_message(myToken,slackchannel, coin + " " + "autotrade start")

        now = datetime.datetime.now()
        start_time = get_start_time(coinR)
        end_time = start_time + datetime.timedelta(days=1)


        if start_time < now < end_time - datetime.timedelta(seconds = 60):
            target_price = get_target_price(coinR, rate)
            ma15 = get_ma15(coinR)
            current_price = get_current_price(coinR)


            if (now - registerdt).seconds > 3600:
                registerdt = now
                post_message(myToken,slackchannel, coin + " " + "working target_price : " + str(target_price) + " ma15 : " + str(ma15) + " current_price : " + str(current_price))    


            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                mybtc = get_balance(coin)
                btcprice = float(pyupbit.get_current_price(coinR))
                print(coin + " krw " + str(krw), "mybtc " + str(mybtc), "btcprice " + str(btcprice))

                if (krw > 100000) and (mybtc * btcprice < 50000):
                    buy_result = upbit.buy_market_order(coinR, krw*0.9995)
                    post_message(myToken,slackchannel, coin + " " + " buy : " + str(buy_result))
        else:
            mybtc = get_balance(coin)
            btcprice = float(pyupbit.get_current_price(coinR))

            if mybtc * btcprice > 5000:
                sell_result = upbit.sell_market_order(coinR, mybtc * 0.9995)
                post_message(myToken,slackchannel, coin + " " + " buy : " + str(sell_result))

        time.sleep(2)
    except Exception as e:
        upbit = None
        print(e)
        post_message(myToken,slackchannel, e)
        time.sleep(2)
