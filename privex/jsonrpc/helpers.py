import logging
from decimal import Decimal
from privex.jsonrpc.JsonRPC import JsonRPC
from typing import List, Union, Dict

log = logging.getLogger(__name__)

class BitcoinRPC(JsonRPC):
    """
    Wrapper class for JsonRPC, with default host 127.0.0.1 and port 8332
    Contains pre-defined methods with pydoc for interacting with `bitcoind` compatible JsonRPC services
    including most coin daemons forked from Bitcoin, e.g. litecoind, dogecoind etc.

    If a method is not defined, you can still use it! You just won't get any IDE hints with the parameters.

    Basic usage (by default, connects to http://127.0.0.1:8332):

        >>>  j = BitcoinRPC(username='bitcoinrpc', password='somesecurepassword')
        >>>  j.getbalance()
        Decimal(0.2456337)
    """
    def __init__(self, hostname='127.0.0.1', port=8332, username=None, password=None, ssl=False, timeout=120, 
                 url: str = '', auth: str = 'plain'):
        super().__init__(
            hostname=hostname, port=port, username=username, password=password, 
            ssl=ssl, timeout=timeout, url=url, auth=auth
        )

    def getnewaddress(self, account="", address_type=None) -> str:
        """
        Generate a new crypto address and return it as a string.

        :param account:       Name of the account to store address in. Default is blank ``""``
        :param address_type:  The address type to use. Options are ``legacy``, ``p2sh-segwit``, and ``bech32``.
        :return: string - the address that was generated
        """
        if address_type is None:
            return self.call('getnewaddress', account)
        return self.call('getnewaddress', account, address_type)

    def getbalance(self, account="*", confirmations: int = 0, watch_only=False) -> Decimal:
        """
        Get the current wallet balance as a Decimal

        :param str account: DEPRECATED - Get the balance of this wallet account, ``*`` means all accs.
        :param int confirmations: Get wallet balance that has at least this many confirms
        :param bool watch_only: Include "Watch Only" addresses in the balance figure
        :return Decimal balance: The total balance of the given account
        """
        bal = self.call('getbalance', account, confirmations, watch_only)
        if type(bal) == float:
            bal = '{0:.8f}'.format(bal)
        return Decimal(bal)

    def getreceivedbyaddress(self, address, confirmations: int = 0) -> Decimal:
        """
        Get the total amount of coins received by an address (must exist in the wallet)

        :param str address: The address to lookup
        :param int confirmations: Get received amount that has at least this many confirms
        :return Decimal balance: The total amount of coins received by an address.
        """
        bal = self.call('getreceivedbyaddress', address, confirmations)
        if type(bal) == float:
            bal = '{0:.8f}'.format(bal)
        return Decimal(bal)
    
    def sendtoaddress(self, address, amount: Union[float, str, Decimal], comment="", comment_to="", 
                      subtractfee: bool = False, force_float=True) -> str:
        """
        Send coins to an address

        :param str address:     The destination address to send coins to
        :param float amount:    The amount of coins to send. If coin supports string amounts, see ``force_float`` param.
        :param str comment:     A comment used to store what the transaction is for.
        :param str comment_to:  A comment, representing the name of the person or organization you're sending to.
        :param bool subtractfee: (Default False) If set to True, reduce the sending amount to cover the TX fee.
        :param bool force_float: (Default True) If set to True, the ``amount`` parameter will be casted to a float
                                 before sending via JSONRPC. If you're dealing with a coin daemon that can handle 
                                 string amounts, set this to False and pass amount as a str
        :return str txid: The transaction ID for this "send coins" transaction.
        """

        if force_float:
            amount = float(amount)
        return self.call('sendtoaddress', address, amount, comment, comment_to, subtractfee)

    def listtransactions(self, account="*", count: int = 10, skip: int = 0, watch_only=False) -> List[dict]:
        """
        List transactions sent/received/generated by an account, or all accounts

        :param account: Account to list TXs for
        :param count: Load this many recent TXs
        :param skip: Skip this many recent TXs (for pagination)
        :param watch_only: Include watchonly addresses
        :return: [ {account, address, category, amount, label, vout, fee, confirmations, trusted, generated,
                    blockhash, blockindex, blocktime, txid, walletconflicts, time, timereceived, comment,
                    to, otheraccount, bip125-replaceable, abandoned}, ... ]
        """
        return self.call('listtransactions', account, count, skip, watch_only)
    
    def getblockchaininfo(self) -> dict:
        """
        Get information about the blockchain, such as the current block/header height, network difficulty etc.

        :return dict networkinfo: Returns blockchain information as a dict, in this format

        Return format::

            {
                chain:str, blocks:int, headers: int, bestblockhash: str, difficulty: float,
                mediantime: int, verificationprogress: float, initialblockdownload: bool,
                chainwork: str, size_on_disk: int, pruned: bool, softforks: List[dict],
                bip9_softforks: Dict[dict], warnings: str
            }
        
        """
        return self.call('getblockchaininfo')
    
    def getnetworkinfo(self) -> dict:
        """
        Get information about the network, such as daemon version, relay fees, total connections etc.

        :return dict networkinfo: Returns network information as a dict, in this format

        Return format::

            {
                version:int, subversion:str, localservices:str, localrelay:bool,
                timeoffset:int, networkactive:bool, connections:int, networks:List[dict],
                relayfee:float, incrementalfee:float, localaddresses:List[dict], warnings:str
            }

        """
        return self.call('getnetworkinfo')
    
    def getinfo(self) -> dict:
        """
        WARNING: This is deprecated in favour of getnetworkinfo/getblockchaininfo, and is only here for compatibility
        with older cryptocurrency daemons.

        :return dict daemoninfo: Various status info, such as current block, balance etc. See below.

        Return format::

            {
                version:int, protocolversion: int, walletversion: int, balance: float, blocks:int,
                timeoffset: int, connections: int, proxy: str, difficulty: float, testnet: bool,
                keypoololdest: int, keypoolsize: int, paytxfee: float, relayfee: float, warnings: str
            }
        
        """
        return self.call('getinfo')


class LitecoinRPC(BitcoinRPC):
    """
    Wrapper class for JsonRPC, with default host 127.0.0.1 and port 8332
    """
    def __init__(self, hostname='127.0.0.1', port=9332, username=None, password=None, ssl=False, timeout=120,
                 url: str = '', auth: str = 'plain'):
        super().__init__(
            hostname=hostname, port=port, username=username, password=password, 
            ssl=ssl, timeout=timeout, url=url, auth=auth
        )


class SteemEngineRPC(JsonRPC):
    """
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
    DEF_HOST = 'api.steem-engine.com'
    DEF_URL = '/rpc/contracts'

    def __init__(self, hostname=DEF_HOST, port=443, username=None, password=None, ssl=True, timeout=120, url=DEF_URL, auth='plain'):
        super().__init__(
            hostname=hostname, port=port, username=username, password=password, 
            ssl=ssl, timeout=timeout, url=url, auth=auth
        )

    def getcontract(self, name: str) -> dict:
        """
        Returns information about a given contract, such as 'tokens'
        :param name: Name of the contract, e.g. tokens
        :return: None if not found
        :return: {name, owner, code, codeHash, tables, $loki}
        """
        return self.call('getContract', name=name)

    def findone(self, contract: str, table: str, query: dict) -> dict:
        """
        Returns the first result of a contract table query as a dictionary

            >>> rpc = SteemEngineRPC()
            >>> t = rpc.findone(contract='tokens',table='tokens',query=dict(symbol='ENG'))
            >>> t['name']
            'Steem Engine Token'

        :param contract: Name of the contract, e.g. tokens
        :param table: The table of the contract to query, e.g. balances
        :param query: A dictionary query for filtering results, e.g. {'account': 'someguy123'}
        :return: None if not found
        :return: Dictionary containing the row data
        """
        return self.call('findOne', contract=contract, table=table, query=query)

    def find(self, contract, table, query: dict = None, limit: int = 1000,
             offset: int = 0, indexes: list = None) -> list:
        """
        Returns a list of matching rows for a given contract table query

        Example - Get a list of all tokens (max 1000 results by default):

            >>> rpc = SteemEngineRPC()
            >>> t = rpc.find(contract='tokens',table='tokens')

        :param contract: Name of the contract, e.g. tokens
        :param table: The table of the contract to query, e.g. balances
        :param query: A dictionary query for filtering results, e.g. {'account': 'someguy123'} (Default: {})
        :param limit: Maximum results to retrieve
        :param offset: Skip this many results
        :param indexes:
        :return: A list of matching rows, as dict's
        """
        return self.call(
            'find',
            contract=contract,
            table=table,
            query=query if query is not None else {},
            limit=limit,
            offset=offset,
            indexes=indexes if indexes is not None else []
         )

"""
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

Python Json RPC - A simple library for interacting with JsonRPC services
Copyright (c) 2019    Privex Inc. ( https://www.privex.io )

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation 
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, 
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the 
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of 
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS 
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name(s) of the above copyright holders shall not be used in advertising or 
otherwise to promote the sale, use or other dealings in this Software without prior written authorization.
"""
