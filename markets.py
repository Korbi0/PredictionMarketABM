import random
import numpy as np
from math import isnan
random.seed(1)



class Market_Generic():
  def __init__(self, traders, mode='binary', exchange_fee=0.0):
    self.traders = traders # List of traders
    self.mode = mode
    self.exchange_fee = exchange_fee
    assert(self.mode in ['binary', 'index'])
    self.yes_prices = [] # List of prices at which bets on 'yes' have been traded
    self.no_prices = [] # List of prices at which bets on 'no' have been traded
    

  def run_market(self, trading_rounds):
    """
    Runs the market for a given number of trading rounds and reports
    the market's credence after theses rounds
    """

    for i in range(trading_rounds):
      trade = self.trading_round()
      if trade is None:
        continue
      elif trade['direction'] == 'yes':
        self.yes_prices.append(trade['price'])
      elif trade['direction'] == 'no':
        self.no_prices.append(trade['price'])
      else:
        raise ValueError("direction must be yes or no")
    return self.get_credence()

  def trading_round(self):
    """
    Should implement an event at which a trade may take place
    If a trade takes place, should return a dictionary of the form
    {'direction': 'no' or 'yes', 'price': price, 'buyer': trader1, 'seller': trader2}
    if no trade takes place, should return None
    """
    raise NotImplementedError("This method must be implemented in the child class")
  
  def get_credence(self):
    """
    Returns the market's credence
    """
    raise NotImplementedError("This method must be implemented in the child class")

class SimplifiedDoubleAuctionMarket(Market_Generic):
  """
  A market where a trade only takes place if there are two traders
  which can agree to a price
  """
  def __init__(self, traders, mode, exchange_fee=0.):
      super().__init__(traders, mode, exchange_fee)
      assert(len(self.traders) > 0)
      self.yes_prices = []
      self.uncertainties = []

      
      self.uncertainty = 1
      self.uncertainties.append(self.uncertainty)
    
  def trading_round(self):
      seller, buyer = random.sample(self.traders, 2)

      if seller.expected_income_yes_share > buyer.expected_income_yes_share:
          seller, buyer = buyer, seller
      
      proposed_price = ((seller.expected_income_yes_share
                        + buyer.expected_income_yes_share)
                        / 2)
      seller_price = proposed_price - self.exchange_fee
      buyer_price = proposed_price + self.exchange_fee
      if (seller.decide_on_trade(seller_price, buysell=-1, direction=1, 
            market_uncertainty=self.uncertainty)
          and
          buyer.decide_on_trade(buyer_price,
              buysell=1, direction=1, market_uncertainty=self.uncertainty)):
          seller.make_trade(1, -1, 1., seller_price)
          buyer.make_trade(1, 1, 1., buyer_price)
          combined_prices = self.yes_prices + [1 - x for x in self.no_prices]
          uncertainty = np.std(combined_prices)
          if not isnan(uncertainty):
            self.uncertainty = uncertainty
            self.uncertainties.append(self.uncertainty)
          return {'direction': 'yes',
                  'price': proposed_price,
                  'buyer': buyer,
                  'seller': seller}
      else:
        return None
      
  def get_credence(self):
      if len(self.yes_prices) == 0 and len(self.no_prices) == 0:
          return 0.5
      else:
          return np.mean(self.yes_prices + [1 - x for x in self.no_prices])
        
    