import json
from json import JSONDecodeError
from typing import Union, List, Optional, Dict
from requests.exceptions import HTTPError
from privex.jsonrpc.JsonRPC import JsonRPC
import logging

log = logging.getLogger(__name__)


class WalletNotLoaded(Exception):
    pass


class WalletLoadFailed(Exception):
    pass


class MethodNotFound(Exception):
    pass


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
    _wallet_autoload: bool
    _wallet_password: Optional[str]
    
    def __init__(self, hostname, port: int = 7777, username=None, password=None, ssl=False, timeout=120,
                 url: str = '', auth: str = 'plain', wallet_autoload: bool = False, wallet_password=None):
        self._wallet_autoload = wallet_autoload
        self._wallet_password = wallet_password
        super().__init__(hostname=hostname, port=port, username=username, password=password, ssl=ssl, timeout=timeout, url=url, auth=auth)

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

    def get_info(self) -> dict:
        """
        Returns the RPC version as an integer, formatted with Major * 2^16 + Minor (Major encoded over the first 16 bits,
        and Minor over the last 16 bits).
        """
        return self.call('getinfo')

    def get_address_history(self, address: str) -> list:
        return self.call('getaddresshistory', address)

    def get_address_unspent(self, address: str) -> list:
        return self.call('getaddressunspent', address)

    def get_address_balance(self, address: str) -> Dict[str, str]:
        return self.call('getaddressbalance', address)

    def get_transaction(self, txid: str, wallet=None):
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

    def payto(self, destination, amount, fee=None, feerate=None, from_addr=None, from_coins=None, change_addr=None,
              nocheck=False, unsigned=False, rbf=None, password=None, locktime=None, wallet=None) -> List[str]:
        """List wallet addresses. Returns the list of all addresses in your wallet. Use optional arguments to filter the results."""
        q = dict(destination=destination, amount=amount)
        if fee: q['fee'] = fee
        if feerate: q['feerate'] = feerate
        if from_addr: q['from_addr'] = from_addr
        if from_coins: q['from_coins'] = from_coins
        if change_addr: q['change_addr'] = change_addr
        if nocheck: q['nocheck'] = nocheck
        if unsigned: q['unsigned'] = unsigned
        if rbf: q['rbf'] = rbf
        if password: q['password'] = password
        if locktime: q['locktime'] = locktime
        if wallet: q['wallet'] = wallet
        return self.call('payto', **q)

    def load_wallet(self, wallet_path=None, password=None) -> bool:
        q = {}
        if wallet_path is not None: q['wallet_path'] = wallet_path
        if password is not None: q['password'] = password
        return self.call('load_wallet', **q)

    def close_wallet(self, *args, **kwargs) -> bool:
        return self.call('close_wallet', *args, **kwargs)

    def validate_address(self, address: str):
        return self.call('validateaddress', address)

    def version(self, *args, **kwargs) -> str:
        return self.call('version', *args, **kwargs)
