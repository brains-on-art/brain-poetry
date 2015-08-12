#!/usr/bin/python
# -*- coding: utf-8  -*-

import json
import os  
import time
import shelve
import sys
import socket
import threading
try:
    from queue import Queue, Empty
except ImportError: # Python2
    from Queue import Queue, Empty
from poem_printer import print_poem, parse_poem


# Logging helpers FIXME: move to utility library
file_time_str = lambda: time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime())
time_str = lambda: time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
log_msg = lambda msg: print('{}: {}'.format(time_str(), msg))

# Defaults
POEM_SERVER_PORT = 5556
save_directory = os.path.realpath('~/brain_poetry_data/')


class UIClient(object):
    SENDADDR = ('localhost', 4333)
    RECVADDR = ('localhost', 4332)

    def __init__(self):
        self.stop_flag = thread.Event()
        self.receive_thread = threading.Thread(target=wait_for_msg, args=(self.stop_flag,))
        self.receive_thread.start()
        self.receive_q = Queue()

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def close(self):
        self.stop_flag.set()

    def send_poem(self, poem_dict):
        viz_poem = parse_poem(poem)
        send_socket.sendto(('p'+viz_poem).encode('utf-8'), SENDADDR)

    def receive_messages(self, stop_flag):
        log_msg('Starting to listen for messages from UI')
        # Initialize socket for receiving from UI
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receive_socket.bind(self.RECVADDR)
        receive_socket.settimeout(0.1)

        while True:
            if stop_flag.is_set():
                log_msg('Stopping UI listen')
                break
            
            #print('READING BUFFER')
            #read the buffer
            try:
                packet = receive_socket.recvfrom(1024)
            except socket.timeout:
                continue
            except socket.error:
                log_msg('UI receiving socket error!')
                break
            else:
                log_msg('Got packet from UI: {}'.format(packet))
                msg = packet[0]
                if 'start' in msg:
                    lang = msg.split()[1]
                    language = 'finnish' if lang == '0' else 'english' # FIXME
                    message = {}
                    message['msg'] = msg
                    message['type'] = 'start'
                    message['language'] = language
                    receive_q.put(message)
                elif msg[0] == 'n':
                    message = {}
                    message['msg'] = msg
                    message['type'] = 'name'
                    message['name'] = msg[1:].decode('utf-8')
                    receive_q.put(message)
                elif msg == 'done':
                    message = {}
                    message['msg'] = msg
                    message['type'] = 'done'
                    receive_q.put(message)
                elif msg == 'print':
                    message = {}
                    message['msg'] = msg
                    message['type'] = 'print'
                    receive_q.put(message)

    

def main():
    import subprocess  # FIXME: move me
    
    script_directory = os.path.dirname(os.path.realpath(__file__))
    current_time     = file_time_str()
    poem_server_path = os.path.join(script_directory, 'poem_server.py')

    # Start poem server
    log_msg('Starting poem server subprocess on port {}...'.format(POEM_SERVER_PORT))
    poem_server_log = open(current_time + '_poem_server.log', 'w')
    log_msg('  Logging poem server messages to {}'.format(poem_server_log.name))
    poem_server = subprocess.Popen(['python3', poem_server_path, '--port', str(POEM_SERVER_PORT)],
                                   stdout=poem_server_log, 
                                   stderr=subprocess.STDOUT)


    # Start EPOC LSL streaming
    log_msg('Starting EPOC LSL streaming...')
    epoc_streamer_path = os.path.join(script_directory, 'epoc_streamer.py')
    epoc_streamer_log = open(current_time + '_epoc_streamer.log', 'w')
    log_msg('  Logging EPOC streamer messages to {}'.format(epoc_streamer_log.name))
    epoc_streamer = subprocess.Popen(['python3', epoc_streamer_path], 
                                     stdout=epoc_streamer_log,
                                     stderr=subprocess.STDOUT)

    # Start MIDAS servers
    node_config_path = os.path.join(script_directory, 'node_config.ini')
    log_msg('Starting MIDAS node(s) and dispatcher...')
    iaf_node_path = os.path.join(script_directory, 'iaf_node.py')
    iaf_node_log = open(current_time + '_iaf_node.log', 'w')
    log_msg('  Logging IAF MIDAS node messages to {}'.format(iaf_node_log.name))
    iaf_node = subprocess.Popen(['python3', iaf_node_path, node_config_path], 
                                stdout=iaf_node_log,
                                stderr=subprocess.STDOUT)
    dispatcher_path = os.path.join(script_directory, 'dispatcher.py')
    dispatcher_log = open(current_time + '_dispatcher.log', 'w')
    log_msg('  Logging MIDAS dispatcher messages to {}'.format(dispatcher_log.name))
    dispatcher = subprocess.Popen(['python3', dispatcher_path, node_config_path], 
                                  stdout=dispatcher_log,
                                  stderr=subprocess.STDOUT)

    # Start Processing UI
    log_msg('Starting Processing UI (fi/eng)')
    ui_path = os.path.join(script_directory, 'dispatcher.py')
    #processing-java --sketch=/home/boa/sketchbook/runo_viz_biling --output=/home/boa/runo_viz_biling_build/ --force --present
    ui_log = open(current_time + '_processing_ui.log', 'w')
    log_msg('  Logging Processing UI messages to {}'.format(ui_log.name))
    ui = subprocess.Popen(['processing-java', 
                           '--sketch=/home/boa/sketchbook/runo_viz_biling',
                           '--output=/home/boa/runo_viz_biling_build/',
                           '--force',
                           '--present'],
                          stdout=ui_log, 
                          stderr=subprocess.STDOUT)

    # Initialize connection with visualization
    ui = UIClient()

    # EPOC stream
    log_msg('Getting handle on EPOC stream')
    epoc_stream = rec.pylsl.resolve_byprop("name", 'EPOC')[0]

    # Recorder
    stream_recorder = None

    # Main loop
    state = 'idle'
    username = None
    language = 'finnish'
    start_time = None
    stop_time = None
    save_file = None
    save = None
    while True:
        gevent.sleep(0.008)   
          
        # See if we have messages from Processing, decipher them and set state accordingly
        try:
            msg = ui.receive_q.get_nowait()
        except Empty:
            pass
        else:
            if msg['type'] == 'start':
                log_msg('Processing start message: {}'.format(msg))
                language = msg['language']
                start_time = time.time()

                tmp = file_time_str()
                save_file = open(os.path.join(save_directory, tmp + '_metadata.json'), 'w')
                save = {}
                save['time_str'] = tmp                
                stream_recorder = rec.StreamRecorder(os.path.join(save_directory, tmp + '_eeg.xcf'), epoc_stream)
                stream_recorder.start_recording()

                state = 'collect'
                log_msg('Switched to state: {}'.format(state))
            elif msg['type'] == 'name':
                log_msg('Processing name message: {}'.format(msg))
                username = msg['name']
            elif msg['type'] == 'print':
                log_msg('Processing print message: {}'.format(msg))
                print_thr = threading.Thread(target=print_poem, args=(poem,username,))
                print_thr.daemon = True
                print_thr.start()
            elif msg['type'] == 'done':
                save['start_time'] = start_time
                save['stop_time'] = stop_time
                save['username'] = username
                save['language'] = language
                save['poem'] = poem
                save['eeg_data_file'] = stream_recorder.f.name
                json.dumps(save, save_file)
                save = None

                save_file.close()
                stream_recorder.end_recording()
                save_file = None
                stream_recorder = None

                username = None
                language = 'finnish'
                poem = None
                start_time = None
                stop_time = None
                stream_recorder = None
                state = 'idle'
                log_msg('Switched to state: {}'.format(state))


        # Main state machine
        if state == 'idle': #waiting for a new customer
            continue

        elif state == 'collect':
            stop_time = time.time()
            if stop_time - start_time > 5: # Collection time in seconds
                log_msg('Collected sufficient data')
                GET_IAF # FIXME
                poem_client.generate_poem(language, IAF) # FIXME
                state = 'generate' 
                log_msg('Switched to state: {}'.format(state))

        elif state == 'generate':
            if poem is None:
                tmp = poem_client.get_poem()
                if rep['type'] == 'poem':
                    poem = rep
            
            if poem is not None and username is not None:
                log_msg('Sending poem to visualization')
                ui.send_poem(poem)
                state = 'done'
                log_msg('Switched to state: {}'.format(state))
           
        elif state == 'done':
            continue

    # Shut down everything...
    poem_server.send_signal(signal.SIGTERM)
    epoc_streamer.send_signal(signal.SIGTERM)
    iaf_node.send_signal(signal.SIGTERM)
    dispatcher.send_signal(signal.SIGTERM)
    ui.send_signal(signal.SIGTERM)
    


if __name__=="__main__":
    main() 
    