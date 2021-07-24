#requires python version >= 3.7
#requires numpy



from dataclasses import dataclass, field
import numpy as np
import math



@dataclass
class Enforce_Type:

    def validate(self):
        correct_type = True
        for field_name, field_def in self.__dataclass_fields__.items():
            actual_type = type(getattr(self, field_name))
            if actual_type != field_def.type:
                print(f"\t{field_name}: '{actual_type}' instead of '{field_def.type}'")
                correct_type = False
        return correct_type
     
    def __post_init__(self):
        if not self.validate():
            raise ValueError('Wrong types')

@dataclass
class ClientOrder(Enforce_Type):
    instrument_id: int
    quantity: int
    traded_price: float

@dataclass
class MarketUpdate(Enforce_Type):
    instrument_id: int
    market_price: float

@dataclass
class TradeBook(Enforce_Type):
    positions: list
    market_prices: list
    hedge: bool = field(init=True,default=False)
    risk: int = field(init=True,default=1)
    volatility: list = field(init=True,default_factory=list)
    cost:list = field(init=True, default_factory=list)
    pnl: float = field(init=False,default=0.0)
    pnl_array: list = field(init=False,default_factory=list)


    def __post_init__(self):
        if not self.validate():
            raise ValueError('Wrong types')

        if any(not isinstance(x, int) for x in self.positions):
            raise ValueError('Wrong types - positions must be a list of integers')
        
        if any(not isinstance(y, float) for y in self.market_prices):
            raise ValueError('Wrong types - market prices must be a list of floats')
        
        if any((len(lst) != len(self.positions)) for lst in [self.market_prices,self.volatility,self.cost]):
            raise IndexError("lists must be of the same length")

        self.pnl_array.append(self.pnl)

    def add_client_order(self,ClientOrder):
        self.positions[ClientOrder.instrument_id-1] += ClientOrder.quantity
        self.pnl += -round((ClientOrder.traded_price)*ClientOrder.quantity,5)
        if self.hedge:
            if self.positions[ClientOrder.instrument_id-1] > 0:
                a = self.risk*self.cost[ClientOrder.instrument_id-1]
                b = 2*(math.pow(self.volatility[ClientOrder.instrument_id-1],2))
                delta_q = min((a/b)-self.positions[ClientOrder.instrument_id-1],0)
                self.positions[ClientOrder.instrument_id-1]+= delta_q
                self.pnl -= round(self.market_prices[ClientOrder.instrument_id-1]*delta_q,5)
            elif self.positions[ClientOrder.instrument_id-1] < 0:
                a = self.risk*self.cost[ClientOrder.instrument_id-1]
                b = 2*(math.pow(self.volatility[ClientOrder.instrument_id-1],2))
                delta_q = max((-1*a/b)-self.positions[ClientOrder.instrument_id-1],0)
                self.positions[ClientOrder.instrument_id-1]+= delta_q
                self.pnl -= round(self.market_prices[ClientOrder.instrument_id-1]*delta_q,5)
        self.pnl_array.append(self.pnl)


    def update_market_price(self,MarketUpdate):
        self.market_prices[MarketUpdate.instrument_id-1]=round(MarketUpdate.market_price,5)

    def get_pnl(self):
        return self.pnl

    def get_maximum_drawdown(self):
        pnl_array=np.array(self.pnl_array)
        acc_max = np.maximum.accumulate(pnl_array)
        return (pnl_array-acc_max).min()



    
    