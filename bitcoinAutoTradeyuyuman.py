import time
import pyupbit
import datetime
import requests
import sys
import numpy as np



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

krwunit = int(getparam("krwunit"))

coin = getparam("coin")
coin = coin.upper()

coinR = "KRW-" + coin



upbit = pyupbit.Upbit(access, secret)

searchdt = (datetime.datetime.now() - datetime.timedelta(seconds = 600)).strftime('%Y-%m-%d %H:%M:%S')
# df = pyupbit.get_ohlcv("KRW-BTC", interval="minute10", count=100, to=searchdt)

def post_message(token, channel, text):
    # print(text)
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel,"text": text}
    )

def getactionsignal() :
    returnvalue = None

    df = pyupbit.get_ohlcv(coinR, interval="minute10", count=100)
    df['gap'] = abs(df['open'] - df['close'])
    df['gapavg'] = df['gap'].rolling(window=20).mean().shift(2)
    df['gaprate'] = df['gap'] / df['gapavg']
    df['gapresult'] = np.where(df['gaprate'] > 2.4, np.where(df['close'] > df['close'].shift(1), "longplus", "longminus") , "")


    df['closerate'] = ((df['close'] - df['close'].shift(1)) / df['close'].shift(1)) * 100
    df['volumerate'] = ((df['volume'] - df['volume'].shift(1)) / df['volume'].shift(1)) * 100

    df['ma10'] = df['close'].rolling(window=20).mean()
    df['ma22'] = df['close'].rolling(window=22).mean()
    df['marate'] = abs(df['ma22'] - df['ma10']) / ((abs(df['ma22'].shift(1) - df['ma10'].shift(1)) + abs(df['ma22'].shift(2) - df['ma10'].shift(2))) / 2)

    df['buysignal'] = np.where(
                    ((df['gapresult'] == "longplus") & (df['gapresult'].shift(1) == "longminus"))
                    | ((df['closerate'] > 0.25) & (df['volumerate'] > 70) & (df['closerate'].shift(1) > 0.25) & (df['volumerate'].shift(1) > 70))
                    , 
                    1
                    ,
                    0)


    df['sellsignal'] = np.where(
                    ((df['gapresult'] == "longminus") & (df['gapresult'].shift(1) == "longplus"))
                    | ((df['closerate'] < -0.25) & (df['volumerate'] > 70) & (df['closerate'].shift(1) < -0.25) & (df['volumerate'].shift(1) > 70))
                    , 
                    1
                    ,
                    0)


    df['buyaction'] = np.where(((df['buysignal'].shift(1) == 1 ) & (df['buysignal'].shift(2) == 0)), "buy", np.nan)
    df['sellaction'] = np.where(((df['sellsignal'].shift(1) == 1 ) & (df['sellsignal'].shift(2) == 0)), "sell", np.nan)


    df['buyprice'] = np.where((df['buyaction'] == "buy"), df['open'], np.nan)

    # df.data.fillna(method='backfill')

    value = 0
    for idx in df.index:
        lastidx = idx
        if (df.loc[idx, 'buyprice'] > 0) and (value == 0) :
            value = df.loc[idx, 'buyprice']
        else :
            df.loc[idx, 'buyprice'] = value

        if df.loc[idx, 'sellaction'] == "sell" :
            value = 0


    df['benefit'] = np.where((df['sellaction'] == "sell") & (df['buyprice'] > 0), (df['open'] - df['buyprice']) / df['buyprice'], np.nan)

    # print(lastidx)

    if (df.loc[lastidx, 'buyaction'] != np.nan) and (df.loc[lastidx, 'buyaction'] == "buy") : 
        return "buy"
    elif (df.loc[lastidx, 'sellaction'] != np.nan) and (df.loc[lastidx, 'sellaction'] == "sell") : 
        return "sell"
    else :
        return "stay"


def get_balance(coin):
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

def buy():
    myKRW = get_balance("KRW")
    mycoin = get_balance(coin)
    mycoinrate = float(pyupbit.get_current_price(coinR))
    

    if (myKRW > krwunit) and (mycoin * mycoinrate < krwunit * 0.5):
        post_message(myToken,slackchannel, coin + " buy myKRW:" + str(myKRW) + " mycoin:" + str(mycoin) + " mycoinrate:" + str(mycoinrate))
        print("buy ", "myKRW : ", str(myKRW), "mycoin : ", str(mycoin), "mycoinrate : ", str(mycoinrate))
        buy_result = upbit.buy_market_order(coinR, krwunit * 0.9995)

def sell():
    mycoin = get_balance(coin)
    mycoinrate = float(pyupbit.get_current_price(coinR))
    if mycoin * mycoin > 5000:
        post_message(myToken,slackchannel, coin + " sell mycoin:" + str(mycoin) + " mycoinrate:" + str(mycoinrate))
        print("sell ", "mycoin : ", str(mycoin), "mycoinrate : ", str(mycoinrate))
        sell_result = upbit.sell_market_order(coinR, mycoin * 0.9995)
        

registerdt = datetime.datetime.now()
while True :

    try :
        now = datetime.datetime.now()

        if (now - registerdt).seconds > 3600:
            registerdt = now
            post_message(myToken,slackchannel, coin + " yuyuman logic")            

        action = getactionsignal()
        print(coin, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), action)
        if action == "buy" :
            buy()
        elif action == "sell" :
            sell()
        
    except :
        print("except")

    time.sleep(5)
    
