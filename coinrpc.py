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

    def get_total_pending(self):
        return sum(self.pending.values())

    def get_available(self):
        return self.balance - self.get_total_pending() - self.txfee

    def get_current_payout(self):
        return self.ratio * self.get_available()


def with_bank(orig_func):
    '''Function decorator to provide coinrpc bank'''
    def wrapped_func(*arg, **kwarg):
        app = bottle.default_app()
        bank = app.config['coinrpc.bank']
        return orig_func(bank, *arg, **kwarg)
    return wrapped_func
    
@bottle.get('/help')
@with_bank
def help(bank):
    hdoc = bank.svc.help()
    return hdoc.replace('\n', '<br>')

@bottle.get('/current_payout')
@with_bank
def get_balance(bank):
    return str(bank.get_current_payout())

@bottle.get('/balance')
@with_bank
def get_balance(bank):
    return str(bank.balance)

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
