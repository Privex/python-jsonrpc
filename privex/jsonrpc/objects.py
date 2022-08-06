import dataclasses
from dataclasses import dataclass
from typing import Union, List, Dict, Tuple, Type, Iterable, Optional

from privex.helpers import DictObject, Dictable, empty

from privex.jsonrpc.core import atomic_to_decimal, decimal_to_atomic
from decimal import Decimal
import logging

log = logging.getLogger(__name__)

AnyNum = Union[int, float, Decimal, str]


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


class BaseData(Dictable):
    raw_data: Union[dict, DictObject]
    _dict_exclude = ['raw_data', '_dict_exclude', '_dict_listify']
    _dict_listify = ['inputs', 'outputs']
    
    def __iter__(self):
        # r = self.raw_data
        # itr = r.items() if isinstance(r, dict) else enumerate(r)
        # for k, v in itr:
        #     yield (k, v,)
        for k, v in self.__dict__.items():
            if k.startswith('_electrum_ins') or k.startswith('__'):
                continue
            if k in self._dict_exclude: continue
            if k in self._dict_listify and isinstance(v, (list, set, iter)):
                v = [dict(a) for a in v]
            if isinstance(v, BaseData):
                v = dict(v)
            yield k, v
    
    def __getitem__(self, key):
        """
        When the instance is accessed like a dict, try returning the matching attribute.
        If the attribute doesn't exist, or the key is an integer, try and pull it from raw_data
        """
        if type(key) is int: return self.raw_data[key]
        if hasattr(self, key): return getattr(self, key)
        if key in self.raw_data: return self.raw_data[key]
        raise KeyError(key)
    
    def __setitem__(self, key, value):
        if hasattr(self, key):
            return setattr(self, key, value)
        if key in self.raw_data:
            self.raw_data[key] = value
            return
        raise KeyError(key)
    
    def get(self: Union[Type[dataclass], dataclass], key, fallback=None):
        names = set([f.name for f in dataclasses.fields(self)])
        if key in names:
            return getattr(self, key)
        return fallback
    
    @classmethod
    def from_dict(cls: Type[dataclass], obj):
        names = set([f.name for f in dataclasses.fields(cls)])
        clean = {k: v for k, v in obj.items() if k in names}
        if 'raw_data' in names:
            clean['raw_data'] = DictObject(clean.get('raw_data')) if 'raw_data' in clean else DictObject(obj)
        return cls(**clean)
    
    @classmethod
    def from_list(cls: Type[dataclass], obj_list: Iterable[dict]):
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
            yield cls.from_dict(tx)


class MoneroPayment(ObjBase):
    """
    Represents a Payment from ``get_payments`` in Monero
    """

    def __init__(self, address: str = "", amount: int = 0, block_height: int = None, payment_id="",
                 subaddr_index: dict = {}, tx_hash="", unlock_time: int = 0, **kwargs):
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


class MoneroTransfer(ObjBase):
    """
    Represents a Transfer item from ``get_transfers`` in Monero
    """

    def __init__(self, address: str = "", amount: int = 0, confirmations: int = 0, fee: int = 0,
                 height: int = 0, payment_id="", subaddr_index: dict = None, subaddr_indices: List[dict] = None,
                 timestamp: int = None, txid: str = "", type: str = "", unlock_time: int = 0, note: str = None,
                 suggested_confirmations_threshold: int = 0, double_spend_seen: bool = False, **kwargs):

        if subaddr_indices is None:
            subaddr_indices = []
        if subaddr_index is None:
            subaddr_index = {}

        self.address = address
        self.amount = amount
        self.confirmations = confirmations
        self.double_spend_seen = double_spend_seen
        self.fee = fee
        self.height = height
        self.note = note
        self.payment_id = payment_id
        self.subaddr_index = subaddr_index
        self.subaddr_indices = subaddr_indices
        self.timestamp = timestamp
        self.txid = txid
        self.type = type
        self.unlock_time = unlock_time
        self.suggested_confirmations_threshold = suggested_confirmations_threshold

        dicdata = dict(
            address=address, amount=amount, confirmations=confirmations, double_spend_seen=double_spend_seen, fee=fee,
            height=height, note=note, payment_id=payment_id, subaddr_index=subaddr_index, unlock_time=unlock_time,
            subaddr_indices=subaddr_indices, timestamp=timestamp, txid=txid, type=type,
            suggested_confirmations_threshold=suggested_confirmations_threshold
        )

        self.raw_data = {**kwargs, **dicdata}

    @property
    def decimal_amount(self) -> Decimal:
        """Return the atomic integer :py:attr:`.amount` as a normal Decimal amount"""
        return atomic_to_decimal(self.amount)

    @property
    def decimal_fee(self) -> Decimal:
        """Return the atomic integer :py:attr:`.fee` as a normal Decimal amount"""
        return atomic_to_decimal(self.fee)

    def __str__(self):
        return f'<MoneroTransfer amount="{self.decimal_amount} XMR", address="{self.address}" ' \
               f'confirmations={self.confirmations} >'

    def __repr__(self):
        return self.__str__()


class ElectrumInstanceInject(BaseData):
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC"
    
    def set_electrum_instance(self, electrum_ins):
        self._electrum_instance = electrum_ins

    @classmethod
    def from_dict(cls: Type[dataclass], obj, electrum_ins=None):
        obj = dict(obj)
        names = set([f.name for f in dataclasses.fields(cls)])
        clean = {k: v for k, v in obj.items() if k in names}
        if 'raw_data' in names:
            clean['raw_data'] = DictObject(clean.get('raw_data')) if 'raw_data' in clean else DictObject(obj)
        if electrum_ins: clean['_electrum_instance'] = electrum_ins
        return cls(**clean)

    @classmethod
    def from_list(cls: Type[dataclass], obj_list: Iterable[dict], electrum_ins=None):
        for tx in obj_list:
            yield cls.from_dict(tx, electrum_ins=electrum_ins)


class ElectrumFullTX(ElectrumInstanceInject):
    tx_hash: str
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC"
    _full_data: "ElectrumTransaction"
    _dict_exclude = BaseData._dict_exclude + ['_electrum_instance', '_full_data']
    
    def __iter__(self):
        d = dict(super(ElectrumFullTX, self).__iter__())
        try:
            if 'inputs' not in d and self.full_data is not None:
                d['inputs'] = self.full_data.outputs
            if 'outputs' not in d and self.full_data:
                d['outputs'] = self.full_data.outputs
        except Exception as e:
            log.warning("Ignoring exception while extracting 'inputs' and 'outputs' via full_data: %s %s", type(e), str(e))
            d['inputs'], d['outputs'] = d.get('inputs', []), d.get('outputs', [])
        
        for k, v in d.items():
            # if k in self._dict_exclude: continue
            # if k in ['inputs', 'outputs'] and isinstance(v, (list, set, iter)):
            #     v = [dict(a) for a in v]
            yield k, v
    
    @property
    def inputs(self) -> List[Union[dict, "ElectrumInput"]]:
        """Returns a list of :class:`.ElectrumInput` objects queried via :attr:`.full_data`"""
        return self.full_data.inputs
    
    @property
    def outputs(self) -> List[Union[dict, "ElectrumOutput"]]:
        """Returns a list of :class:`.ElectrumOutput` objects queried via :attr:`.full_data`"""
        return self.full_data.outputs
    
    @property
    def locktime(self) -> Optional[int]:
        """Returns a the transaction lock time as an :class:`.int` queried from :attr:`.full_data`"""
        return self.full_data.locktime
    
    @property
    def txid(self) -> str:
        """Alias for :attr:`.tx_hash"""
        return self.tx_hash
    
    @property
    def full_data(self) -> "ElectrumTransaction":
        """
        Helper property for :meth:`.get_full` with automatic instance caching.
        
        Caches the :class:`.ElectrumTransaction` result from :meth:`.get_full` into :attr:`._full_data`,
        allowing class properties such as :attr:`.inputs` and :attr:`.outputs` to be used without constantly
        re-querying Electrum.
        """
        if not self._full_data:
            self._full_data = self.get_full()
        return self._full_data
    
    def get_full(self, electrum_ins=None) -> "ElectrumTransaction":
        """
        Get the full :class:`.ElectrumTransaction` object from Electrum using this object's :attr:`.txid` transaction ID.
        
        Tries to use the Electrum instance passed via the parameter ``electrum_ins``. If it isn't specified / is ``None``,
        then it will attempt to fallback to this object's :attr:`._electrum_instance`
        
        :param privex.jsonrpc.ElectrumRPC.ElectrumRPC electrum_ins:
        :raises AttributeError: When neither :attr:`._electrum_instance` nor parameter ``electrum_ins`` contain valid
                                :class:`.ElectrumRPC` instances.
        :return ElectrumTransaction full_tx: A :class:`.ElectrumTransaction` object containing full TX details.
        """
        if not electrum_ins:
            electrum_ins = self._electrum_instance
        if not electrum_ins:
            raise AttributeError(
                f"{self.__class__.__name__}.get_full was not passed a valid electrum_ins, and self._electrum_instance "
                f"is not set. Cannot get full data without electrum instance."
            )
        
        tx = electrum_ins.get_transaction(self.txid)
        decoded = electrum_ins.deserialize(tx)
        return decoded

    @property
    def total_out(self) -> Decimal:
        """
        Calculate the total amount of coins (decimal) that were outputted in this transaction

        Alias for :meth:`privex.jsonrpc.ElectrumRPC.ElectrumTransaction.total_out`
        """
        return self.full_data.total_out

    def total_out_address(self, address: str) -> Decimal:
        """
        Similar to :meth:`.total_out` - but only count outputs which were destined for ``address``
        
        Alias for :meth:`privex.jsonrpc.ElectrumRPC.ElectrumTransaction.total_out_address`
        
        :param str address: The wallet address to calculate total outputted coins amount for
        :return Decimal total: The total amount of coins which were transferred to ``address``
        """
        return self.full_data.total_out_address(address=address)


@dataclass
class ElectrumHistoryItem(ElectrumFullTX):
    tx_hash: str = None
    height: int = None
    fee: int = None
    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""
    # noinspection PyUnresolvedReferences
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC" = dataclasses.field(default=None, repr=False)
    _full_data: "ElectrumTransaction" = dataclasses.field(default=None, repr=False)
    
    @property
    def fee_decimal(self) -> Decimal:
        return Decimal(str(self.fee)) / Decimal('10e7')


@dataclass
class ElectrumUnspent(ElectrumFullTX):
    tx_hash: str = None
    tx_pos: int = None
    height: int = None
    value: int = None
    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""
    # noinspection PyUnresolvedReferences
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC" = dataclasses.field(default=None, repr=False)
    _full_data: "ElectrumTransaction" = dataclasses.field(default=None, repr=False)
    
    @property
    def value_decimal(self) -> Decimal:
        return Decimal(str(self.value)) / Decimal('10e7')


@dataclass
class ElectrumInput(ElectrumFullTX):
    prevout_hash: str = None
    prevout_n: int = None
    coinbase: bool = None
    nsequence: int = None
    scriptSig: str = None
    witness: str = None
    value_sats: int = None
    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""

    # noinspection PyUnresolvedReferences
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC" = dataclasses.field(default=None, repr=False)
    _full_data: "ElectrumTransaction" = dataclasses.field(default=None, repr=False)
    
    @property
    def txid(self) -> str:
        return self.prevout_hash
    
    @property
    def previous_output(self) -> "ElectrumOutput":
        return self.outputs[self.prevout_n]
    
    @property
    def previous_value(self) -> Decimal:
        return self.previous_output.value_decimal

    @property
    def previous_value_sats(self) -> int:
        return self.previous_output.value_sats
    
    @property
    def value(self):
        return self.value_sats
    
    @value.setter
    def value(self, value):
        self.value_sats = value
    
    def __post_init__(self):
        if empty(self.value_sats) and not empty(self.raw_data.get('value')):
            self.value_sats = self.raw_data.get('value')


@dataclass
class ElectrumOutput(BaseData):
    address: str
    value_sats: int = None
    scriptpubkey: str = None
    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""

    @property
    def value_decimal(self) -> Decimal:
        return Decimal(str(self.value_sats)) / Decimal('10e7')

    @property
    def value(self):
        return self.value_sats

    @value.setter
    def value(self, value):
        self.value_sats = value

    def __post_init__(self):
        if empty(self.value_sats) and not empty(self.raw_data.get('value')):
            self.value_sats = self.raw_data.get('value')


@dataclass
class ElectrumBalanceResponse(BaseData):
    confirmed: Decimal = dataclasses.field(default_factory=Decimal)
    unconfirmed: Decimal = dataclasses.field(default_factory=Decimal)

    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""
    
    def __post_init__(self):
        if self.confirmed is not None and not isinstance(self.confirmed, Decimal):
            self.confirmed = Decimal(str(self.confirmed))
        if self.unconfirmed is not None and not isinstance(self.unconfirmed, Decimal):
            self.unconfirmed = Decimal(str(self.unconfirmed))


@dataclass
class ElectrumTransaction(ElectrumInstanceInject):
    version: int = 0
    locktime: int = None
    inputs: List[Union[dict, ElectrumInput]] = dataclasses.field(default_factory=list)
    outputs: List[Union[dict, ElectrumOutput]] = dataclasses.field(default_factory=list)
    raw_data: Union[dict, DictObject] = dataclasses.field(default_factory=DictObject, repr=False)
    """The raw, unmodified data that was passed as kwargs, as a dictionary"""
    # noinspection PyUnresolvedReferences
    _electrum_instance: "privex.jsonrpc.ElectrumRPC.ElectrumRPC" = dataclasses.field(default=None, repr=False)
    
    def __post_init__(self):
        new_inputs, new_outputs = [], []
        
        if isinstance(self.inputs, (list, set, iter)):
            for i in self.inputs:
                if isinstance(i, ElectrumInput):
                    new_inputs.append(i)
                    continue
                try:
                    n = ElectrumInput.from_dict(i, electrum_ins=self._electrum_instance)
                    new_inputs.append(n)
                except Exception as e:
                    log.warning("Failed to convert input into ElectrumInput... Using original: %s", i)
                    log.warning("Exception was: %s %s", type(e), str(e))
                    new_inputs.append(i)
            self.inputs = new_inputs

        if isinstance(self.outputs, (list, set, iter)):
            for i in self.outputs:
                if isinstance(i, ElectrumOutput):
                    new_outputs.append(i)
                    continue
                try:
                    n = ElectrumOutput.from_dict(i)
                    new_outputs.append(n)
                except Exception as e:
                    log.warning("Failed to convert input into ElectrumOutput... Using original: %s", i)
                    log.warning("Exception was: %s %s", type(e), str(e))
                    new_outputs.append(i)
            self.outputs = new_outputs

    @property
    def total_in(self) -> Decimal:
        """
        Calculate the total amount of coins (decimal) being spent within the inputs of this transaction.
        
        WARNING: This method/property requires loading and then deserializing the source transaction of each input, where the
        input coin was originally outputted to this Electrum wallet.
        
        As an example of why this may be an issue - a transaction with 5 inputs, would require 5 get_transaction calls to obtain
        the source transactions of the inputs, plus 5 deserialize calls (total of 10 RPC calls) to convert the transactions
        into a ``dict`` / :class:`.ElectrumTransaction`
        """
        v = Decimal('0')
        for o in self.inputs:
            v += o.previous_value
        return v
    
    @property
    def total_out(self) -> Decimal:
        """
        Calculate the total amount of coins (decimal) that were outputted in this transaction
        
        Example::
        
            >>> inputs = [ElectrumInput('abcd1234', 0)]
            >>> outputs = [
            ...     ElectrumOutput(address='LWJUwsFeKtFszgtG2kvuqnK8HfZhigscSj', value_sats=1207250),
            ...     ElectrumOutput(address='ltc1q9nd8g7y2vw342m9kz2u2fwj43w30l46mk9umjd', value_sats=352438)
            ... ]
            >>> tx = ElectrumTransaction(version=2, locktime=14532535463, inputs=inputs, outputs=outputs)
            >>> tx.total_out
            Decimal('0.01559688')
        
        """
        v = Decimal('0')
        for o in self.outputs:
            if o.value_sats is None:
                continue
            v += o.value_decimal
        return v

    def total_out_address(self, address: str) -> Decimal:
        """
        Similar to :meth:`.total_out` - but only count outputs which were destined for ``address``
        
        Example::
        
            >>> inputs = [ElectrumInput('abcd1234', 0)]
            >>> outputs = [
            ...     ElectrumOutput(address='LWJUwsFeKtFszgtG2kvuqnK8HfZhigscSj', value_sats=1207250),
            ...     ElectrumOutput(address='ltc1q9nd8g7y2vw342m9kz2u2fwj43w30l46mk9umjd', value_sats=352438)
            ... ]
            >>> tx = ElectrumTransaction(version=2, locktime=14532535463, inputs=inputs, outputs=outputs)
            >>> tx.total_out_address('ltc1q9nd8g7y2vw342m9kz2u2fwj43w30l46mk9umjd')
            Decimal('0.00352438')
            >>> tx.total_out_address('LWJUwsFeKtFszgtG2kvuqnK8HfZhigscSj')
            Decimal('0.0120725')
        
        :param str address: The wallet address to calculate total outputted coins amount for
        :return Decimal total: The total amount of coins which were transferred to ``address``
        """
        v = Decimal('0')
        for o in self.outputs:
            if o.value_sats is None or o.address != address:
                continue
            v += o.value_decimal
        return v

    @property
    def tx_fee(self) -> Decimal:
        """
        Calculate the transaction fee by subtracting :attr:`.total_out` from :attr:`.total_in`.
        
        TX fee result is returned as a :class:`.Decimal`
        """
        return self.total_in - self.total_out
