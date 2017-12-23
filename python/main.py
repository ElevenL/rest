#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

from OkcoinSpotAPI import OKCoinSpot
from OkcoinFutureAPI import OKCoinFuture
from time import sleep
import logging

#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='log',
                filemode='a')



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


    def getTicker(self, symbol):
        return self.okcoinSpot.ticker(symbol)['ticker']

    def getBalance(self):
        '''

        :return: 
        '''
        self.balance = {}
        info = self.okcoinSpot.userinfo()
        for symbol in info['funds']['borrow'].keys():
            self.balance[symbol] = float(info['funds']['borrow'][symbol]) - float(info['funds']['freezed'][symbol])

    def trade(self, symbol, type, price, amount):
        '''

        :param symbol:
        :param type:
        :param price:
        :param amount:
        :return: order_id
        '''
        rsp = self.okcoinSpot.trade(symbol, type, price, amount)
        if rsp['result']:
            return rsp['order_id']
        else:
            return False

    def getOrderInfo(self, symbol, order_id):
        '''

        :param symbol:
        :param order_id:
        :return: order_status: -1:已撤销  0:未成交  1:部分成交  2:完全成交 3:撤单处理中
        '''
        rsp = self.okcoinSpot.orderinfo(symbol, order_id)
        if rsp['result']:
            return rsp['orders'][0]['status']
        else:
            return False

    def cancelOrder(self, symbol, order_id):
        '''

        :param symbol:
        :param order_id:
        :return: True or False
        '''
        rsp = self.okcoinSpot.cancelOrder(symbol, order_id)
        return rsp['result']

    def good_trade(self, symbols, Threshold=1.02):
        '''

        :param symbols: such as [btc, eth, mco]
        :return:
        '''
        symbol_1 = symbols[1] + '_' + symbols[0]
        symbol_2 = symbols[2] + '_' + symbols[0]
        symbol_3 = symbols[2] + '_' + symbols[1]
        t1 = self.getTicker(symbol_1)
        t2 = self.getTicker(symbol_2)
        t3 = self.getTicker(symbol_3)
        # print ('=======================================')
        # temp = (float(t2['sell']) / float(t3['buy']))
        a1 = (float(t2['sell']) / float(t3['buy'])) / float(t1['buy'])
        a2 = (float(t1['sell']) * float(t3['sell'])) / float(t2['buy'])

        if a1 < Threshold:
            traderSymbol = [symbol_2, symbol_3, symbol_1]

            logging.debug('=======================================')
            logging.debug(a1)
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[2] + '--->' + symbols[1] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)
        elif a2 < Threshold:
            traderSymbol = [symbol_1, symbol_3, symbol_2]

            logging.debug('=======================================')
            logging.debug(a2)
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[1] + '--->' + symbols[2] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)
        else:
            pass

    def tradePolicy(self, symbols, initAmount=0.005, Threshold=1.02):
        '''

        :param symbols: such as [btc, eth, mco]
        :return:
        '''
        retry = 3
        symbol_1 = symbols[1] + '_' + symbols[0]
        symbol_2 = symbols[2] + '_' + symbols[0]
        symbol_3 = symbols[2] + '_' + symbols[1]
        t1 = self.getTicker(symbol_1)
        t2 = self.getTicker(symbol_2)
        t3 = self.getTicker(symbol_3)
        a1 = (float(t2['sell']) / float(t3['buy'])) / float(t1['buy'])
        a2 = (float(t1['sell']) * float(t3['sell'])) / float(t2['buy'])
        # logging.debug(t1)
        if a1 < Threshold:
            logging.info('=========================================================')
            logging.debug(a1)
            traderSymbol = [symbol_2, symbol_3, symbol_1]
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[2] + '--->' + symbols[1] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)
            #step1
            logging.info('[step1]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount1 = round((initAmount * 0.999) / float(t2['sell']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_2 + '|buy|' + str(float(t2['sell'])) + '|' + str(amount1))
                orderId = self.trade(symbol_2, 'buy', float(t2['sell']), amount1)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_2, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_2, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_2, orderId)
                        logging.info('[cancelOrder!]')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return

            #step2
            logging.info('[step2]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount2 = self.balance[symbols[2]]
            for i in range(retry):
                logging.info('[order]' + symbol_3 + '|sell|' + str(float(t3['buy'])) + '|' + str(amount2))
                orderId = self.trade(symbol_3, 'sell', float(t3['buy']), amount2)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_3, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_3, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_3, orderId)
                        logging.info('cancelOrder!')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return

            #step3
            logging.info('[step3]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount3 = self.balance[symbols[1]]
            for i in range(retry):
                logging.info('[order]' + symbol_1 + '|sell|' + str(float(t1['buy'])) + '|' + str(amount3))
                orderId = self.trade(symbol_1, 'sell', float(t1['buy']), amount3)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_1, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_1, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_1, orderId)
                        logging.info('cancelOrder!')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return

        elif a2 < Threshold:
            logging.info('=========================================================')
            logging.debug(a2)
            traderSymbol = [symbol_1, symbol_3, symbol_2]
            logging.debug('[trader] ' + symbols[0] + '--->' + symbols[1] + '--->' + symbols[2] + '--->' + symbols[0])
            logging.debug(t1)
            logging.debug(t2)
            logging.debug(t3)

            # step1
            logging.info('[step1]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount1 = round((initAmount * 0.999) / float(t1['sell']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_1 + '|buy|' + str(float(t1['sell'])) + '|' + str(amount1))
                orderId = self.trade(symbol_1, 'buy', float(t1['sell']), amount1)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_1, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_1, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_1, orderId)
                        logging.info('cancelOrder!')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return

            # step2
            logging.info('[step2]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount2 = round((self.balance[symbols[1]] * 0.999) / float(t3['sell']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_3 + '|buy|' + str(float(t3['sell'])) + '|' + str(amount2))
                orderId = self.trade(symbol_3, 'buy', float(t3['sell']), amount2)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_3, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_3, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_3, orderId)
                        logging.info('cancelOrder!')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return

            # step3
            logging.info('[step3]')
            self.getBalance()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount3 = self.balance[symbols[2]]
            for i in range(retry):
                logging.info('[order]' + symbol_2 + '|sell|' + str(float(t2['buy'])) + '|' + str(amount3))
                orderId = self.trade(symbol_2, 'sell', float(t2['buy']), amount3)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_2, orderId)
                if status != 2:
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_2, orderId)
                    if status != 2:
                        self.cancelOrder(symbol_2, orderId)
                        logging.info('cancelOrder!')
                        return
                    else:
                        logging.info('[order succssed!]')
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order failed!]')
                return
        else:
            pass


if __name__ == '__main__':
    api = okex()
    while(1):
        api.tradePolicy(['btc', 'eth', 'mco'], initAmount=0.005, Threshold=0.98)
        api.tradePolicy(['btc', 'eth', 'eos'], initAmount=0.005, Threshold=0.98)
        api.tradePolicy(['btc', 'eth', 'xrp'], initAmount=0.005, Threshold=0.98)
        sleep(1)