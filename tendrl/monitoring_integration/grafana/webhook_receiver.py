from gevent.pywsgi import WSGIServer


def application(env, start_response):
    if env['PATH_INFO'] == '/grafana_callback':
        start_response('200 OK', [('Content-Type', 'text/html')])

        # TODO(Rishubh) Receive Data and call parsing functions 
        # data = env['wsgi.input'].read()

        return [b"<b>Recieved</b>"]

    start_response('404 Not Found', [('Content-Type', 'text/html')])
    return [b'<h1>Not Found</h1>']


def start_server():
    WSGIServer(('', 8789), application).serve_forever()

