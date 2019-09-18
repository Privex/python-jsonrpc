from privex.helpers import empty

from privex.jsonrpc.JsonRPC import JsonRPC
from decimal import Decimal
from typing import Union, List, Dict
from privex.jsonrpc.objects import MoneroPayment, MoneroTransfer
from privex.jsonrpc.core import decimal_to_atomic, atomic_to_decimal


class MoneroRPC(JsonRPC):
    """
    Monero JsonRPC Client for Python

    Basic Usage:

        >>> m = MoneroRPC(username='monero', password='mypass')
        >>> m.open_wallet(filename='mywallet', password='mywalletpass')
        {}
        >>> m.get_height()
        173463
        >>> m.create_account(label='myaccount')
        {"account_index": 1, "address": "77Vx9cs1VPicFndSVgYUvTdLCJEZw9h81hXL..."}
        >>> for p in m.get_payments('60900e5603bf96e3'):
        ...     print(p.address, ':', p.decimal_amount)
        55LTR8KniP4LQGJSPtbYDacR7dz8RBFnsfAKMa : 1.2345
        55LTR8KniP4LQGJSPtbYDacR7dz8RBFnsfAKMa : 2.342
        >>> m.make_uri(address='77Vx9cs1VPicFndSVgYUvTdLCJEZw9h81hXL...', amount=m.decimal_to_atomic('10'))
        monero:77Vx9cs1VPicFndSVgYUvTdLCJEZw9h81hXL...?tx_amount=10000000000000


    Copyright::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Python Simple JSON RPC library             |
        |        License: X11/MIT                           |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |                                                   |
        +===================================================+
    
    """
    DEF_URL = '/json_rpc'

    def __init__(self, hostname='127.0.0.1', port=18082, username=None, password=None, ssl=False, timeout=120, 
                 url=DEF_URL, auth='digest'):
        super().__init__(
            hostname=hostname, port=port, username=username, password=password, 
            ssl=ssl, timeout=timeout, url=url, auth=auth
        )
    
    @staticmethod
    def decimal_to_atomic(amount: Union[Decimal, str]) -> int:
        """
        Convert a Decimal monero amount into an atomic (piconero) integer amount

            >>> MoneroRPC.decimal_to_atomic(Decimal('10'))
            10000000000000
        
        """
        return decimal_to_atomic(amount)
    
    @staticmethod
    def atomic_to_decimal(amount: int) -> Decimal:
        """
        Convert an integer atomic monero amount into a normal Decimal amount
        
            >>> MoneroRPC.atomic_to_decimal(10000000000000)
            Decimal('10')
        
        """
        return atomic_to_decimal(amount)
    
    def create_address(self, account_index: int = 0, label: str = "") -> dict:
        """
        Create a monero address. Returns a dictionary with the monero address ``address`` and ID ``address_index``

        :param int account_index: The account ID to create an address for
        :param str label: An optional label for the address
        :return dict addr: dict(address: str, address_index: int)
        """
        return self.call('create_address', account_index=account_index, label=label)

    def create_account(self, label: str = "") -> dict:
        """
        Creates an account with the given optional label, and returns the first address + account index as a dict.

        :return dict acc: dict(address: str, account_index: 2)
        """
        return self.call('create_account', label=label)
    
    def create_wallet(self, filename: str, password: str = None, language="English") -> dict:
        if password is None:
            return self.call('create_wallet', filename=filename, language=language)
        return self.call('create_wallet', filename=filename, password=password, language=language)

    def get_height(self) -> int:
        """Returns the current block height of the monero wallet/rpc as an integer"""
        return self.call('get_height').get('height')
    
    def get_accounts(self, tag: str = None) -> dict:
        """
        Returns a dict containing a list of accounts, and total balances.

        Subaddress accounts are formatted as: ``dict(account_index: int, balance: int, base_address: str, label: str, tag: str, unlocked_balance: int)``
        
        :return dict accounts: dict(subaddress_accounts: List[dict], total_balance: int, total_unlocked_balance: int)
        """
        return self.call('get_accounts') if tag is None else self.call('get_accounts', tag=tag)
    
    def get_address(self, account_index=0, address_index: List[int] = []):
        return self.call('get_address', account_index=account_index, address_index=address_index)
    
    def get_balance(self, account_index=0, address_indices: List[int] = []) -> dict:
        """
        Get the balance for the wallet

        :return dict baldata: dict(balance: int, unlocked_balance: int, multisig_import_needed: bool, per_subaddress: List[dict])
        """
        return self.call('get_balance', account_index=account_index, address_indices=address_indices)

    def get_payments(self, payment_id: str) -> List[MoneroPayment]:
        p = self.call('get_payments', payment_id=payment_id)
        payments = p.get('payments', [])
        return list(MoneroPayment.from_list(payments))

    def get_transfers(self, account_index=0, pending=True, incoming=True, outgoing=True,
                      subaddr_indices: List[int] = None, **kw) -> Dict[str, List[MoneroTransfer]]:
        """
        Get incoming/outgoing transfers as a ``dict`` - generally with the keys ``in`` and ``out``

        See :class:`.MoneroTransfer` for the attributes contained in each transfer object.

        NOTE: As ``in`` is a protected Python keyword, ``in`` and ``out`` have been changed to ``incoming``
        and ``outgoing``, however you can still use ``in`` and ``out`` if they're passed as kwargs using
        ``**somedict`` with a quoted dictionary
        e.g. ``get_transfers(account_index=1, **{"in": False, "out": True})``

        Usage:

            >>> m = MoneroRPC(username='monero', password='somepass')
            >>> transfers = m.get_transfers(account_index=1)
            >>> for t in transfers['in']:   # type: MoneroTransfer
            ...     print(f'Received {t.decimal_amount:.4} XMR into address {t.address}')
            ...
            Received 1.000 XMR into address 77Vx9cs1VPicFndSVgYUvTdLCJEZw9h81hXL...
            Received 2.473 XMR into address 55LTR8KniP4LQGJSPtbYDacR7dz8RBFnsfAKMa...
            >>>


        :param int account_index: (Default: 0) The account ID to get transfers for
        :param bool pending:  (Default: True) Include unconfirmed transactions
        :param bool incoming: (Default: True) List incoming transfers (``in``)
        :param bool outgoing: (Default: True) List outgoing transfers (``out``)
        :param list subaddr_indices: (Optional) A list of int sub-address indices to filter transfers for
        :param Any kw: Any additional dictionary parameters to pass to get_transfers
        :return dict transfers: dict(in: List[MoneroTransfer], out: List[MoneroTransfer])
        """
        _args = {
            "account_index": account_index, "pending": pending,
            "in": kw.get('in', incoming), "out": kw.get('out', outgoing),
            "subaddr_indices": [] if empty(subaddr_indices, itr=True) else subaddr_indices, **kw
        }
        args = {k: v for k, v in _args.items() if v is not None}
        t = self.call('get_transfers', **args)
        res = {}
        if 'in' in t:
            res['in'] = list(MoneroTransfer.from_list(t['in']))
        if 'out' in t:
            res['out'] = list(MoneroTransfer.from_list(t['out']))
        return {**res, **{k: v for k, v in t.items() if k not in ['in', 'out']}}

    def get_version(self) -> int:
        """
        Returns the RPC version as an integer, formatted with Major * 2^16 + Minor (Major encoded over the first 16 bits, 
        and Minor over the last 16 bits).
        """
        return self.call('get_version').get('version')
    
    def make_uri(self, address, amount: int = None, payment_id: str = None, recipient_name=None, tx_description=None) -> str:
        """Returns a Monero payment URI based on the arguments specified"""
        _args = dict(address=address,amount=amount,payment_id=payment_id,recipient_name=recipient_name,tx_description=tx_description)
        args = {k: v for k, v in _args.items() if v is not None}
        return self.call('make_uri', **args).get('uri', '')
    
    def make_integrated_address(self, standard_address: str = None, payment_id: str = None) -> dict:
        """
        Creates an integrated address (monero address combined with payment id)

        :param standard_address: A monero address (if not specified, will default to the "primary address")
        :param payment_id: A payment ID to integrate (if not specified, a random one will be generated)
        :return dict result: dict(integrated_address: str, payment_id: str)
        """
        _args = dict(standard_address=standard_address, payment_id=payment_id)
        args = {k: v for k, v in _args.items() if v is not None}
        return self.call('make_integrated_address', **args)

    def open_wallet(self, filename: str, password: str = None) -> dict:
        """Open a Monero wallet by filename. Optionally specify a password if it's required"""
        if password is None:
            return self.call('open_wallet', filename=filename)
        return self.call('open_wallet', filename=filename, password=password)

    def close_wallet(self) -> dict:
        """Close the current wallet (returns an empty dict)"""
        return self.call('close_wallet')

    def store(self) -> dict:
        """Save the wallet file"""
        return self.call('store')

    def transfer(self, destinations: List[dict], account_index: int = 0, subaddr_indices: List[int] = [], priority: int = 0, 
                 mixin: int = 0, ring_size: int = 0, payment_id: str = "", **kwargs) -> dict:
        """
        Transfer monero to one or more destinations.

        Basic usage (monero address and tx_key truncated for sanity):

            >>> m = MoneroRPC(username='monero', password='somepass')
            >>> amt = m.decimal_to_atomic('10')
            >>> m.transfer(destinations=[dict(amount=amt, address='7BnERTpvL5MbCLtj5n9No7J5oE5hH...')])
            {
                "amount": 10000000000000,
                "fee": 86897600000,
                "multisig_txset": "",
                "tx_blob": "",
                "tx_hash": "7663438de4f72b25a0e395b770ea9ecf7108cd2f0c4b75be0b14a103d3362be9",
                "tx_key": "25c9d8ec20045c80c93d665c9d3684aab7335f8b2cd02e1ba263...",
                "tx_metadata": "",
                "unsigned_txset": ""
            }
        

        """
        return self.call(
            'transfer', 
            destinations=destinations, account_index=account_index, subaddr_indices=subaddr_indices,
            priority=priority, mixin=mixin, ring_size=ring_size, payment_id=payment_id, **kwargs
        )
    
    def simple_transfer(self, amount: Union[Decimal, str], address: str, account_index: int = 0, payment_id: str = "", **kwargs):
        """
        A small wrapper function for :py:meth:`.transfer` to make sending Monero easier.

        Usage (monero address and tx_key truncated for sanity):

            >>> m = MoneroRPC(username='monero', password='somepass')
            >>> m.simple_transfer('10', '7BnERTpvL5MbCLtj5n9No7J5oE5hH...')
            {
                "amount": 10000000000000,
                "fee": 86897600000,
                "multisig_txset": "",
                "tx_blob": "",
                "tx_hash": "7663438de4f72b25a0e395b770ea9ecf7108cd2f0c4b75be0b14a103d3362be9",
                "tx_key": "25c9d8ec20045c80c93d665c9d3684aab7335f8b2cd02e1ba263...",
                "tx_metadata": "",
                "unsigned_txset": ""
            }
        """
        atomic_amt = self.decimal_to_atomic(amount)
        dest = [dict(amount=atomic_amt, address=address)]
        return self.transfer(destinations=dest, account_index=account_index, payment_id=payment_id, **kwargs)

    def validate_address(self, address: str) -> dict:
        """
        Validate a monero address

            >>> m = MoneroRPC(username='monero', password='somepass')
            >>> m.validate_address(
            ...    '8BNkere1xg7Jsbth2HbGBMdzFvgLDxpaJ4nmqqk72GFwVKGWpgPv3Xib1bEEx8hMt1PtpF3BiZws4dEovurWD73NDh9gFDj'
            ... )
            {'integrated': False, 'nettype': 'mainnet', 'openalias_address': '', 'subaddress': True, 'valid': True}


        :param str address: A monero address
        :return dict addr_info: dict(integrated:bool, nettype:str, openalias_address:str, subaddress:bool, valid:bool)
        """
        return self.call('validate_address', address=address)

