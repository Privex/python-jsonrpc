import json
import requests
import logging
from json import JSONDecodeError
from _decimal import Decimal

log = logging.getLogger(__name__)


class RPCException(BaseException):
    """Thrown when 'error' is present in the result, and is not None/False"""
    pass


class JsonRPC:
    """
    JsonRPC - a small Python class for querying JSON RPC servers over HTTP / HTTPS

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
    
    Basic usage:

        >>>  j = JsonRPC(hostname='api.example.com', port=443, ssl=True)
        >>>  j.get_someinfo('my first parameter')
        ['some', 'result', 'data', 'returned']
    
    If a method is not defined, you can still use it! You just won't get any IDE hints with the parameters.
    """

    LAST_ID = 0

    # Using a python-requests session will help to encourage connection re-use, e.g. HTTP Keep-alive
    # Since this is a static attribute, it will be shared across ALL instances of the class.
    req = requests.Session()

    def __init__(self, hostname, port: int = 80, username=None, password=None, ssl=False, timeout=120, url: str = ''):
        """
        Configure the remote JSON RPC server settings

        :param hostname: The hostname or IP address of the JSON RPC server
        :param port:     The JSON RPC TCP port to connect to
        :param username: If the RPC server needs a username, specify it here
        :param password: If the RPC server needs a password, specify it here (username must also be set)
        :param ssl:      If set to True, will use https for requests. Default is false - use plain http
        :param timeout:  If the server stops sending us data for this many seconds, abort and throw an exception
        :param url:      The URL to query, e.g. api/v1/test (starting /'s will automatically be removed)
        """
        self.timeout = timeout
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.ssl = ssl
        self.endpoint = url

    @property
    def url(self):
        url = self.endpoint
        proto = 'https' if self.ssl else 'http'
        host = '{}:{}'.format(self.hostname, self.port)
        if self.username is not None:
            host = '{}:{}@{}:{}'.format(self.username, self.password, self.hostname, self.port)
        url = url[1:] if len(url) > 0 and url[0] == '/' else url  # Strip starting / of URL

        return "{}://{}/{}".format(proto, host, url)

    @property
    def next_id(self):
        JsonRPC.LAST_ID += 1
        return JsonRPC.LAST_ID

    def call(self, method, *params, **dicdata):
        """
        Calls a JSON RPC method with method 'params' being the positional args passed as a list.

        If keyword args are passed, params will be a dict of the kwargs `dicdata` and positional args will be ignored.

        If both positional and keyword args are empty, params will be set to an empty list []

        :param method: JSON RPC method to call
        :param params: Parameters to be passed as a list as 'params' in the JSON request body
        :param dicdata: Arguments to be passed as a dict as 'params' in the JSON request body (overrides params)
        :raises RPCException: When an RPC call returns with a non-null/non-false 'error' key
        :return: dict() or list() of results, depending on what format the method returns.
        """
        headers = {'content-type': 'application/json'}

        payload = {
            "method": method,
            "params": list(params),
            "jsonrpc": "2.0",
            "id": self.next_id,
        }
        # If kwargs are passed, payload params is a dictionary of the kwargs instead of positionals
        if len(dicdata.keys()) > 0:
            payload['params'] = dict(dicdata)
        r = None
        try:
            log.debug('Sending JsonRPC request to %s with payload: %s', self.url, payload)
            r = self.req.post(self.url, data=json.dumps(payload), headers=headers, timeout=self.timeout)
            response = r.json()
        except JSONDecodeError as e:
            log.warning('JSONDecodeError while querying %s', self.url)
            log.warning('Params: %s / DicData: %s', params, dicdata)
            t = r.text.decode('utf-8') if type(r.text) is bytes else str(r.text)
            log.warning('Raw response data was: %s', t)
            raise e

        if 'error' in response and response['error'] not in [None, False]:
            raise RPCException(response['error'])
        return response['result']

    def __getattr__(self, name):
        """
        Methods that haven't yet been defined are simply passed off to :meth:`.call` with the positional and kwargs.

        This means `rpc.getreceivedbyaddress(address)` is equivalent to `rpc.call('getreceivedbyaddress', address)`

        :param name: Name of the attribute requested
        :return: Dict or List from call result
        """
        def c(*args, **kwargs):
            return self.call(name, *args, **kwargs)
        return c

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
