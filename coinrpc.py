from gevent import Greenlet, monkey, core; monkey.patch_all()

import bottle, jsonrpc, sys

class DuplicateKeyError(Exception):
    pass

class CoinBank(object):
    def __init__(self, config):
        self.acct  = config['coinrpc.acct']
        self.svc   = config['coinrpc.svc']
        self.ratio = float(config['coinrpc.ratio'])
        self.txfee = float(config['coinrpc.txfee'])
        self.interval  = float(config['coinrpc.interval'])

        self.next_payout = core.time() + self.interval
        self.pending = {}
        self.paid = [(0,0)]
        self.making_payment = False

    @property
    def balance(self):
        return float(self.svc.getbalance(self.acct))

    @property
    def public_address(self):
        return self.svc.getaccountaddress(self.acct)

    def get_total_pending(self):
        return sum(self.pending.values())

    def get_available(self):
        return self.balance - self.get_total_pending() - self.txfee

    def get_current_payout(self):
        return min(self.ratio * self.get_available(), 1000)

    def get_pay_status(self):
        '''This method should be greenthread-atomic'''
        return (len(self.paid), sum(self.pending.values()))

    def schedule_payment(self, addr):
        if not self.svc.validateaddress(addr)['isvalid']:
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
    '''Function decorator to provide coinrpc bank'''
    def wrapped_func(*arg, **kwarg):
        app = bottle.default_app()
        bank = app.config['coinrpc.bank']
        return orig_func(bank, *arg, **kwarg)
    return wrapped_func

@with_bank
def make_payments(bank):

    amt = bank.get_total_pending()
    Greenlet.spawn_later(bank.interval, globals()['make_payments'])

    if amt == 0:
        return False

    to_pay = bank.pending
    bank.pending = {}
    bank.paid += [(core.time(), amt)]

    bank.svc.sendmany(bank.acct, to_pay)

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
    return """
Donation address is: {}
<br>
Available funds are: {}
<br>
Current payout is: {}
<br>
Total pending payouts are: {}
<br>
Last payout was on {} for {}
""".format(
    bank.public_address,
    bank.get_available(),
    bank.get_current_payout(),
    bank.get_total_pending(),
    bank.paid[-1][0],
    bank.paid[-1][1],
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
        conf_file = 'coin.conf'

    config = app.config.load_config(conf_file)

    url = 'http://%s:%s@%s:%s' % (
        config['coinrpc.user'],
        config['coinrpc.pass'],
        config['coinrpc.host'],
        config['coinrpc.port'],
    )

    svc = jsonrpc.ServiceProxy(url)
    config['coinrpc.svc'] = svc

    bank = CoinBank(config)
    config['coinrpc.bank'] = bank

    # GeventServer is more fragile than the default WSGIRefServer: extra
    # arguments must be filtered out of config
    gevent_conf = {'server': 'gevent'}
    for key, val in config.items():
        if '.' not in key and key not in ('catchall','autojson'):
            gevent_conf[key] = val

    Greenlet.spawn_later(bank.interval, make_payments)
    app.run(**gevent_conf)
