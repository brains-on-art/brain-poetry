import time
import zmq
from poem_server import DEFAULT_PORT


# Logging helpers FIXME: move to utility library
file_time_str = lambda: time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime())
time_str = lambda: time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
log_msg = lambda msg: print('{}: {}'.format(time_str(), msg))


class PoemClient(object):
    API_VERSION = '0.1'
    API_DATE    = '2015-08-12'

    def __init__(self, host='127.0.0.1', port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket  = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://{}:{}".format(host,port))

    def generate_poem(self, language, category):
        request = {}
        request['command']  = 'generate_poem'
        request['language'] = language
        request['category'] = category
        self.socket.send_json(request)

        return self.socket.recv_json()

    def get_poem(self):
        request = {}
        request['command'] = 'get_poem'
        self.socket.send_json(request)

        return self.socket.recv_json()

    def get_api(self):
        request = {}
        request['command'] = 'get_api'
        self.socket.send_json(request)

        return self.socket.recv_json()


def test_malformed_request(socket, request=None):
    if request is not None:
        bad_request = request
    else:
        bad_request = {}
        bad_request['command'] = 'malformed'
        bad_request['content'] = 'FOOBAR'
    log_msg('Sending malformed request: {}'.format(bad_request))
    socket.send_json(bad_request)

    log_msg('Waiting for response...')
    response = socket.recv_json()
    log_msg('Got response: {}'.format(response))



def test(port=DEFAULT_PORT):
    import os
    import signal
    import subprocess
    log_msg('Starting server subprocess on port {}...'.format(port))
    server_log = open(file_time_str() + '_poem_server_test.log', 'w')
    server_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'poem_server.py') 
    server = subprocess.Popen(['python3', server_path, '--port', str(port)], stdout=server_log)
    
    log_msg('Starting client on port {}...'.format(port))
    client = PoemClient(port=port)

    log_msg('Getting server API...')
    api_resp = client.get_api()
    #log_msg('Got: {}'.format(api_resp))

    log_msg('Available languages: {}'.format(api_resp['available_languages']))
    log_msg('Iterating over available languages and requesting poems...')
    for lang in api_resp['available_languages']:
        log_msg('  {}:'.format(lang))
        for cat in api_resp['available_categories'][lang]:
            client.generate_poem(lang, cat)
            time.sleep(1)
            poem_resp = client.get_poem()
            log_msg('    {}'.format(poem_resp['poem']))


    test_malformed_request(client.socket)

    log_msg('Stopping server subprocess...')
    server.send_signal(signal.SIGINT)

if __name__ == '__main__':
    test()
    







