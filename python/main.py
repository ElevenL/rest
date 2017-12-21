#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

from OkcoinSpotAPI import OKCoinSpot
from OkcoinFutureAPI import OKCoinFuture
from time import sleep
import logging

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='log',
                filemode='w')



class okex():
    def __init__(self):
        ##初始化apikey，secretkey,url
        apikey = 'XXXX'
        secretkey = 'XXXXX'
        okcoinRESTURL = 'www.okex.com'   #请求注意：国内账号需要 修改为 www.okcoin.cn

        #现货API
        self.okcoinSpot = OKCoinSpot(okcoinRESTURL,apikey,secretkey)

        # 期货API
        self.okcoinFuture = OKCoinFuture(okcoinRESTURL, apikey, secretkey)


    def get_ticker(self, symbol):
        return self.okcoinSpot.ticker(symbol)['ticker']

    def get_balance(self):
        self.balance = {}
        info = self.okcoinSpot.userinfo()
        for symbol in info['funds']['free']:
            self.balance[symbol] = float(info['funds']['free'][symbol]) - float(info['funds']['freezed'][symbol])

    def do_trade(self, ):
        pass

    def good_trade(self, symbols, Threshold=1.02):
        '''

        :param symbols: such as [btc, eth, mco]
        :return:
        '''
        symbol_1 = symbols[1] + '_' + symbols[0]
        symbol_2 = symbols[2] + '_' + symbols[0]
        symbol_3 = symbols[2] + '_' + symbols[1]
        t1 = self.get_ticker(symbol_1)
        t2 = self.get_ticker(symbol_2)
        t3 = self.get_ticker(symbol_3)
        print ('=======================================')
        logging.debug('=======================================')
        # temp = (float(t2['sell']) / float(t3['buy']))
        a1 = (float(t2['sell']) / float(t3['buy'])) / float(t1['buy'])
        a2 = (float(t1['sell']) * float(t3['sell'])) / float(t2['buy'])

        if a1 > Threshold:
            print (a1)
            print ('[trader] ' + symbols[0] + '--->' + symbols[2] + '--->' + symbols[1] + '--->' + symbols[0])
            print (t1)
            print (t2)
            print (t3)
            logging.debug(a1)
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[2] + '--->' + symbols[1] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)
        elif a2 > Threshold:
            print (a2)
            print ('[trader] ' + symbols[0] + '--->' + symbols[1] + '--->' + symbols[2] + '--->' + symbols[0])
            print (t1)
            print (t2)
            print (t3)
            logging.debug(a2)
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[1] + '--->' + symbols[2] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)
        else:
            pass

if __name__ == '__main__':
    api = okex()
    while(1):
        api.good_trade(['btc', 'eth', 'mco'], Threshold=1.02)
        sleep(1)