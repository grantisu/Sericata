import bottle, jsonrpc, sys

class CoinBank(object):
    def __init__(self, config):
        self.acct  = config['coinrpc.acct']
        self.svc   = config['coinrpc.svc']
        self.ratio = float(config['coinrpc.ratio'])
        self.txfee = float(config['coinrpc.txfee'])

        self.pending = {}

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

    def make_payment(self, addr):
        if not self.svc.validateaddress(addr)['isvalid']:
            raise ValueError
        amt = self.get_current_payout()
        txid = self.svc.sendfrom(self.acct, addr, amt)
        return (amt, txid)

def with_bank(orig_func):
    '''Function decorator to provide coinrpc bank'''
    def wrapped_func(*arg, **kwarg):
        app = bottle.default_app()
        bank = app.config['coinrpc.bank']
        return orig_func(bank, *arg, **kwarg)
    return wrapped_func

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

@bottle.post('/payout')
@with_bank
def attempt_payout(bank):
    form = bottle.request.forms
    addr = form.get('addr')
    try:
        amt, txid = bank.make_payment(addr)
    except ValueError:
        return bottle.HTTPResponse(status = 400, body = "Bad address: "+addr)

    return "Sent {} in transaction '{}'".format(amt, txid)


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

    app.run(**config)
