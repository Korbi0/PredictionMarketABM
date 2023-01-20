from multipledispatch import dispatch
import random
from agent import Agent

from sympy.abc import b, x, y
random.seed(1)

from mathtools import *

def get_participant(true_value,
                    mode,
                    take_market_uncertainty_into_account=False,
                    credence_distribution=truncated_distribution,
                    pright=.5):

  """
  pright comes into action only for participants in binary markets.
  pright is the probability of the belief being true
  """
  if mode == "binary":
      if not pright:
        belief = belief = np.random.randint(2)
      else:
        gets_it_right = np.random.uniform(0.0, 1.0) < pright
        if gets_it_right:
          belief = true_value
        else:
          belief = 1 - true_value
      uncertainty = np.random.uniform(0.1, 0.5)


      # Assumption that people who are correct are more confident
      if abs(belief - true_value) < 0.1:
        uncertainty = np.random.uniform(0.01, 0.3)

      participant = Market_Participant_binary(belief, uncertainty)
      return participant

  elif mode == "index":
      # Mode is index
      expected_result = np.random.uniform(0., 1.)

      epistemic_uc_about_outcome = abs(true_value - expected_result)

      participant = Market_Participant_continuous(expected_result,
        epistemic_uc_about_outcome,
        credence_distribution,
        take_market_uncertainty_into_account=take_market_uncertainty_into_account)

      return participant

  else:
    raise ValueError("mode must be binary or index")

class Market_Participant(Agent):
    def __init__(self,
                    expected_result,
                    uncertainty,
                    take_market_uncertainty_into_account,
                    credence_distribution=None):
        super().__init__()
        if credence_distribution:
            self.credence_distribution = credence_distribution
        self.take_market_uncertainty_into_account = take_market_uncertainty_into_account
        self.expected_result = expected_result
        self.uncertainty = uncertainty
        self.get_credence()
        self.get_expected_income_of_shares()
        self.validate()
    

    def get_credence(self):
        """
        Should set self.credence to the credence of the participant in the proposition
        """
        raise NotImplementedError("get_credence must be implemented")

    def get_expected_income_of_shares(self):
        """
        Should set self.expected_income_yes_share
        and self.expected_income_no_share to the expected income of a bet on 
        'yes' and of a bet on 'no' respectively
        """
        raise NotImplementedError("get_expected_income_of_shares must be implemented")

    def validate(self):
        """
        Validate that all necessary attributes have been set
        """
        try:
            assert(self.credence)
            assert(self.expected_income_yes_share)
            assert(self.expected_income_no_share)
        except:
            print('error')


    def decide_on_trade(self, offered_price, direction=1, buysell=1, market_uncertainty=None):
        """
        offered_price: price at which trade would take place
        buysell: 1 means 'buy', -1 means 'sell
        direction: 1 means 'yes', 0 means 'no'
        """
        direction, buysell = self.work_with_alternative_inputs(direction, buysell)

        assert(buysell in [1, -1])
        assert(direction in [1, 0])
        expected_income_of_share = (direction * self.expected_income_yes_share
                                    + (1 - direction) * self.expected_income_no_share)
        expected_value_of_trade = buysell * (expected_income_of_share - offered_price)

        if not self.take_market_uncertainty_into_account or not market_uncertainty:
            return expected_value_of_trade > 0.
        else:
            # A trader who takes market certaity into account will be
            # more likely to trade if his own uncertainty
            # is lower than that of the market
            market_assessment = market_uncertainty > self.uncertainty

            return expected_value_of_trade > 0. and market_assessment



class Market_Participant_binary(Market_Participant):
    """
    participant for the case where the question is binary

    The participant holds a belief of either 1 (yes) or 0 (no)

    He has an uncertainty in [0, 0.5) which describes the probability he assigns to
    the possibility that his belief is wrong
    """
    def __init__(self, belief, uncertainty):
        super().__init__(belief, uncertainty, take_market_uncertainty_into_account=False)
        if not self.expected_result:
            (self.expected_income_yes_share, self.expected_income_no_share) = (
                self.expected_income_no_share, self.expected_income_yes_share
                )

    def get_credence(self):
        self.credence = 1 - self.uncertainty
    
    def get_expected_income_of_shares(self):
        self.expected_income_yes_share = self.credence
        self.expected_income_no_share = 1 - self.credence



class Market_Participant_continuous(Market_Participant):
    """
    participant for the case where the question is continous (index market)

    """

    def __init__(self,
                    expected_result,
                    uncertainty,
                    credence_distribution,
                    take_market_uncertainty_into_account=False):
        super().__init__(expected_result,
                        uncertainty,
                        take_market_uncertainty_into_account,
                        credence_distribution=credence_distribution)
        self.take_market_uncertainty_into_account = take_market_uncertainty_into_account

    def get_credence(self):
       self.credence = self.credence_distribution(self.expected_result,
                                                    self.uncertainty, 0., 1.,)


    def get_expected_income_of_shares(self):
        lb = self.credence.ppf(0.001)
        ub = self.credence.ppf(0.999)
        self.expected_income_yes_share = self.credence.expect(lambda x: x, lb=lb, ub=ub)
        self.expected_income_no_share = self.credence.expect(lambda x: (1 - x), lb=lb, ub=ub)
