import json
import time
from collections import namedtuple
from decimal import Decimal
from json import JSONDecodeError
from typing import Union, List, Optional, Dict, Generator, Any, Tuple

from privex.helpers import is_true, empty
from requests.exceptions import HTTPError
from privex.jsonrpc.JsonRPC import JsonRPC
import logging

from privex.jsonrpc.objects import ElectrumTransaction, ElectrumHistoryItem, ElectrumUnspent, ElectrumBalanceResponse, AnyNum, BaseData

log = logging.getLogger(__name__)


class ElectrumRPCException(Exception):
    pass


class WalletNotLoaded(ElectrumRPCException):
    pass


class WalletLoadFailed(ElectrumRPCException):
    pass


class MethodNotFound(ElectrumRPCException):
    pass


class MethodNotSpecified(ElectrumRPCException):
    pass


class InvalidTXID(ElectrumRPCException):
    pass


BroadcastResult = namedtuple('BroadcastResult', 'txid raw_tx tx_data', defaults=[None, None])

BCResType = Union[BroadcastResult, Tuple[str, Optional[str], Optional[ElectrumTransaction]]]


class ElectrumRPC(JsonRPC):
    """
    
    **Basic usage**
    
    
    Connecting to Electrum and getting basic information::
        
        >>> from privex.jsonrpc import ElectrumRPC
        >>> rpc = ElectrumRPC('127.0.0.1', port=54770, username='rpc_user', password='rpc_password', wallet_autoload=True)
        >>> rpc.get_info()
            {
                'path': '/root/.electrum-ltc', 'server': 'backup.electrum-ltc.org',
                'blockchain_height': 1814580, 'server_height': 1814580,
                'spv_nodes': 5, 'connected': True, 'auto_connect': True,
                'version': '4.0.0a0', 'default_wallet': '/root/.electrum-ltc/wallets/default_wallet',
                'fee_per_kb': 100000
            }
        >>> rpc.version()
        '4.0.0a0'
    
    Creating the default wallet, with no encryption / no password::
    
        >>> rpc.create()   # Create the default wallet, with no encryption / password
            {'seed': 'you salmon flock govern behave satoshi leaf lion congress typical install report',
             'path': '/root/.electrum-ltc/wallets/default_wallet',
             'msg': 'Please keep your seed in a safe place; if you lose it, you will not be able to restore your wallet.'}
        >>> rpc.close_wallet()  # Close the wallet (to re-create the wallet, delete .electrum-ltc/wallets/default_wallet)
    
    Creating the default wallet, and encrypt it using the password ``MyWalletPassword``::
    
        >>> rpc.create(password='MyWalletPassword', encrypt_file=True)
        >>> # To load an encrypted wallet, specify the wallet password when loading.
        >>> rpc.load_wallet(password='MyWalletPassword')
    
    Getting addresses::
    
        >>> rpc.get_unused_address()
        'ltc1qa65chzjpkvj5fy4uhttc5qa5ejet292m8e3sjp'
        >>> rpc.get_unused_address()
        'ltc1qa65chzjpkvj5fy4uhttc5qa5ejet292m8e3sjp'
    
    Sending coins::
        
        >>> tx = rpc.payto('Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', '0.00001', broadcast=True)
        >>> tx.txid
        'aa8ad8cbb6e34c61e96151db08fa7b1c092c237b1dd56ff35524e58943901590'
    
    
    
    More information about the methods available can be found in the Electrum code.
    
     * Electrum-BTC: https://github.com/spesmilo/electrum/blob/master/electrum/commands.py#L174
     * Electrum-LTC: https://github.com/pooler/electrum-ltc/blob/master/electrum_ltc/commands.py#L174
    
    
    All methods (based on electrum-ltc help as of 30/MAR/2020)::
    
        "add_lightning_request", "add_peer", "add_request", "addtransaction", "broadcast", "clear_invoices", "clear_ln_blacklist",
        "clear_requests", "close_channel", "close_wallet", "commands", "convert_xkey", "create", "createmultisig", "createnewaddress",
        "decrypt", "deserialize", "dumpgraph", "dumpprivkeys", "encrypt", "freeze", "get", "get_channel_ctx", "get_tx_status",
        "getaddressbalance", "getaddresshistory", "getaddressunspent", "getalias", "getbalance", "getconfig", "getfeerate",
        "getinfo", "getmasterprivate", "getmerkle", "getmpk", "getprivatekeys", "getpubkeys", "getrequest", "getseed",
        "getservers", "gettransaction", "getunusedaddress", "help", "importprivkey", "init_lightning", "inject_fees",
        "is_synchronized", "ismine", "lightning_history", "list_channels", "list_invoices", "list_requests", "list_wallets",
        "listaddresses", "listcontacts", "listunspent", "lnpay", "load_wallet", "make_seed", "nodeid", "notify",
        "onchain_history", "open_channel", "password", "payto", "paytomany", "remove_lightning", "removelocaltx",
        "restore", "rmrequest", "searchcontacts", "serialize", "setconfig", "setlabel", "signmessage", "signrequest",
        "signtransaction", "stop", "sweep", "unfreeze", "validateaddress", "verifymessage", "version"
    
    
    """
    auto_broadcast: bool
    _wallet_autoload: bool
    _wallet_password: Optional[str]
    _retry_blacklist = ("broadcast", "payto",)
    
    def __init__(self, hostname, port: int = 7777, username=None, password=None, ssl=False, timeout=120,
                 url: str = '', auth: str = 'plain', wallet_autoload: bool = False, wallet_password=None, **kwargs):
        """
        
        
        
        :param hostname: The hostname or IP address of the JSON RPC server
        :param port:     The JSON RPC TCP port to connect to
        :param username: If the RPC server needs a username, specify it here
        :param password: If the RPC server needs a password, specify it here (username must also be set)
        :param ssl:      If set to True, will use https for requests. Default is false - use plain http
        :param timeout:  If the server stops sending us data for this many seconds, abort and throw an exception
        :param url:      The URL to query, e.g. api/v1/test (starting /'s will automatically be removed)
        :param str auth: HTTP Authentication type - either ``plain`` (default) or ``digest``
        :param bool wallet_autoload: (Default: ``False``) Automatically load and unlock the default Electrum wallet if a call fails
                                     due to the wallet not being loaded.
        :param str wallet_password: When ``wallet_autoload`` is ``True``, ``wallet_password`` is used to decrypt the wallet automatically.
                                    This defaults to ``None`` (no wallet decryption password needed)
        :param kwargs: Optional additional keyword-only arguments.
        
        :keyword bool auto_broadcast: (default: ``False``) Automatically broadcast transactions generated by transaction methods
                                      such as :meth:`.payto` (send coins)
        
        :keyword bool auto_retry: (default: ``True``) Automatically retry safe calls such as ``get_transaction`` or ``deserialize`` when
        an unknown (or known to be intermittent) error is raised.
        :keyword int max_retries: (default: 3) Maximum amount of times to retry a call before giving up
        :keyword int|float|Decimal retry_delay: (default: 2) Number of seconds to wait between each retry
        
        """
        self._wallet_autoload = wallet_autoload
        self._wallet_password = wallet_password
        super().__init__(hostname=hostname, port=port, username=username, password=password, ssl=ssl, timeout=timeout, url=url, auth=auth)
        
        self.auto_broadcast = is_true(kwargs.get('auto_broadcast', False))
        self._auto_retry = is_true(kwargs.get('auto_retry', True))
        self._max_retries = int(kwargs.get('max_retries', 3))
        self._retry_delay = float(kwargs.get('retry_delay', 2))

    def _handle_call_error(self, e: HTTPError, method=None, params: list = None, dicdata: dict = None, **kwargs):
        retries = kwargs.pop('_retries', 0)
        cname = self.__class__.__name__
        try:
            err_data = json.loads(e.response.text)
            emsg = err_data.get('error', {}).get('message', '').lower()
            if 'wallet not loaded' in emsg:
                if self._wallet_autoload:
                    log.info("Wallet not loaded. Attempting to auto-load wallet, as wallet_autoload is true.")
                    if self.load_wallet(password=self._wallet_password):
                        if empty(method):
                            raise MethodNotSpecified("Successfully loaded wallet, but cannot auto-retry, as no method was specified???")
                        return self.call(method, *params, **dicdata)
                    else:
                        raise WalletLoadFailed("Tried auto-loading wallet but got 'false' response. Invalid password???")
                raise WalletNotLoaded(f"Electrum wallet not loaded. Call {cname}.load_wallet() !")
            if 'method not found' in emsg:
                raise MethodNotFound(f"JsonRPC Method '{method}' does not exist.")
            
            if 'is not a txid' in emsg:
                raise InvalidTXID(f"Invalid transaction ID: {emsg}")
            raise e
        except (MethodNotFound, InvalidTXID, MethodNotSpecified) as err:
            raise err
        except Exception as err:
            log.warning("Exception while calling method %s - exception was: %s %s", method, type(err), str(err))
            if self._auto_retry:
                if method in self._retry_blacklist:
                    log.exception("Auto-retry is enabled, but method %s is blacklisted (unsafe to retry). Raising exception!", method)
                    raise err
                if empty(method):
                    log.exception("Auto-retry enabled, but RPC method passed to error handler is empty. Cannot retry. Raising exception!")
                    raise err
                retries += 1
                log.warning(f"[Retry {retries} of {self._max_retries}] Waiting {self._retry_delay} seconds then retrying call...")
                time.sleep(self._retry_delay)
                log.warning(f"[Retry {retries} of {self._max_retries}] Retrying call '{method}'...")
                return self.call(method, *params, **dicdata)
            raise err
            
    
    def call(self, method, *params, **dicdata) -> Union[dict, list, str, bool, int]:
        cname = self.__class__.__name__
        try:
            _c = super().call(method, *params, **dicdata)
            return _c
        except HTTPError as e:
            try:
                err_data = json.loads(e.response.text)
                emsg = err_data.get('error', {}).get('message', '').lower()
                if 'wallet not loaded' in emsg:
                    if self._wallet_autoload:
                        log.info("Wallet not loaded. Attempting to auto-load wallet, as wallet_autoload is true.")
                        if self.load_wallet(password=self._wallet_password):
                            return self.call(method, *params, **dicdata)
                        else:
                            raise WalletLoadFailed("Tried auto-loading wallet but got 'false' response. Invalid password???")
                    raise WalletNotLoaded(f"Electrum wallet not loaded. Call {cname}.load_wallet() !")
                if 'method not found' in emsg:
                    raise MethodNotFound(f"JsonRPC Method '{method}' does not exist.")
                
                raise e
            except JSONDecodeError:
                raise e
    
    def _clean_keys(self, data: Union[dict, list, tuple, BaseData, Any], c_key: str = 'raw_data') -> Union[dict, list, Any]:
        """
        Recursively remove a certain key from the object ``data``.
        
        If ``data`` isn't a :class:`.list`, :class:`.set`, :class:`.dict` or a dataclass instance based on :class:`.BaseData`,
        then it will simply be returned with no modifications.
        
        :param dict|list|tuple|BaseData|Any data: A dict/:class:`.BaseData` object, or list of them to recursively remove
                                                  the key ``c_key`` from.
        :return dict|list|Any clean_data: The original ``data`` object after removing ``c_key`` keys
        """
        clean_list = []
        if isinstance(data, (list, set)):
            for v in data:
                log.debug("(clean list) calling _clean_keys with value: %s", v)
                newv = self._clean_keys(v)
                clean_list.append(newv)
            return clean_list
        if isinstance(data, (dict, BaseData)):
            o: dict = dict(data)
            if c_key in o: del o[c_key]
            for k, v in o.items():
                if not isinstance(v, (dict, BaseData, list, set)):
                    continue
                log.debug("(clean dict) calling _clean_keys with key '%s' - value: %s", k, v)
                newv = self._clean_keys(v)
                o[k] = newv
            return o
        return data
    
    def broadcast(self, transaction: Union[str, dict, ElectrumTransaction]) -> BCResType:
        if isinstance(transaction, (dict, ElectrumTransaction)):
            log.debug("Serializing transaction into a string for broadcasting: %s", transaction)
            transaction = self.serialize(transaction)
            log.debug("Success? Serialized string is: %s", transaction)

        if not isinstance(transaction, str):
            raise ValueError(f"{self.__class__.__name__}.broadcast expected 'transaction' to be a string, "
                             f"but actual type was: {type(transaction)}")
        
        txid = self.call('broadcast', transaction)
        try:
            data = self.deserialize(transaction)
        except Exception as e:
            log.warning("Warning! Failed to deserialize transaction after broadcasting. Reason: %s %s", type(e), str(e))
            log.warning("Raw TX is: %s", transaction)
            data = None
        
        return BroadcastResult(txid=txid, raw_tx=transaction, tx_data=data)

    def create(self, passphrase=None, password=None, encrypt_file=False, seed_type=None, wallet_path=None) -> dict:
        q = {}
        if wallet_path is not None: q['wallet_path'] = wallet_path
        if password is not None: q['password'] = password
        if passphrase is not None: q['passphrase'] = passphrase
        if encrypt_file is not None: q['encrypt_file'] = encrypt_file
        if seed_type is not None: q['seed_type'] = seed_type

        return self.call('create', **q)

    def create_new_address(self, wallet=None):
        """Create a new receiving address, beyond the gap limit of the wallet"""
        q = {}
        if wallet is not None: q['wallet'] = wallet
        return self.call('createnewaddress', **q)
    
    def deserialize(self, transaction: str) -> Union[ElectrumTransaction, dict, list]:
        """
        
            >>> rpc = ElectrumRPC()
            >>> rpc.get_address_history('ltc1q9nd8g7y2vw342m9kz2u2fwj43w30l46mk9umjd')
            [
                {'tx_hash': '59b578ede3ee43a80588e5971a183580fbdb9ae4efdef8b422fd69daa2c16a48', 'height': 0, 'fee': 334}
            ]
            >>> rpc.get_transaction('59b578ede3ee43a80588e5971a183580fbdb9ae4efdef8b422fd69daa2c16a48')
            '0200000001f8b1b36b33925a8ab6e6134ba39223c0d0d7934db2fd884307c42b07ff158232000000006b483045022100cce2bf23d3ef80ae
             9adf70c14c9a532906d56776fe929900f4faa0984f04196d02203180e49b6397776c0c04d708f59ffe7fb0523076091358b4f8daae90046a
             5e42012103009b55ae2052a31de6c9a03feb40f9e927452303f1a05fc559f616c782370660fdffffff02a0860100000000001600142cda74
             788a63a3556cb612b8a4ba558ba2ffd75b23210500000000001976a9141014b2fb4380643e35a30112fc735f5887964ef088acd9601c00'
            >>> tx = rpc.get_transaction('59b578ede3ee43a80588e5971a183580fbdb9ae4efdef8b422fd69daa2c16a48')

            >>> rpc.deserialize(tx)
            {'version': 2,
             'locktime': 1859801,
             'inputs': [{'prevout_hash': '328215ff072bc4074388fdb24d93d7d0c02392a34b13e6b68a5a92336bb3b1f8',
               'prevout_n': 0,
               'coinbase': False,
               'nsequence': 4294967293,
               'scriptSig': '483045022100cce2bf23d3ef80ae9adf70c14c9a532906d56776fe9299...'}],
             'outputs': [
                {
                    'scriptpubkey': '00142cda74788a63a3556cb612b8a4ba558ba2ffd75b',
                    'address':  'ltc1q9nd8g7y2vw342m9kz2u2fwj43w30l46mk9umjd',
                    'value_sats': 100000
                },
                {
                    'scriptpubkey': '76a9141014b2fb4380643e35a30112fc735f5887964ef088ac',
                    'address': 'LLgysV38xrpu3PP1qRYPnw3exgPe9X6xtd',
                    'value_sats': 336163
                }
            ]}

        :param transaction:
        :return:
        """
        if transaction in ['', None]:
            raise AttributeError(f"Transaction passed to {self.__class__.__name__}.deserialize is empty!")
        
        res = self.call('deserialize', transaction)
        if isinstance(res, dict):
            return ElectrumTransaction.from_dict(res, electrum_ins=self)
        return res
    
    deserialise = deserialize
    """Alias the British English spelling ``deserialise`` to the native method ``deserialize``"""
    
    def get_info(self) -> dict:
        """
        Returns the RPC version as an integer, formatted with Major * 2^16 + Minor (Major encoded over the first 16 bits,
        and Minor over the last 16 bits).
        """
        return self.call('getinfo')

    def get_address_history(self, address: str) -> Generator[ElectrumHistoryItem, None, None]:
        res = self.call('getaddresshistory', address)
        return ElectrumHistoryItem.from_list(res, electrum_ins=self)

    def get_address_unspent(self, address: str) -> Generator[ElectrumUnspent, None, None]:
        res = self.call('getaddressunspent', address)
        return ElectrumUnspent.from_list(res, electrum_ins=self)

    def get_address_balance(self, address: str) -> ElectrumBalanceResponse:
        res = self.call('getaddressbalance', address)
        return ElectrumBalanceResponse.from_dict(res)

    def get_transaction(self, txid: str, wallet=None) -> str:
        """
        Returns the full transaction data for the transaction ID ``txid`` as a serialized hex string.
        
        Pass the result of this method to :meth:`.deserialize` to convert the hex data into an :class:`.ElectrumTransaction`
        dataclass object, which can also be easily converted into a :class:`.dict`.
        
        :param str txid: A transaction ID to lookup
        :param wallet: (optional) The wallet to use
        :return:
        """
        q = dict(txid=txid)
        if wallet is not None: q['wallet'] = wallet
        return self.call('gettransaction', **q)

    def get_unused_address(self, wallet=None) -> str:
        """Returns the first unused address of the wallet, or None if all addresses are used.
        An address is considered as used if it has received a transaction, or if it is used in a payment request."""
        q = {}
        if wallet is not None: q['wallet'] = wallet
        return self.call('getunusedaddress', **q)
    
    def list_addresses(self, receiving=False, change=False, labels=False, frozen=False, unused=False, funded=False, balance=False,
                       wallet=None) -> List[str]:
        """List wallet addresses. Returns the list of all addresses in your wallet. Use optional arguments to filter the results."""
        q = dict(receiving=receiving, change=change, labels=labels, frozen=frozen, funded=funded, unused=unused, balance=balance)
        if wallet is not None: q['wallet'] = wallet
        return self.call('listaddresses', **q)

    def list_wallets(self) -> List[dict]:
        return self.call('list_wallets')

    def payto(self, destination: str, amount: AnyNum, fee: Optional[AnyNum] = None, **kwargs) -> Union[str, BCResType]:
        """
        Send ``amount`` coins to ``destination``.
        
        Basic usage::
        
            >>> rpc = ElectrumRPC()
            >>> tx = rpc.payto('Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', '0.00001', broadcast=True)
            >>> tx.txid
            'aa8ad8cbb6e34c61e96151db08fa7b1c092c237b1dd56ff35524e58943901590'
            >>> tx.raw_tx
            '0200000000010189a187af0de1f4be8c60260d9f2f6b8b187b981fb452d86adc8ef143ee347...'
            >>> tx.tx_data
            ElectrumTransaction(version=2, locktime=1859899, inputs=[ElectrumInput(prevout_hash...)], ...)
        
        Since :class:`.BroadcastResult` is a namedtuple, it can also be used like a normal tuple, such as assigning the
        return values to three variables at once, instead of accessing them within the tuple result::
        
            >>> txid, _, data = rpc.payto('Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', '0.00001', broadcast=True)
        
        If you'd like to inspect or modify the transaction before it's broadcasted, you can use :meth:`.payto` without ``broadcast=True``,
        and you'll receive a raw transaction string. You can then decode the raw transaction string using :meth:`.deserialize`
        to convert it into an :class:`.ElectrumTransaction` object, allowing you to easily review the transaction before sending it.
         
            >>> rawtx = rpc.payto('Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', '0.00001')
            >>> res = rpc.deserialize(rawtx)
            >>> res
            ElectrumTransaction(version=2, locktime=1859891, inputs=[ElectrumInput(prevout_hash='...', prevout_n=1, coinbase=False,)], ...)
            >>> res.total_out
            Decimal('0.0005480')
            >>> res.total_out_address('Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx')
            Decimal('0.0000100')
            >>> res.outputs
            [
                ElectrumOutput(address='Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', value_sats=1000,
                               scriptpubkey='76a914e0b6bc970a38f3d3ac2118daf9e5e81c1be57bf888ac'),
                ElectrumOutput(address='ltc1q5yqd66ev6j94dh6dtaalt42gfgzhjzqlgvneag', value_sats=53800,
                               scriptpubkey='0014a100dd6b2cd48b56df4d5f7bf5d5484a0579081f')
            ]
        
        Once you've reviewed the transaction, you can broadcast the original raw TX string returned by :meth:`.payto` using
        the :meth:`.broadcast` method::
        
            >>> data = rpc.broadcast(rawtx)
            >>> data
            BroadcastResult(
              txid='d9690a87e294dfe615cca4f4ea4a60c389279cc7aa07ecc20835812b0f1fd736', raw_tx='02000...',
              tx_data=ElectrumTransaction(
                  version=2, locktime=1859819,
                  inputs=[
                       ElectrumInput(prevout_hash='aa8ad8...', prevout_n=1, coinbase=False, nsequence=4294, scriptSig='',
                                     witness='024730440220...', value_sats=None)
                  ],
                  outputs=[
                      ElectrumOutput(address='Lfi8Xx4TgBKiRWCN3uBPJiohGW1MjkmJBx', value_sats=1000, scriptpubkey='76a914e0b6b...'),
                      ElectrumOutput(address='ltc1q5yqd66ev6j94dh6dtaalt42gfgzhjzqlgvneag', value_sats=53800, scriptpubkey='0014a10...')
                  ]
              )
            )

        
        :param str destination: Destination address to send ``amount`` coins to.
        :param str|int|float|Decimal amount: The amount of coins to send to ``destination``
        :param str|int|float|Decimal fee: The miner fee to use. If set to ``None``, this is automatically determined.
        
        :keyword callable cast_amount: (default: :class:`.str`) Cast ``amount`` using this callable function/method/class.
                                       This can be set to ``None`` to disable casting ``amount``
        :keyword bool broadcast: (default: uses :attr:`.auto_broadcast` which defaults to ``False``) If True, will automatically
                                 broadcast the transaction using :meth:`.broadcast`, instead of just returning the serialised
                                 string transaction returned by ``payto``.
          
        :keyword feerate:
        :keyword str from_addr: Send the coins from this specific address
        :keyword from_coins:
        :keyword str change_addr:
        :keyword bool nocheck:
        :keyword bool unsigned:
        :keyword rbf:
        :keyword str password:
        :keyword int locktime:
        :keyword str wallet:
        
        :returns str raw_tx: When ``broadcast`` is False (default), this method will only build the transaction and return it as a hex
                             string. You would need to broadcast it manually by passing it to :meth:`.broadcast`
        
        :returns BCResType broadcast_result: When ``broadcast`` is True, a :class:`.BroadcastResult` named tuple object will be returned,
                                             instead of a hex transaction string.
        """
        def h(k): return k in kwargs
        
        broadcast = is_true(kwargs.pop('broadcast', self.auto_broadcast))
        cast_amount = kwargs.pop('cast_amount', str)
        if cast_amount is not None:
            amount = cast_amount(amount)
        q = dict(destination=destination, amount=amount)
        if fee: q['fee'] = fee
        if h('nocheck'): q['nocheck'] = is_true(kwargs.pop('nocheck', False))
        if h('unsigned'): q['unsigned'] = is_true(kwargs.pop('unsigned', False))
        
        q = {**q, **kwargs}
        
        res: str = self.call('payto', **q)
        
        if broadcast:
            return self.broadcast(res)
        
        return res

    def load_wallet(self, wallet_path=None, password=None) -> bool:
        q = {}
        if wallet_path is not None: q['wallet_path'] = wallet_path
        if password is not None: q['password'] = password
        return self.call('load_wallet', **q)

    def serialize(self, jsontx: Union[dict, ElectrumTransaction]) -> str:
        """
        Serialize a transaction from a :class:`.dict` or :class:`.ElectrumTransaction` into a BASE64 encoded transaction string.

        Basic example::

            >>> rpc = ElectrumRPC()
            >>> inputs = [dict(
            ...     prevout_hash='167234ee43f18edc6ad852b41f987b188b6b2f9f0d26608cbef4e10daf87a189',
            ...     prevout_n=1, value=10000,
            ... )]
            >>> outputs = [dict(address='LLgysV38xrpu3PP1qRYPnw3exgPe9X6xtd', value=10000)]
            >>> rpc.serialize(dict(inputs=inputs, outputs=outputs))
            "dGhpcyBpcyBub3QgYSByZWFsIHRyYW5zYWN0aW9uLiB0aGlzIGlzIGp1c3QgYW4gZXhhbXBsZS4="

        :param jsontx:
        :return:
        """
        if isinstance(jsontx, ElectrumTransaction):
            jsontx = jsontx.raw_data
        if 'inputs' not in jsontx:
            raise AttributeError("serialize expects the transaction to contain the key 'inputs' with a list of dict's")
        if 'outputs' not in jsontx:
            raise AttributeError("serialize expects the transaction to contain the key 'outputs' with a list of dict's")
    
        #####
        # Ensure every input and output has a 'value' key
        inputs, outputs = jsontx['inputs'], jsontx['outputs']
        for k, i in enumerate(inputs):
            if 'value' in i and not empty(i['value']):
                continue
            if 'value_sats' not in i:
                raise AttributeError("One or more transaction 'inputs' are missing the 'value' key (and fallback 'value_sats')")
            inputs[k]['value'] = i['value_sats']
            del inputs[k]['value_sats']
        for k, i in enumerate(outputs):
            if 'value' in i and not empty(i['value']):
                continue
            if 'value_sats' not in i:
                raise AttributeError("One or more transaction 'outputs' are missing the 'value' key (and fallback 'value_sats')")
            outputs[k]['value'] = i['value_sats']
            del outputs[k]['value_sats']
    
        jsontx['inputs'], jsontx['outputs'] = inputs, outputs
        clean = self._clean_keys(jsontx)
    
        return self.call('serialize', jsontx=clean)
    
    def close_wallet(self, *args, **kwargs) -> bool:
        return self.call('close_wallet', *args, **kwargs)

    def validate_address(self, address: str):
        return self.call('validateaddress', address)

    def version(self, *args, **kwargs) -> str:
        return self.call('version', *args, **kwargs)
