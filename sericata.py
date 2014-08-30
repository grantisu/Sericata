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
    return """
Donation address is: {}
<br>
Current payout is: {}
<br>
<form action="/payout" method="post">
  Address: <input name="addr" type="text" />
  <input value="payout" type="Submit">
</form>
""".format(bank.public_address, bank.get_current_payout())

@bottle.get('/stats')
@with_bank
def make_stats_page(bank):
    last_time, last_amt = bank.paid[-1]
    next_time = bank.last_pay_time + bank.interval
    return """
Donation address is: {}
<br>
Available funds are: {}
<br>
Current payout is: {}
<br>
Total pending payouts are: {}
<br>
Total pay periods elapsed: {}
<br>
Last payout was on {} for {}
<br>
Next payout will be in {} seconds
""".format(
    bank.public_address,
    bank.get_available(),
    bank.get_current_payout(),
    bank.get_total_pending(),
    bank.pay_periods,
    last_time,
    last_amt,
    next_time - core.time(),
)

@bottle.post('/payout')
@with_bank
def attempt_payout(bank):
    form = bottle.request.forms
    addr = form.get('addr')
    try:
        amt = bank.schedule_payment(addr)
    except ValueError:
        return bottle.HTTPResponse(status = 400, body = "Bad address: "+addr)
    except DuplicateKeyError:
        return bottle.HTTPResponse(status = 400, body = addr+" already queued")

    return "Scheduled {} to {}".format(amt, addr)


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
