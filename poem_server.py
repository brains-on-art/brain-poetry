from __future__ import print_function
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

DEFAULT_PORT = 5556




## POETRY GENERATION ##########################################################

def get_generator(language):
    if language == 'finnish':
        try:
            from generate_poem import generate as get_poem_fi
        except ImportError:
            log_msg('Finnish poem generation import error, using placeholder function...')
            get_poem_fi = lambda category: 'Poem {} {}'.format('finnish', category)
        return get_poem_fi
    elif language == 'english':
        try:
            from generate_poem_eng import generate as get_poem_en
        except ImportError:
            log_msg('English poem generation import error, using placeholder function...')
            get_poem_en = lambda category: 'Poem {} {}'.format('english', category)
        return get_poem_en
    elif language == 'german':
        try:
            from german_poetry_generation.german_poem import generate_german_poem as get_poem_de
        except ImportError:
            log_msg('German poem generation import error, using placeholder function...')
            get_poem_de = lambda category: 'Poem {} {}'.format('german', category)
        return get_poem_de
    else:
        log_msg('{} poem generation import error, using placeholder function...'.format(language.capitalize()))
        get_poem_lang = lambda category: 'Poem {} {}'.format(language.capitalize(), category)
        return get_poem_lang

def get_categories(language):
    if language == 'finnish':
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # FIXME
    elif language == 'english':
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # FIXME
    elif language == 'german':
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # FIXME
    else:
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # FIXME


class PoemGenerator(object):
    languages = ['finnish', 'english', 'german']
    # Poetry generators
    def __init__(self):
        self.generators = {lang:get_generator(lang) for lang in self.languages}
        self.categories = {lang:get_categories(lang) for lang in self.languages}
        self.poemgen_q = Queue() # FIXME: rename
    

    def generate_poem(self, language, category):
        poem = self.generators[language](category) # get_poem_fi etc. 
        self.poemgen_q.put((category, poem))


## API ########################################################################

class PoemServer(object):
    API_VERSION = '0.1'
    API_DATE    = '2015-08-12'

    def __init__(self, socket):
        self.poem_generator = PoemGenerator()
        self.socket = socket

    # Create response dictionary
    def create_response(self, response_type, message, originating_request):
        response = {}
        response['type']    = response_type
        response['message'] = message
        response['request'] = originating_request
        return response

    # Send error response
    def send_error(self, originating_request):
        error = self.create_response('error', 'Bad request', originating_request)
        log_msg('Sending error message: {}'.format(error))
        self.socket.send_json(error)

    # Send acknowledge response
    def send_ack(self, originating_request):
        ack = self.create_response('acknowledge', 'Request acknowledged', originating_request)
        log_msg('Sending acknowledge: {}'.format(ack))
        self.socket.send_json(ack)

    # Send poem response
    def send_poem(self, originating_request, poem_text, category):
        poem = self.create_response('poem', 'Poem generated', originating_request)
        poem['poem']     = poem_text
        poem['category'] = category
        log_msg('Sending poem: {}'.format(poem))
        self.socket.send_json(poem)

    # Send API response
    def send_api(self, originating_request):
        api = self.create_response('api_info', 'API information', originating_request)
        api['available_commands']   = ['generate_poem', 'get_api', 'get_poem', 'help']
        api['available_languages']  = list(self.poem_generator.generators.keys())
        api['available_categories'] = self.poem_generator.categories
        api['api_version']          = self.API_VERSION
        api['api_date']             = self.API_DATE
        log_msg('Sending API: {}'.format(api))
        self.socket.send_json(api)

    # Check request validity
    def check_request(self, request):
        good = True
        try:
            if request == {} or request['command'] in ['get_api', 'get_poem', 'help']:
                pass
            elif request['command'] == 'generate_poem':       
                if request['language'] not in self.poem_generator.languages or \
                   request['category'] not in self.poem_generator.categories[request['language']]:
                    good = False
            else:
                good = False
        except KeyError:
            good = False
        return good 

    def process(self, request):
        if self.check_request(request): # Good request?
            if request == {} or request['command'] in ['get_api', 'help']:
                self.send_api(request)
            elif request['command'] == 'generate_poem': 
                log_msg('Starting to generate poem in {} category {}'.format(request['language'], 
                                                                             request['category']))
                poemgen_thr = Thread(target=self.poem_generator.generate_poem, 
                                     args=[request['language'], 
                                           request['category']])
                poemgen_thr.start()
                self.send_ack(request)
            # FIXME: Should we send an error if a get request comes without
            #        a generate request?
            elif request['command'] == 'get_poem': 
                category, poem = None, None
                try:
                    category, poem = self.poem_generator.poemgen_q.get_nowait()
                    log_msg('Poem generated!')
                except Empty:
                    pass
                
                if category is not None and poem is not None:
                    self.send_poem(request, poem, category)
                else:
                    self.send_ack(request)               
        else:
            self.send_error(request)



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
    poem_server = PoemServer(socket)
    
    # Main loop
    while running:
        # Get request
        try:
            request = socket.recv_json(zmq.NOBLOCK)
        except zmq.ZMQError as e: 
            request = None
        if request is not None:
            log_msg('Received request: {}'.format(request))
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
    parser.add_argument('--port', default=DEFAULT_PORT, type=int, help='Server port')

    args = parser.parse_args()

    if args.test:
        print('Testing...')
        import os
        print(os.path.realpath(__file__))
    else:
        server(args.port)
