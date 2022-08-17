#!/usr/bin/env python
# coding: utf-8

# In[1]:


import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import string
from datetime import datetime
from dateutil.relativedelta import relativedelta


# In[2]:


## The point of the program is to help visualize option structure payoffs using real data
## You must create Asset(s), which can be stocks or options, then add them to a Portfolio
## Each asset, if valid, will have underlying, quantity (can be +/-)
## In addition, Options will have strike, cp tag (call or put), and maturity
## Once added to the portfolio, the portfolio total_payoff function can return:
    ## 1) a range of hypothetical prices for the underlying, ranging from 0 to some upper bound
    ## 2) a corresponding range of total payoffs at option maturity


# In[3]:


##Maturity/exp is YYYY-MM-DD
##option symbol is XYZYYMMDD(C/P) then eight digits with three decimal places
##e.g., $410.00 strike will be 00410000


# In[4]:


def callpayoff(price, strike, premium):
    if price < strike:
        return premium*(-100)
    else:
        return (price-strike)*100 - premium*100
def putpayoff(price, strike, premium):
    if price > strike:
        return premium*(-100)
    else:
        return (strike-price)*100 - premium*100


# In[5]:


class Asset:
    def __init__(self,underlying,quantity):
        self.underlying = underlying
        self.quantity = quantity
        self.data = []
    def get_underlying(self):
        return self.underlying
    def get_quantity(self):
        return self.quantity
    def get_data(self):
        return self.data


# In[6]:


class Stock(Asset):
    def __init__(self,underlying,quantity):
        super().__init__(underlying,quantity)
        self.data = []
    #finding the price from the loaddata function
    def loadstockdata(self):
    #getting the data from Yahoo finance
        self.data = yf.Ticker(self.underlying)
    def find_bidask(self):
        try:
            bid = self.data.info['bid']
            ask = self.data.info['ask']
            return bid, ask
        except:
            pass
    def get_type(self):
        return "Stock"


# In[7]:


class Option(Asset):
    def __init__(self,strike,cp,underlying,quantity,maturity):
        super().__init__(underlying,quantity)
        self.strike = strike
        self.cp = cp
        self.maturity = maturity
        self.symbol = str.upper(underlying)+pd.to_datetime(maturity).strftime("%y%m%d")+str.upper(cp)+str(int(strike*1000)).rjust(8, '0')
        self.data = {'calls':'','puts':''}
    def get_strike(self):
        return self.strike
    def get_cp(self):
        return self.cp
    def get_maturity(self):
        return self.maturity
    def loadoptiondata(self):
        #getting the data from Yahoo finance
        data = yf.Ticker(self.underlying)
        try:
            calls = pd.DataFrame(data.option_chain(self.maturity)[0])
            puts = pd.DataFrame(data.option_chain(self.maturity)[1])
            self.data.update({'calls': calls})
            self.data.update({'puts': puts})
        except:
            pass
    def find_bidask(self):
        try:            
            if str.upper(self.cp) == 'C':
                data = self.data['calls']
            else:
                data = self.data['puts']
            data = data[data['contractSymbol']==self.symbol].reset_index(drop=True)
            bid = data['bid'][0]
            ask = data['ask'][0]
            return bid,ask
        except:
            pass
    def get_type(self):
        return "Option"


# In[8]:


class Portfolio:
    def __init__(self):
        self.calls = []
        self.puts = []
        self.stock = []
        self.data = {}
        
    def add_position(self,position):
        if position.get_type() == "Stock":
            self.stock.append(position)
            position.loadstockdata()
            self.data[position] = position.get_data()
        else:
            position.loadoptiondata()
            if str.upper(position.get_cp()) == "C":
                self.calls.append(position)
                self.data[position] = position.get_data()['calls']
            else:
                self.puts.append(position)
                self.data[position] = position.get_data()['puts']
                
    def stock_payoff(self):
        delta = 0
        intercept = 0
        for i in range(len(self.stock)):
            try:
                delta += self.stock[i].get_quantity()
                intercept -= self.stock[i].find_bidask()[0] * self.stock[i].get_quantity()
            except:
                pass
        return delta, intercept
    
    def option_payoff(self):
        if len(self.calls) > 0:
            a = int(max([x.get_strike() for x in self.calls]))
        else:
            a = 0
        if len(self.puts) > 0:
            b = int(max([x.get_strike() for x in self.puts]))
        else:
            b = 0
        prices = np.arange(0, round(1.5*max(a,b)), 0.10).tolist()

        ##a,b,prices give the range of the x axis (underlying price)
        payoffs = []
        for i in prices:
            temppayoff = 0
            for j in self.calls:
                if j.get_quantity()>0: ##if you're long the option, use the ask as the premium
                    try:
                        temppayoff += callpayoff(i,j.get_strike(),j.find_bidask()[1])*j.get_quantity()
                    except:
                        pass
                else: ## if you're short the option, use the bid as the premium
                    try:
                        temppayoff += callpayoff(i,j.get_strike(),j.find_bidask()[0])*j.get_quantity()
                    except:
                        pass
            for k in self.puts:
                if k.get_quantity()>0:
                    try:
                        temppayoff += putpayoff(i,k.get_strike(),k.find_bidask()[1])*k.get_quantity()
                    except:
                        pass
                else:
                    try:
                        temppayoff += putpayoff(i,k.get_strike(),k.find_bidask()[0])*k.get_quantity()
                    except:
                        pass
            payoffs.append(temppayoff)
        return prices, payoffs
    
    def total_payoff(self):
        prices = self.option_payoff()[0]
        if len(prices) <1:
            prices = np.arange(0, 100, 0.5).tolist()
        if len(self.option_payoff()[0]) > 0:
            optionpayoff = self.option_payoff()[1]
        else:
            optionpayoff = [0]*500
        sd = self.stock_payoff()[0]
        si = self.stock_payoff()[1]
        stockpayoff = [sd*price+si for price in prices]
        totalpayoff = [s+o for s,o in zip(stockpayoff,optionpayoff)]
        return prices, totalpayoff


# In[ ]:





# In[ ]:





# In[9]:


### SAMPLE CODE BELOW (1 call plus short 100 underlying)
#spyc = Option(400,'c','spy',1,'2022-08-19')
#spy = Stock('spy',-100)
#p = Portfolio()
#p.add_position(spyc)
#p.add_position(spy)
#pd.DataFrame(p.total_payoff()).to_csv('testoption.csv')


# In[ ]:





# In[10]:


### MORE SAMPLE CODE (adding in two invalid positions)
#spyc = Option(400,'c','spy',1,'2022-08-19')
#errorp = Option(400,'p','c23',1,'2022-08-19')
#errorstock = Stock('c23',1)
#p1 = Portfolio()
#p1.add_position(spyc)
#p1.add_position(errorstock)
#p1.add_position(errorp)
#pd.DataFrame(p1.total_payoff()).to_csv('testerror.csv')

