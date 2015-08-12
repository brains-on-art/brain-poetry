import time
import zmq

#port = 5556

#print('Connecting to server....')
#context = zmq.Context()
#socket  = context.socket(zmq.REQ)
#socket.connect("tcp://127.0.0.1:{}".format(port))

# Logging helpers FIXME: move to utility library
time_str = lambda: time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
log_msg = lambda msg: print('{}: {}'.format(time_str(), msg))


class PoemClient(object):
    API_VERSION = '0.1'
    API_DATE    = '2015-08-12'

    def __init__(self, port=5556):
        self.context = zmq.Context()
        self.socket  = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://127.0.0.1:{}".format(port))

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




def test(port):
    log_msg('Connecting to server on port {}....'.format(port))
    context = zmq.Context()
    socket  = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:{}".format(port))

    server.send_signal(signal.SIGINT)
    server_log.close()

def start_server(port):
    log_msg('Starting server subprocess on port {}...'.format(port))
    import os
    import subprocess
    server_log = time_str + '_poem_server_test.log'
    server = subprocess.Popen(['python3',os.path.realpath(__file__), '--port', port], stdout=server_log)


if __name__ == '__main__':
    pass
    

def test_malformed_request(socket, request=None):
    if request is not None:
        bad_request = request
    else:
        bad_request = {}
        bad_request['command'] = 'malformed'
        bad_request['content'] = 'FOOBAR'
    print('Sending malformed request: {}'.format(bad_request))
    socket.send_json(bad_request)

    print('Waiting for response...')
    response = socket.recv_json()
    print('Got response: {}'.format(response))

def test_request(socket, language, category):
    generate_request = {}
    generate_request['command'] = 'generate_poem'
    generate_request['language'] = language
    generate_request['category'] = category
    print('Sending generate_poem request: {}'.format(generate_request))
    socket.send_json(generate_request)

    print('Waiting for response...')
    response = socket.recv_json()
    print('Got response: {}'.format(response))
        
    get_request = {}
    get_request['command'] = 'get_poem'
    print('Sending get_poem request: {}'.format(get_request))

    print('Waiting for response...')
    response = socket.recv_json()
    print('Got response: {}'.format(response))





