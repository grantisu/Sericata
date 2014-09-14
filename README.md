Sericata
========

Sericata is a simple Bitcoin/Litecoin/Dogecoin/etc. faucet written in Python.


Usage
-----

- Set up a [virtualenv](
  http://docs.python-guide.org/en/latest/dev/virtualenvs/ ) with Python 2.7

- Run `pip install -r requirements.txt` to install dependencies.

- Install and configure a [client]( https://en.bitcoin.it/wiki/Bitcoind ) to
  support RPC.

- Edit sericata.conf with your RPC credentials, desired faucet parameters, etc.
  You may also want to edit logging.conf, e.g. to talk to syslog.

- Edit style.css and the templates to make things look pretty.

- Run `./sericata.py`


About
-----

Sericata uses gevent and Bottle, and thus is named after the common green
bottle fly, _Lucilia sericata_.


License
-------

Sericata is relasesd under the terms of the MIT license, as explained in the
LICENSE file.

