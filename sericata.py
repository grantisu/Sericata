from gevent import Greenlet, monkey, core; monkey.patch_all()

import bottle, jsonrpc, sys
import logging, logging.config

try:
    from recaptcha.client import captcha
except ImportError:
    captcha = None

try:
    import qrcode
except ImportError:
    qrcode = None

class DuplicateKeyError(Exception):
    pass

class CoinBank(object):
    def __init__(self, config):
        self.url       = config['rpc.url']
        self.acct      = config['faucet.acct']
        self.ratio     = float(config['faucet.ratio'])
        self.txfee     = float(config['faucet.txfee'])
        self.interval  = float(config['faucet.interval'])
        self.max_pay   = float(config['faucet.max_payout'])
        self.qr_regen  = config['qrcode.generate']
        self.qr_path   = config['qrcode.path']
        self.qr_file   = config['qrcode.file']

        logging.config.fileConfig(config['logging.config_file'])
        self.log = logging.getLogger('CoinBank')

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
            'm': ('test-coin', u'\u0166'),
            'n': ('test-coin', u'\u0166'),
        }.get(self.public_address[0], ('UNK', '?'))

        if 'recaptcha.pub_key' in config:
            if captcha:
                self.captcha_html =  captcha.displayhtml(config['recaptcha.pub_key'])
                self.captcha_priv_key = config['recaptcha.priv_key']
            else:
                raise Exception("Can't use api keys: failed to import from recaptcha.client")
        else:
            self.captcha_html =  ''
            self.captcha_priv_key = None

        self.log.info('Started new CoinBank instance (%s)', self.coin)

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
            if self.qr_regen:
                qr = qrcode.QRCode()
                qr.add_data(self._public_address)
                qr_img = qr.make_image()
                qr_img.save(self.qr_path + '/' + self.qr_file)
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
        return min(self.ratio * self.get_available(), self.max_pay)

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

        if amt > 0:
            self.pending[addr] = amt
            self.log.info('Scheduled payment of %f to %s', amt, addr)
        else:
            self.log.warning('Attempted to schedule a payment with zero funds')
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
        bank.log.debug('Payment period ended with no scheduled payments')
        return False

    svc = bank.get_proxy()
    to_pay = bank.pending
    bank.pending = {}
    bank.paid += [(core.time(), amt)]

    svc.sendmany(bank.acct, to_pay)
    vals = to_pay.values()
    bank.log.info('Made payments totalling %f to %d addresses', sum(vals), len(vals))

def http_err(code, body):
    code_map = {
        400: 'Bad Request',
        403: 'Forbidden',
        595: 'Insufficient Funds',
    }

    return bottle.HTTPResponse(
        status = code,
        body = '<h3>%d %s</h3>\n%s<p><a href="./">Go Back</a>' % (code, code_map[code], body)
    )

@bottle.get('/')
@with_bank
def make_main_page(bank):
    return bottle.template(
        'main',
        captcha_html = bank.captcha_html,
        **bank.get_public_status()
    )

@bottle.get('/stats')
@with_bank
def make_stats_page(bank):
    return bottle.template('stats', **bank.get_public_status())

@bottle.get('/donate.png')
@with_bank
def show_donate(bank):
    return bottle.static_file(bank.qr_file, bank.qr_path)

@bottle.get('/style.css')
def show_style():
    app = bottle.default_app()
    return bottle.static_file(
        app.config['style.file'],
        app.config['style.path'],
    )

@bottle.post('/payout')
@with_bank
def attempt_payout(bank):
    form = bottle.request.forms
    addr = form.get('addr')

    if captcha and bank.captcha_priv_key:
        response = captcha.submit(
            form.get('recaptcha_challenge_field'),
            form.get('recaptcha_response_field'),
            bank.captcha_priv_key,
            bottle.request['REMOTE_ADDR'],
        )
        if not response.is_valid:
            return http_err(403, "I think you're a robot!")

    try:
        amt = bank.schedule_payment(addr)
    except ValueError:
        return http_err(400, "Invalid address: "+addr)
    except DuplicateKeyError:
        return http_err(400, "Address "+addr+" already queued")

    if amt == 0:
        return http_err(595, "Out of "+bank.coin)

    return bottle.template('payout', amount=amt, address=addr, **bank.get_public_status())

if __name__ == '__main__':
    app = bottle.default_app()
    try:
        conf_file = sys.argv[1]
    except IndexError:
        conf_file = 'sericata.conf'

    config = app.config.load_config(conf_file)

    url = 'http://%s:%s@%s:%s' % (
        config['rpc.user'],
        config['rpc.pass'],
        config['rpc.host'],
        config['rpc.port'],
    )
    config['rpc.url'] = url

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
