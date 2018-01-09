#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

from OkcoinSpotAPI import OKCoinSpot
from OkcoinFutureAPI import OKCoinFuture
from operator import itemgetter
from time import *
from conf import *
from itertools import *
import logging
import json
import threading

#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='log',
                filemode='a')

SYMBOL = ['ace', 'act', 'amm', 'ark', 'ast', 'avt', 'bnt', 'btm', 'cmt', 'ctr',
          'cvc', 'dash', 'dat', 'dgb', 'dgd', 'dnt', 'dpy', 'edo', 'elf', 'eng',
          'eos', 'etc', 'evx', 'fun', 'gas', 'gnt', 'gnx', 'hsr', 'icn', 'icx',
          'iota', 'itc', 'kcash', 'knc', 'link', 'lrc', 'ltc', 'mana', 'mco',
          'mda', 'mdt', 'mth', 'nas', 'neo', 'nuls', 'oax', 'omg', 'pay',
          'ppt', 'pro', 'qtum', 'qvt', 'rcn', 'rdn', 'read', 'req', 'rnt', 'salt',
          'san', 'sngls', 'snm', 'snt', 'ssc', 'storj', 'sub', 'swftc',
          'tnb', 'trx', 'ugc', 'ukg', 'vee', 'wrc', 'wtc', 'xem', 'xlm', 'xmr',
          'xrp', 'xuc', 'yoyo', 'zec', 'zrx', '1st']


amount = {
    'eth_btc': 0.015,
    'eos_btc': 1.8,
    'eos_eth': 1.8,
    'etc_btc': 0.5,
    'etc_eth': 0.5,
    'mco_btc': 0.8,
    'mco_eth': 0.8,
}

global depth

class okex():
    def __init__(self):
        global depth
        ##初始化apikey，secretkey,url
        apikey = config.apikey
        secretkey = config.secretkey
        okcoinRESTURL = 'www.okex.com'   #请求注意：国内账号需要 修改为 www.okcoin.cn

        #现货API
        self.okcoinSpot = OKCoinSpot(okcoinRESTURL,apikey,secretkey)

        # 期货API
        self.okcoinFuture = OKCoinFuture(okcoinRESTURL, apikey, secretkey)

        self.depth = {}
        depth = {}


    def getTicker(self, symbol):
        return self.okcoinSpot.ticker(symbol)['ticker']

    def getDepth(self, symbol):
        global depth
        try:
            d = self.okcoinSpot.depth(symbol)
            depth[symbol] = {'sell':{'price':d['asks'][-1][0], 'amount':d['asks'][-1][1]},
                    'buy':{'price':d['bids'][0][0], 'amount':d['bids'][0][1]}}
        except Exception:
            logging.debug('getDepth api error!')
            pass
        # print({'sell':{'price':depth['asks'][-1][0], 'amount':depth['asks'][-1][1]},
        #         'buy':{'price':depth['bids'][0][0], 'amount':depth['bids'][0][1]}})
        # return {'sell':{'price':depth['asks'][-1][0], 'amount':depth['asks'][-1][1]},
        #         'buy':{'price':depth['bids'][0][0], 'amount':depth['bids'][0][1]}}

    def getBalance(self):
        '''

        :return:
        '''
        self.balance = {}
        try:
            info = json.loads(self.okcoinSpot.userinfo())
            for symbol in info['info']['funds']['free'].keys():
                self.balance[symbol] = float(info['info']['funds']['free'][symbol])
        except Exception:
            logging.debug('getBalance api error!')

    def trade(self, symbol, type, price, amount):
        '''

        :param symbol:
        :param type:
        :param price:
        :param amount:
        :return: order_id
        '''
        if price != '':
            logging.info('[order]' + symbol + '|' + type+ '|' + str(price) + '|' + str(amount))
        try:
            rsp = json.loads(self.okcoinSpot.trade(symbol, type, price, amount))
            if 'error_code' in rsp:
                if str(rsp['error_code']) != '1003':
                    logging.info('[trade error]' + str(rsp['error_code']))
                return False
            if rsp['result']:
                return rsp['order_id']
        except Exception:
            logging.debug('trade api error!')
            return False

    def getOrderInfo(self, symbol, order_id):
        '''

        :param symbol:
        :param order_id:
        :return: order_status: -1:已撤销  0:未成交  1:部分成交  2:完全成交 3:撤单处理中
        '''
        try:
            rsp = json.loads(self.okcoinSpot.orderinfo(symbol, order_id))
            if 'error_code' in rsp:
                logging.info('[getOrderInfo error]' + str(rsp['error_code']))
                return False
            if rsp['result']:
                return int(rsp['orders'][0]['status'])
            else:
                return False
        except Exception:
            logging.debug('getOrderInfo api error!')
            return False

    def toBtc(self):
        self.getBalance()
        for symbol in self.balance.keys():
            if symbol != 'usdt' and symbol != 'btc' and symbol != 'mtl' and self.balance[symbol] != 0:
                # print(symbol)
                if self.balance[symbol] != 0:
                    tradeSymbol = symbol + '_btc'
                    self.trade(tradeSymbol, 'sell_market', '', self.balance[symbol])

    def cancelOrder(self, symbol, order_id):
        '''

        :param symbol:
        :param order_id:
        :return: True or False
        '''
        try:
            rsp = json.loads(self.okcoinSpot.cancelOrder(symbol, order_id))
            if 'error_code' in rsp:
                logging.info('[cancelOrder error]' + str(rsp['error_code']))
                return False
            return rsp['result']
        except Exception:
            logging.debug('cancelOrder api error!')
            return False

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
        t1 = self.getDepth(symbol_1)
        t2 = self.getDepth(symbol_2)
        t3 = self.getDepth(symbol_3)
        a1 = (float(t2['sell']['price']) / float(t3['buy']['price'])) / float(t1['buy']['price'])
        a2 = (float(t1['sell']['price']) * float(t3['sell']['price'])) / float(t2['buy']['price'])
        # logging.debug(t1)
        if a1 < Threshold:
            if float(t2['sell']['amount']) < amount[symbol_2] or float(t3['buy']['amount']) < amount[symbol_3] or\
                float(t1['buy']['amount']) < amount[symbol_1]:
                return
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
            self.toBtc()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount1 = round((initAmount * 0.999) / float(t2['sell']['price']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_2 + '|buy|' + str(float(t2['sell']['price'])) + '|' + str(amount1))
                orderId = self.trade(symbol_2, 'buy', float(t2['sell']['price']), amount1)
                if orderId:
                    break
            if orderId:
                logging.info('[orderId]' + str(orderId))
                status = self.getOrderInfo(symbol_2, orderId)
                if status != 2:
                    print(status)
                    sleep(0.5)
                    status = self.getOrderInfo(symbol_2, orderId)
                    if status != 2:
                        print(status)
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
                logging.info('[order]' + symbol_3 + '|sell|' + str(float(t3['buy']['price'])) + '|' + str(amount2))
                orderId = self.trade(symbol_3, 'sell', float(t3['buy']['price']), amount2)
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
                logging.info('[order]' + symbol_1 + '|sell|' + str(float(t1['buy']['price'])) + '|' + str(amount3))
                orderId = self.trade(symbol_1, 'sell', float(t1['buy']['price']), amount3)
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
            if float(t2['buy']['amount']) < amount[symbol_2] or float(t3['sell']['amount']) < amount[symbol_3] or\
                float(t1['sell']['amount']) < amount[symbol_1]:
                return
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
            self.toBtc()
            logging.info('[Balance]')
            logging.info(self.balance)
            amount1 = round((initAmount * 0.999) / float(t1['sell']['price']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_1 + '|buy|' + str(float(t1['sell']['price'])) + '|' + str(amount1))
                orderId = self.trade(symbol_1, 'buy', float(t1['sell']['price']), amount1)
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
            amount2 = round((self.balance[symbols[1]] * 0.999) / float(t3['sell']['price']), 8)
            for i in range(retry):
                logging.info('[order]' + symbol_3 + '|buy|' + str(float(t3['sell']['price'])) + '|' + str(amount2))
                orderId = self.trade(symbol_3, 'buy', float(t3['sell']['price']), amount2)
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
                logging.info('[order]' + symbol_2 + '|sell|' + str(float(t2['buy']['price'])) + '|' + str(amount3))
                orderId = self.trade(symbol_2, 'sell', float(t2['buy']['price']), amount3)
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

    def getCoinList(self, symbols):
        coinList = []
        for k in permutations(symbols, 2):
            tmp = ['btc', k[0], 'eth', k[1]]
            coinList.append(tmp)
        return coinList

    def getTradeSymbol(self, coinlist):
        ts =[]
        for c in coinlist:
            s = ['_'.join((c[1], c[0])),
                '_'.join((c[1], c[2])),
                '_'.join((c[3], c[2])),
                '_'.join((c[3], c[0]))]
            ts.append(s)
        return ts

    def getTradeAmount(self, symbols):
        global depth
        # print(len(depth))
        for s in symbols:
            if s not in depth.keys():
                return 0,0
        ss = (depth[symbols[1]]['buy']['price'] * depth[symbols[3]]['buy']['price']) / (depth[symbols[0]]['sell']['price'] * depth[symbols[2]]['sell']['price'])
        if ss > 1.01:
            # logging.debug('profit: %f' % ss)
            # logging.debug(symbols)
            # logging.debug(depth[symbols[0]])
            # logging.debug(depth[symbols[1]])
            # logging.debug(depth[symbols[2]])
            # logging.debug(depth[symbols[3]])
            amount = []
            amount.append(depth[symbols[0]]['sell']['price'] * min(depth[symbols[0]]['sell']['amount'],
                                                                        depth[symbols[1]]['buy']['amount']))
            amount.append(depth[symbols[3]]['buy']['price'] * min(depth[symbols[3]]['buy']['amount'],
                                                                       depth[symbols[2]]['sell']['amount']))
            amount.sort()
            # logging.debug('amount: %f' % amount[0])
            return ss,amount[0]
        else:
            return 0,0

    def doTrade(self, symbols, amount):
        global depth
        if self.balance['btc'] < amount * 0.9:
            initamount = self.balance['btc'] * 0.99
        else:
            initamount = amount * 0.9

        logging.debug('step1')
        amount1 = round(initamount / depth[symbols[0]]['sell']['price'], 8)
        orderId = self.trade(symbols[0], 'buy', depth[symbols[0]]['sell']['price'], amount1)
        if orderId:
            logging.info('[orderId]' + str(orderId))
            status = self.getOrderInfo(symbols[0], orderId)
            if status != 2:
                sleep(0.5)
                status = self.getOrderInfo(symbols[0], orderId)
                if status != 2:
                    self.cancelOrder(symbols[0], orderId)
                    logging.info('cancelOrder!')
                    # return
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order succssed!]')
        else:
            self.toBtc()
            logging.info('[order failed!]')
            return

        logging.debug('step2')
        self.getBalance()
        logging.info('[Balance]')
        logging.info(self.balance)
        amount2 = self.balance[symbols[1].split('_')[0]]
        orderId = self.trade(symbols[1], 'sell', depth[symbols[1]]['buy']['price'], amount2)
        if orderId:
            logging.info('[orderId]' + str(orderId))
            status = self.getOrderInfo(symbols[1], orderId)
            if status != 2:
                sleep(0.5)
                status = self.getOrderInfo(symbols[1], orderId)
                if status != 2:
                    self.cancelOrder(symbols[1], orderId)
                    logging.info('cancelOrder!')
                    # return
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order succssed!]')
        else:
            self.toBtc()
            logging.info('[order failed!]')
            return

        logging.debug('step3')
        self.getBalance()
        logging.info('[Balance]')
        logging.info(self.balance)
        amount3 = round((self.balance[symbols[2].split('_')[1]] / depth[symbols[2]]['sell']['price']) * 0.998, 8)
        orderId = self.trade(symbols[2], 'buy', depth[symbols[2]]['sell']['price'], amount3)
        if orderId:
            logging.info('[orderId]' + str(orderId))
            status = self.getOrderInfo(symbols[2], orderId)
            if status != 2:
                sleep(0.5)
                
                status = self.getOrderInfo(symbols[2], orderId)
                if status != 2:
                    self.cancelOrder(symbols[2], orderId)
                    logging.info('cancelOrder!')
                    # return
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order succssed!]')
        else:
            self.toBtc()
            logging.info('[order failed!]')
            return

        logging.debug('step4')
        self.getBalance()
        logging.info('[Balance]')
        logging.info(self.balance)
        amount4 = self.balance[symbols[3].split('_')[0]]
        orderId = self.trade(symbols[3], 'sell', depth[symbols[3]]['buy']['price'], amount4)
        if orderId:
            logging.info('[orderId]' + str(orderId))
            status = self.getOrderInfo(symbols[3], orderId)
            if status != 2:
                sleep(0.5)
                status = self.getOrderInfo(symbols[3], orderId)
                if status != 2:
                    self.cancelOrder(symbols[3], orderId)
                    logging.info('cancelOrder!')
                    self.toBtc()
                    return
                else:
                    logging.info('[order succssed!]')
            else:
                logging.info('[order succssed!]')
        else:
            self.toBtc()
            logging.info('[order failed!]')
            return

    def policy(self, allsymbol):
        self.getBalance()
        coins = self.getCoinList(allsymbol)
        tradesymbol = self.getTradeSymbol(coins)
        pp = []
        for symbols in tradesymbol:
            # print(symbols)
            # self.toBtc()
            profit, amount = self.getTradeAmount(symbols)
            if amount > 0.0001:
                one = {}
                one['symbol'] = symbols
                one['amount'] = amount
                one['total'] = profit * amount
                pp.append(one)
                # self.doTrade(symbols, amount)
                logging.debug(symbols)
                logging.debug('profit: %f' % profit)
                logging.debug('amount: %f' % amount)
                logging.debug(depth[symbols[0]])
                logging.debug(depth[symbols[1]])
                logging.debug(depth[symbols[2]])
                logging.debug(depth[symbols[3]])
        if len(pp) != 0:
            st = sorted(pp, key=itemgetter('total'))
            self.doTrade(st[-1]['symbol'],st[-1]['amount'])

if __name__ == '__main__':
    api = okex()
    symbols = ['eos_btc', 'ltc_btc']
    # while(1):
    #     api.policy(SYMBOL)
    global depth
    while(1):
        threads = []
        for ss in SYMBOL:
            s = ss + "_btc"
            threads.append(threading.Thread(target=api.getDepth, args=(s,)))
            e = ss + "_eth"
            threads.append(threading.Thread(target=api.getDepth, args=(e,)))
        # print(time())
        for t in threads:
            t.start()
        t.join()
        # print(depth)
        api.policy(SYMBOL)
        depth = {}
        # print(time())
        sleep(1)