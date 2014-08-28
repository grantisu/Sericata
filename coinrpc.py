import bottle, jsonrpc, sys

def with_coinrpc(*items):
    '''Function decorator to provide coinrpc config items'''
    def wrap_func(orig_func):
        app = bottle.default_app()
        keys = tuple(['coinrpc.' + i for i in items])
        def wrapped_func(*arg, **kwarg):
            config_items = tuple([app.config[k] for k in keys])
            arg = config_items + arg
            return orig_func(*arg, **kwarg)
        return wrapped_func
    return wrap_func
    
@bottle.get('/help')
@with_coinrpc('svc')
def help(svc):
    hdoc = svc.help()
    return hdoc.replace('\n', '<br>')

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

    app.run(**config)
