import argparse
import signal
from threading import Thread
import time
import zmq
try:
    from queue import Queue, Empty
except ImportError: # Python2
    from Queue import Queue, Empty


# Logging helpers FIXME: move to utility library
time_str = lambda: time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
log_msg = lambda msg: print('{}: {}'.format(time_str(), msg))


## POETRY GENERATION ##########################################################

# FIXME: NYT OIKEESTI!!!
import sys
sys.path.append('../../apparatus/apparatus/')
try:
    from generate_poem import generate as get_poem_fi
except ImportError:
    log_msg('Finnish poem generation import error, using placeholder function...')
    get_poem_fi = lambda category: 'Poem {} {}'.format('finnish', category)
try:
    from generate_poem_eng import generate as get_poem_en
except ImportError:
    log_msg('English poem generation import error, using placeholder function...')
    get_poem_en = lambda category: 'Poem {} {}'.format('english', category)
try:
    from german_poetry_generation.german_poem import generate_german_poem as get_poem_de
except:
    log_msg('German poem generation import error, using placeholder function...')
    get_poem_de = lambda category: 'Poem {} {}'.format('german', category)


# Poetry generators
generators = {'finnish' : get_poem_fi,
              'english' : get_poem_en,
              'german'  : get_poem_en}
categories = {'finnish' : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
              'english' : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
              'german'  : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
assert generators.keys() == categories.keys(), 'Must specify both generator and categories for each language'

poemgen_q = Queue()
def generate_poem(language, category):
    poem = generators[language](category) # get_poem_fi etc. 
    poemgen_q.put((category, poem))


## API ########################################################################

class PoemServer(object):
    API_VERSION = '0.1'
    API_DATE    = '2015-08-12'

    def __init__(self, socket):
        self.socket = socket

    # Create response dictionary
    def create_response(self, response_type, message, originating_request):
        response = {}
        response['type']    = response_type
        response['message'] = message
        response['request'] = request
        return response

    # Send error response
    def send_error(self, socket, originating_request):
        error = create_response('error', 'Bad request', originating_request)
        log_msg('Sending error message: {}'.format(error))
        socket.send_json(error)

    # Send acknowledge response
    def send_ack(self, socket, originating_request):
        ack = create_response('acknowledge', 'Request acknowledged', originating_request)
        log_msg('Sending acknowledge: {}'.format(ack))
        socket.send_json(ack)

    # Send poem response
    def send_poem(self, socket, originating_request, poem, category):
        poem = create_response('poem', 'Poem generated', originating_response)
        poem['poem']     = poem
        poem['category'] = category
        log_msg('Sending poem: {}'.format(poem))
        socket.send_json(poem)

    # Send API response
    def send_api(self, socket, originating_request):
        api = create_response('api_info', 'API information', originating_request)
        api['available_commands']   = ['generate_poem', 'get_api', 'get_poem', 'help']
        api['available_languages']  = generators.keys()
        api['available_categories'] = categories
        api['api_version']          = API_VERSION
        api['api_date']             = API_DATE
        log_msg('Sending API: {}'.format(api))
        socket.send_json(api)

    # Check request validity
    def check_request(self, request):
        good = True
        try:
            if request == {} or request['command'] in ['get_api', 'get_poem', 'help']:
                pass
            elif request['command'] == 'generate_poem':       
                if request['language'] not in generators.keys() or \
                   request['category'] not in categories[request['language']]:
                    good = False
            else:
                good = False
        except KeyError:
            good = False
        return good 

    def process(self, request):
        if check_request(request): # Good request?
            if request == {} or request['command'] in ['get_api', 'help']:
                send_api(socket, request)
            elif request['command'] == 'generate_poem': 
                log_msg('Starting to generate poem in {} category {}'.format(request['language'], 
                                                                             request['category']))
                poemgen_thr = Thread(target=generate_poem, 
                                     args=[request['language'], 
                                           request['category']])
                poemgen_thr.start()
                send_ack(socket, request)
            # FIXME: Should we send an error if a get request comes without
            #        a generate request?
            elif request['command'] == 'get_poem': 
                category, poem = None, None
                try:
                    category, poem = poemgen_q.get_nowait()
                    log_msg('Poem generated!')
                except Empty:
                    pass
                
                if category is not None and poem is not None:
                    send_poem(socket, request, poem, category)
                else:
                    send_ack(socket, request)               
        else:
            send_error(socket, request)



# FIXME: global running flag for SIGINT detection
running = True

def server(port):
    # Handle SIGINT
    def signal_handler(signal, frame):
        global running
        log_msg('Received SIGINT/SIGTERM, quitting...')
        running = False
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start listening to port
    port = port
    log_msg('Starting to server poems on port {}...'.format(port))
    context = zmq.Context()
    socket  = context.socket(zmq.REP)
    socket.bind("tcp://127.0.0.1:{}".format(port))

    # Create poem server on socket
    server = PoemServer(socket)
    
    # Main loop
    while running:
        # Get request
        try:
            request = socket.recv_json(zmq.NOBLOCK)
        except zmq.ZMQError as e: 
            request = None
        if request is not None:
            log_msg('Received request: {}'.format(message))
            poem_server.process(request)
        time.sleep(0.1)
    
    # Finalize
    log_msg('Shutting down server on port {}...'.format(port))        
    socket.close()
    context.term()




    
    
    


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(description='Poem server')
    parser.add_argument('--test', action='store_true') 
    parser.add_argument('--port', default=5556, type=int, help='Server port')

    args = parser.parse_args()

    if args.test:
        print('Testing...')
        import os
        print(os.path.realpath(__file__))
    else:
        server(args.port)
