import bottle, jsonrpc, sys

def with_rpc(orig_func):
    '''Function decorator to provide RPC service proxy'''
    def wrapped_func(*arg, **kwarg):
        app = bottle.default_app()
        svc = app.config['coinrpc.svc']
        return orig_func(svc, *arg, **kwarg)
    return wrapped_func
    
@bottle.get('/help')
@with_rpc
def help(rpc):
    hdoc = rpc.help()
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
