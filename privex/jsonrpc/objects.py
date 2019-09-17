from typing import Union, List, Dict, Tuple
from privex.jsonrpc.core import atomic_to_decimal, decimal_to_atomic
from decimal import Decimal

class ObjBase:
    """
    A base class to be extended by data storage classes, allowing their attributes to be
    accessed as if the class was a dict/list.
    
    Also allows the class to be converted into a dict/list if raw_data is filled, like so: ``dict(SomeClass())``
    """

    def __init__(self, raw_data: Union[list, tuple, dict] = None, *args, **kwargs):
        self.raw_data = {} if not raw_data else raw_data  # type: Union[list, tuple, dict]
        super(ObjBase, self).__init__(raw_data, *args, **kwargs)
    
    def __iter__(self):
        r = self.raw_data
        if type(r) is dict:
            for k, v in r.items(): yield (k, v,)
            return
        for k, v in enumerate(r): yield (k, v,)

    def __getitem__(self, key):
        """
        When the instance is accessed like a dict, try returning the matching attribute.
        If the attribute doesn't exist, or the key is an integer, try and pull it from raw_data
        """
        if type(key) is int: return self.raw_data[key]
        if hasattr(self, key): return getattr(self, key)
        if key in self.raw_data: return self.raw_data[key]
        raise KeyError(key)

    @classmethod
    def from_list(cls, obj_list: List[dict]):
        """
        Converts a ``list`` of ``dict`` 's into a ``Generator[cls]`` of instances of the class you're calling this from.

        **Example:**

            >>> _balances = [dict(account='someguy123', symbol='SGTK', balance='1.234')]
            >>> balances = list(SEBalance.from_list(_balances))
            >>> type(balances[0])
            <class 'privex.steemengine.objects.SEBalance'>
            >>> balances[0].account
            'someguy123'
        
        """
        for tx in obj_list:
            yield cls(**tx)

    def __repr__(self):
        return self.__str__()


class MoneroPayment(ObjBase):
    """
    Represents a Payment from ``get_payments`` in Monero
    """
    def __init__(self, address: str = "", amount: int = 0, block_height: int = None, payment_id = "", 
                 subaddr_index:dict = {}, tx_hash="", unlock_time:int = 0, **kwargs):
        self.address, self.amount, self.block_height, self.payment_id = address, amount, block_height, payment_id
        self.subaddr_index, self.tx_hash, self.unlock_time = subaddr_index, tx_hash, unlock_time
        self.raw_data = {
            **kwargs, 
            **dict(
                address=address, amount=amount, block_height=block_height, payment_id=payment_id, 
                subaddr_index=subaddr_index, tx_hash=tx_hash, unlock_time=unlock_time
            )
        }
    
    @property
    def decimal_amount(self) -> Decimal:
        """Return the atomic integer :py:attr:`.amount` as a normal Decimal amount"""
        return atomic_to_decimal(self.amount)

