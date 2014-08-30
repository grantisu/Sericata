from gevent import Greenlet, monkey, core; monkey.patch_all()

import bottle, jsonrpc, sys

class DuplicateKeyError(Exception):
    pass

class CoinBank(object):
    def __init__(self, config):
        self.acct      = config['sericata.acct']
        self.url       = config['sericata.url']
        self.ratio     = float(config['sericata.ratio'])
        self.txfee     = float(config['sericata.txfee'])
        self.interval  = float(config['sericata.interval'])

        self.pending = {}
        self.paid = [(0,0)]
        self.pay_periods = 0
        self.last_pay_time = core.time()

        self._balance_stat = 0
        self._balance = self.balance

        self._public_address_stat = 0
        self._public_address = self.public_address

        self.coin, self.symbol = {
            '1': ('BTC',  u'\u0243'),
            'L': ('LTC',  u'\u0141'),
            'D': ('DOGE', u'\u0189'),
            'N': ('NAME', u'\u2115'),
            'P': ('PPC',  u'\u2C63'),
            'm': ('test', u'\u0166'),
            'n': ('test', u'\u0166'),
        }.get(self.public_address[0], ('UNK', '?'))

        if 'sericata.recaptcha_pub' in config:
            self.recaptcha_pub_key =  config['sericata.recaptcha_pub']
            self.recaptcha_priv_key = config['sericata.recaptcha_priv']
        else:
            self.recaptcha_pub_key =  None
            self.recaptcha_priv_key = None

    @property
    def balance(self):
        svc = None
        while self._balance_stat != self.get_pay_status():
            if svc is None:
                svc = self.get_proxy()
            self._balance_stat = self.get_pay_status()
            self._balance = float(svc.getbalance(self.acct))
        return self._balance

    @property
    def public_address(self):
        svc = None
        while self._public_address_stat != self.get_pay_status():
            if svc is None:
                svc = self.get_proxy()
            self._public_address_stat = self.get_pay_status()
            self._public_address = svc.getaccountaddress(self.acct)
        return self._public_address

    def get_proxy(self):
        return jsonrpc.ServiceProxy(self.url)

    def get_total_pending(self):
        return sum(self.pending.values())

    def get_available(self):
        net = self.balance - self.get_total_pending() - self.txfee
        if net < 0:
            net = 0
        return net

    def get_current_payout(self):
        return min(self.ratio * self.get_available(), 1000)

    def get_pay_status(self):
        '''This method should be greenthread-atomic'''
        return (len(self.paid), sum(self.pending.values()), self.pay_periods)

    def get_public_status(self):

        time = core.time()
        last_time, last_amt = self.paid[-1]
        return {
            'coin':              self.coin,
            'symbol':            self.symbol,
            'current_funds':     self.get_available(),
            'current_payout':    self.get_current_payout(),
            'last_payout_time':  last_time,
            'last_payout_total': last_amt,
            'total_pay_periods': self.pay_periods,
            'payout_interval':   self.interval,
            'current_address':   self.public_address,
            'current_time':      time,
            'next_payout_time':  self.last_pay_time + self.interval,
            'next_payout_total': self.get_total_pending(),
            'recaptcha_pub_key': self.recaptcha_pub_key,
        }

    def schedule_payment(self, addr):
        svc = self.get_proxy()
        if not svc.validateaddress(addr)['isvalid']:
            raise ValueError
        if addr in self.pending:
            raise DuplicateKeyError

        while 1:
            pay_status = self.get_pay_status()
            amt = self.get_current_payout()
            # Check to make sure nothing happened
            if pay_status == self.get_pay_status():
                break

        self.pending[addr] = amt
        return amt

def with_bank(orig_func):
    '''Function decorator to provide CoinBank instance'''
    def wrapped_func(*arg, **kwarg):
        app = bottle.default_app()
        bank = app.config['sericata.bank']
        return orig_func(bank, *arg, **kwarg)
    return wrapped_func

@with_bank
def make_payments(bank):

    bank.pay_periods += 1
    bank.last_pay_time = core.time()
    amt = bank.get_total_pending()
    Greenlet.spawn_later(bank.interval, globals()['make_payments'])

    if amt == 0:
        return False

    svc = bank.get_proxy()
    to_pay = bank.pending
    bank.pending = {}
    bank.paid += [(core.time(), amt)]

    svc.sendmany(bank.acct, to_pay)

@bottle.get('/')
@with_bank
def make_main_page(bank):
    return bottle.template('main', **bank.get_public_status())

@bottle.get('/stats')
@with_bank
def make_stats_page(bank):
    return bottle.template('stats', **bank.get_public_status())

@bottle.post('/payout')
@with_bank
def attempt_payout(bank):
    form = bottle.request.forms
    addr = form.get('addr')
    e400 = "<h3>400 Bad Request</h3>"
    try:
        amt = bank.schedule_payment(addr)
    except ValueError:
        return bottle.HTTPResponse(status = 400, body = e400+"Invalid address: "+addr)
    except DuplicateKeyError:
        return bottle.HTTPResponse(status = 400, body = e400+"Address "+addr+" already queued")

    return bottle.template('payout', amount=amt, address=addr, symbol=bank.symbol)

if __name__ == '__main__':
    app = bottle.default_app()
    try:
        conf_file = sys.argv[1]
    except IndexError:
        conf_file = 'sericata.conf'

    config = app.config.load_config(conf_file)

    url = 'http://%s:%s@%s:%s' % (
        config['sericata.user'],
        config['sericata.pass'],
        config['sericata.host'],
        config['sericata.port'],
    )
    config['sericata.url'] = url

    bank = CoinBank(config)
    config['sericata.bank'] = bank

    # GeventServer is more fragile than the default WSGIRefServer: extra
    # arguments must be filtered out of config
    gevent_conf = {'server': 'gevent'}
    for key, val in config.items():
        if '.' not in key and key not in ('catchall','autojson'):
            gevent_conf[key] = val

    Greenlet.spawn_later(bank.interval, make_payments)
    app.run(**gevent_conf)
