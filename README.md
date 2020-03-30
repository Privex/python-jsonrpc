[![PyPi Version](https://img.shields.io/pypi/v/privex-jsonrpc.svg)](https://pypi.org/project/privex-jsonrpc/)
![License Button](https://img.shields.io/pypi/l/privex-jsonrpc) ![PyPI - Downloads](https://img.shields.io/pypi/dm/privex-jsonrpc)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/privex-jsonrpc) 
![GitHub last commit](https://img.shields.io/github/last-commit/Privex/python-jsonrpc)

# Simple Python JsonRPC
### A small library for interacting with JsonRPC services
### Includes some helper classes for various cryptocurrency daemons inc. `bitcoind` and `litecoind`

**Official Repo:** https://github.com/privex/python-jsonrpc

### Quick Install / Usage

```sh
pip3 install privex-jsonrpc
```

```python
from privex.jsonrpc import JsonRPC, RPCException
try:
    j = JsonRPC(hostname='api.example.com', port=443, ssl=True)
    # call JsonRPC methods as if they're part of the class. they return 'result' as dict/list/int/float/str
    j.list_all('first', 'second')    # 'params' as a list ['first', 'second']
    j.find(name='john')              # 'params' as a dict {name: 'john'}
except RPCException as e:   # raised when the result contains the key 'error' and it is not null/false
    log.exception('the rpc server returned an error: %s', str(e))
except:   # Any other exceptions (generally from the `requests` library) mean something is wrong with the server
    log.exception('something went wrong while communicating with the RPC server...')   
```

# Information

This Python JsonRPC library has been developed at [Privex Inc.](https://www.privex.io) by @someguy123 for interacting
with various JsonRPC services, including cryptocurrency daemons such as `bitcoind`.

It uses the [Python Requests](http://docs.python-requests.org/en/master/) library, including a singleton requests session
ensuring that HTTP Keep-alive is always used, cookies are retained, among other things improving performance.



The main classes included are:

```
    JsonRPC        - The main universally-compatible class, works with most JsonRPC services without any modification.

    BitcoinRPC     - Constructor connects to 127.0.0.1:8332 by default. 
                     Includes a few pre-defined methods for interacting with `bitcoind` and similar daemons.
    
    LitecoinRPC    - Same as BitcoinRPC, except uses 127.0.0.1:9332 by default

    SteemEngineRPC - For interacting with SteemSmartContracts RPC (https://github.com/harpagon210/steemsmartcontracts)
                     Includes pre-defined methods for interacting with SSC RPC. 
                     Default host: https://api.steem-engine.com
    
    MoneroRPC      - For interacting with Monero Wallet RPC, includes various pre-defined methods to make things easier.

    ElectrumRPC    - For interacting with Electrum Wallet RPC, includes various pre-defined methods to make things easier.
                     Should work with Bitcoin Electrum, Electrum LTC, and others.

```


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

    Python JSON RPC - A simple library for interacting with JsonRPC services
    Copyright (c) 2019    Privex Inc. ( https://www.privex.io )

# Install

We recommend that you use at least Python 3.4+ due to the usage of parameter and return type hinting.

### Install from PyPi using `pip`

You can install this package via pip:

```sh
pip3 install privex-jsonrpc
```

### (Alternative) Manual install from Git

If you don't want to PyPi (e.g. for development versions not on PyPi yet), you can install the 
project directly from our Git repo.

Unless you have a specific reason to manually install it, you **should install it using pip3 normally**
as shown above.

**Option 1 - Use pip to install straight from Github**

```sh
pip3 install git+https://github.com/Privex/python-jsonrpc
```

**Option 2 - Clone and install manually**

```bash
# Clone the repository from Github
git clone https://github.com/Privex/python-jsonrpc
cd python-jsonrpc

# RECOMMENDED MANUAL INSTALL METHOD
# Use pip to install the source code
pip3 install .

# ALTERNATIVE INSTALL METHOD
# If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
python3 setup.py install
```

# Usage

Import the class that you need from `privex.jsonrpc` - all are exported using the __init__.py

Basic usage:

```python
    from privex.jsonrpc import JsonRPC, RPCException
    try:
        j = JsonRPC(hostname='api.example.com', port=443, ssl=True)

        # Sends a POST request to https://api.example.com with the following data:
        # {id: 1, jsonrpc: '2.0', method: 'list_all', params: ['my first parameter']}
        data = j.list_all('my first parameter')    # returns: ['some', 'result', 'data', 'returned']
        print(data[0])    # prints 'some'

        # Sends a POST request to https://api.example.com with the following data:
        # {id: 2, jsonrpc: '2.0', method: 'find', params: {name: 'john'}}
        data = j.find(name='john')    # returns: {name: 'john', username: 'john123', created_at: '2019-01-01 00:00:00'}
        print(data['username'])       # prints 'john123'

        # If your JsonRPC call is not valid as a method name, use .call(method, *params, **args)
        # positional params are converted to a list, keyworg args are converted to a dict
        j.call('invalid-python.methodname', '1st param', '2nd param')
        j.call('some.find.func', name='john', user='john123')

    except RPCException as e:
        # RPCException is raised when the result contains the key 'error' and it is not null/false
        log.exception('the rpc server returned an error: %s', str(e))
    except:
        # Any other exceptions (generally from the `requests` library) mean something is wrong with the server
        log.exception('something went wrong while communicating with the RPC server...')    
```

**If a method is not defined, you can still use it! You just won't get any IDE hints with the parameters.**

For full parameter documentation, IDEs such as PyCharm and even Visual Studio Code should show our PyDoc
comments when you try to use the class.

For PyCharm, press F1 with your keyboard cursor over the class to see full function documentation, including
return types, parameters, and general usage information. You can also press CMD-P with your cursor inside of 
a method's brackets (including the constructor brackets) to see the parameters you can use.

Alternatively, just view the files inside of `privex/jsonrpc/` - most methods and constructors
are adequently commented with PyDoc.

# Logging

By default, this package will log anything >=WARNING to the console. You can override this by adjusting the
`privex.jsonrpc` logger instance. 

We recommend checking out our Python package [Python Loghelper](https://github.com/Privex/python-loghelper) which
makes it easy to manage your logging configuration, and copy it to other logging instances such as this one.

```python
# Without LogHelper
import logging
l = logging.getLogger('privex.jsonrpc')
l.setLevel(logging.ERROR)

# With LogHelper (pip3 install privex-loghelper)
from privex.loghelper import LogHelper
# Set up logging for **your entire app**. In this case, log only messages >=error
lh = LogHelper('myapp', handler_level=logging.ERROR)
lh.add_file_handler('test.log')      # Log messages to the file `test.log` in the current directory
lh.copy_logger('privex.jsonrpc')     # Easily copy your logging settings to any other module loggers
log = lh.get_logger()                # Grab your app's logging instance, or use logging.getLogger('myapp')
log.error('Hello World')
```

# Contributing

We're very happy to accept pull requests, and work on any issues reported to us. 

Here's some important information:

**Reporting Issues:**

 - For bug reports, you should include the following information:
     - Version of `privex-jsonrpc` and `requests` tested on - use `pip3 freeze`
        - If not installed via a PyPi release, git revision number that the issue was tested on - `git log -n1`
     - Your python3 version - `python3 -V`
     - Your operating system and OS version (e.g. Ubuntu 18.04, Debian 7)
 - For feature requests / changes
     - Please avoid suggestions that require new dependencies. This tool is designed to be lightweight, not filled with
       external dependencies.
     - Clearly explain the feature/change that you would like to be added
     - Explain why the feature/change would be useful to us, or other users of the tool
     - Be aware that features/changes that are complicated to add, or we simply find un-necessary for our use of the tool may not be added (but we may accept PRs)
    
**Pull Requests:**

 - We'll happily accept PRs that only add code comments or README changes
 - Use 4 spaces, not tabs when contributing to the code
 - You can use features from Python 3.4+ (we run Python 3.7+ for our projects)
    - Features that require a Python version that has not yet been released for the latest stable release
      of Ubuntu Server LTS (at this time, Ubuntu 18.04 Bionic) will not be accepted. 
 - Clearly explain the purpose of your pull request in the title and description
     - What changes have you made?
     - Why have you made these changes?
 - Please make sure that code contributions are appropriately commented - we won't accept changes that involve uncommented, highly terse one-liners.

**Legal Disclaimer for Contributions**

Nobody wants to read a long document filled with legal text, so we've summed up the important parts here.

If you contribute content that you've created/own to projects that are created/owned by Privex, such as code or documentation, then you might automatically grant us unrestricted usage of your content, regardless of the open source license that applies to our project.

If you don't want to grant us unlimited usage of your content, you should make sure to place your content
in a separate file, making sure that the license of your content is clearly displayed at the start of the file (e.g. code comments), or inside of it's containing folder (e.g. a file named LICENSE). 

You should let us know in your pull request or issue that you've included files which are licensed
separately, so that we can make sure there's no license conflicts that might stop us being able
to accept your contribution.

If you'd rather read the whole legal text, it should be included as `privex_contribution_agreement.txt`.

# License

This project is licensed under the **X11 / MIT** license. See the file **LICENSE** for full details.

Here's the important bits:

 - You must include/display the license & copyright notice (`LICENSE`) if you modify/distribute/copy
   some or all of this project.
 - You can't use our name to promote / endorse your product without asking us for permission.
   You can however, state that your product uses some/all of this project.



# Thanks for reading!

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io) - prices start at as little as US$8/mo (we take cryptocurrency!)**
