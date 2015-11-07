#!/usr/bin/env python3

import os
import queue
import time
from Crypto.Cipher import AES
import numpy as np
import gevent
import pyudev
from midas.node import lsl
import socket

EEG_SAMPLING_RATE = 128
NUM_EEG_CHANNELS  = 14

sensor_bits = [[ 10,  11,  12,  13,  14,  15,   0,   1,   2,   3,   4,   5,   6,   7], # F3
               [ 28,  29,  30,  31,  16,  17,  18,  19,  20,  21,  22,  23,   8,   9], # FC5
               [ 46,  47,  32,  33,  34,  35,  36,  37,  38,  39,  24,  25,  26,  27], # AF3
               [ 48,  49,  50,  51,  52,  53,  54,  55,  40,  41,  42,  43,  44,  45], # F7
               [ 66,  67,  68,  69,  70,  71,  56,  57,  58,  59,  60,  61,  62,  63], # T7
               [ 84,  85,  86,  87,  72,  73,  74,  75,  76,  77,  78,  79,  64,  65], # P7
               [102, 103,  88,  89,  90,  91,  92,  93,  94,  95,  80,  81,  82,  83], # O1
               [140, 141, 142, 143, 128, 129, 130, 131, 132, 133, 134, 135, 120, 121], # O2
               [158, 159, 144, 145, 146, 147, 148, 149, 150, 151, 136, 137, 138, 139], # P8
               [160, 161, 162, 163, 164, 165, 166, 167, 152, 153, 154, 155, 156, 157], # T8
               [178, 179, 180, 181, 182, 183, 168, 169, 170, 171, 172, 173, 174, 175], # F8
               [196, 197, 198, 199, 184, 185, 186, 187, 188, 189, 190, 191, 176, 177], # AF4
               [214, 215, 200, 201, 202, 203, 204, 205, 206, 207, 192, 193, 194, 195], # FC6
               [216, 217, 218, 219, 220, 221, 222, 223, 208, 209, 210, 211, 212, 213]] # F4
quality_bits = [ 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112]

class EPOC:
    def __init__(self, serial_number, name='', developer_headset=False):
        print('Init EPOC')
        #self.hidraw = hidraw
        self.serial_number = serial_number

        if name == '':
            self.name = serial_number
        else:
            self.name = name

        # Open device
        #self.hidraw = os.open(device_node, os.O_RDONLY|os.O_NONBLOCK)

        # Setup AES cipher
        sn = serial_number
        if developer_headset:
            key = ''.join([sn[-1], '\0',   sn[-2], 'H', sn[-1], '\0',   sn[-2], 'T',
                           sn[-3], '\x10', sn[-4], 'B', sn[-3], '\0',   sn[-4], 'P'])
        else:
            key = ''.join([sn[-1], '\0',   sn[-2], 'T', sn[-3], '\x10', sn[-4], 'B',
                           sn[-1], '\0',   sn[-2], 'H', sn[-3], '\0',   sn[-4], 'P'])
        self.cipher = AES.new(key, AES.MODE_ECB)

        # Define filter kernel
        #self.filter_numtaps = 64
        #self.filter_kernel = scipy.signal.firwin(self.filter_numtaps, [3.5,40.0], nyq=EEG_SAMPLING_RATE/2.0, pass_zero=False)

        # Ring buffers for data
        #self.minimum_sample_window = minimum_time_window*EEG_SAMPLING_RATE
        #self.data    = np.ones(NUM_EEG_CHANNELS+2)
        #self.counter = self.data[0,:]
        #self.eeg     = self.data[1:-2,:]
        #self.raw_eeg = np.ones_like(self.eeg)
        #self.gyro    = self.data[-2:,:]
        #self.battery = np.zeros(5*60) # FIXME
        #self.quality = 0 # FIXME
        #self.data_index    = self.minimum_sample_window # Current index in data buffer
        #self.battery_index = 0 # Current index in battery buffer
        #self.quality_index = 0 # Current index in quality buffer
        self.worker = None

        self.status = 'DISCONNECTED'
        self.last_packet_time = time.time()

        #self.status_callbacks = {}
        #self.status_callbacks['DISCONNECTED'] = []
        #self.status_callbacks['NO DATA'] = []
        #self.update_callbacks = []
        self.s = None
        while not self.s:
            try:
                print('Getting socket')
                #create UDP socket for sending data
                self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception as e:
                continue
                print(e)
            print('Receiving socket found. Proceeding to meaty part of mainloop')
        self.SENDADDR = ('localhost', 4333)

    def connect(self, hidraw, outlet):
        self.hidraw_path = hidraw
        self.outlet = outlet
        self.start()

    def disconnect(self):
        self.stop()
        self.hidraw_path = None
        self.status = 'DISCONNECTED'
        #for f in self.status_callbacks['DISCONNECTED']:
        #    f()

    def start(self):
        print('Starting up')
        self.hidraw = os.open(self.hidraw_path, os.O_RDONLY|os.O_NONBLOCK)
        self.worker = gevent.spawn(self.run)

    def stop(self):
        print('Stopping')
        gevent.kill(self.worker)
        os.close(self.hidraw)

    #def register_status_callback(self, status, callback):
    #    self.status_callbacks[status].append(callback)

    #def register_update_callback(self, callback):
    #    self.update_callbacks.append(callback)

    def run(self):
        print('Starting run')

        #data    = np.ones(NUM_EEG_CHANNELS+2, dtype=np.float32)
        #self.counter = self.data[0,:]
        eeg     = np.zeros(NUM_EEG_CHANNELS)
        #self.raw_eeg = np.ones_like(self.eeg)
        gyro    = np.zeros(2)



        sample = np.zeros(NUM_EEG_CHANNELS)
        while True and self.hidraw != None:
            # Get
            try:
                raw_packet = os.read(self.hidraw, 32)
            except OSError:
                # No packets for me! ZZzzZZ...
                t = time.time()
                if (t - self.last_packet_time) > 0.5 and self.status != 'NO DATA':
                    self.status = 'NO DATA'
                    #print self.status
                    #for f in self.status_callbacks['NO DATA']:
                    #    f()
                gevent.sleep(0.008) # 1.0/128.0 = 0.0078125
            else:
                # CHECK FOR A REAL PACKET
                assert(len(raw_packet) == 32)

                #print('Encrypted data: ({}) {}'.format(type(raw_packet), raw_packet))

                # Decrypt
                data = self.cipher.decrypt(raw_packet[:16]) + self.cipher.decrypt(raw_packet[16:])
                #print('Decrypted data: ({}) {}'.format(type(data), data))
                #print('First value: {} {}'.format(data[0], int(data[0])))

                #i = self.data_index
                # Unpack packet counter/battery level (first byte)
                value = data[0]
                if value < 128: # Packet counter
                    counter = value
                    #print('Counter: {}'.format(value))
                #    self.counter[i] = value
                #    if value == 0:
                #        print('1 second of data seen now at i=' + str(i))
                #        #print self.eeg[:,i-5:i]
                else: # Battery
                    #sprint('Battery: {}'.format(value))
                    pass
                #    ind = self.battery_index
                #    value = value - 225
                #    if value < 0:
                #        self.battery[ind] = battery_levels[0]
                #    elif value >= len(battery_levels):
                #        self.battery[ind] = battery_levels[-1]
                #    else:
                #        self.battery[ind] = battery_levels[value]
                #    self.battery_index = ind + 1 if ind < len(self.battery) - 1 else 0

                # Unpack gyros
                gyro[0] = ((data[29] << 4) | (data[31] >> 4))
                gyro[1] = ((data[30] << 4) | (data[31] & 0x0F))
                # TODO zero gyros

                # Unpack sensors
                for ch, bits in enumerate(sensor_bits):
                    level = 0
                    for j in range(13, -1, -1):
                        level <<= 1
                        b, o = (bits[j] // 8) + 1, bits[j] % 8
                        level |= (data[b] >> o) & 1
                    eeg[ch] = level
                #self.eeg[:,i] = (self.raw_eeg[:,i-self.filter_numtaps:i]*self.filter_kernel).sum(axis=1)

                # We received and were able to parse the packet!
                #for f in self.update_callbacks:
                #    f(self.eeg[:,i])
                self.last_packet_time = time.time()
                if self.status != 'OK':
                    self.status = 'OK'
                self.outlet.push_sample(eeg)
                # Send things to processing
                self.s.sendto(bytes('d'+','.join([str(x) for x in eeg[:5]*0.01]), 'UTF-8'),
                              self.SENDADDR)




                #print self.data_index
                #if self.data_index == self.data.shape[-1] - 1:
                #    self.raw_eeg[:,:self.minimum_sample_window] = self.raw_eeg[:,-self.minimum_sample_window:]
                #    self.data_index = self.minimum_sample_window
                #else:
                #    self.data_index += 1
                #self.data_index = i + 1 if i < self.data.shape[-1] - 1 else 64
                #print self.data_index

class EPOCManager:
    def __init__(self, config=None):
        self.devices = {}
        self.epocs = {}
        self.active_epoc = None
        self.names = self.parse_config(config) if config != None else {}

        # Create LSL outlet
        info = lsl.StreamInfo('EPOC', #'EPOC-' + self.name,
                              'EEG',
                              NUM_EEG_CHANNELS,
                              128,
                              'float32',
                              self.serial_number)
        self.outlet = lsl.StreamOutlet(info)

        self.context = pyudev.Context()

        self.populate_devices()
        print('EPOCManager init: {} EPOCs found!'.format(len(self.devices)))

        self.hidraw_event_queue = queue.Queue()
        self.worker = gevent.spawn(self.process_events)

        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by('hidraw')
        self.observer = pyudev.MonitorObserver(self.monitor, self.add_event)
        self.observer.start()

    def parse_config(self, config):
        f = open(config, 'r')
        res = {}
        for line in f:
            if line.strip() == '' or line.strip()[0] == '#':
                continue
            else:
                serial_number, name = line.strip().split()
                res[name] = serial_number
        return res

    def process_hidraw(self, device):
        #device_node = serial_number = None
        device_parent = device.find_parent('usb', 'usb_device')
        #manufacturer  = device_parent.attributes['manufacturer'].decode('utf-8')
        if 'manufacturer' in device_parent.attributes and \
           device_parent.attributes['manufacturer'].decode('utf-8') in ['Emotiv Systems Inc.','Emotiv Systems Pty Ltd']:
            # Each EPOC shows up as two hidraw devices. We select the one with an
            # 'interface' descriptor in the usb_interface parent
            interface_parent = device.find_parent('usb', 'usb_interface')
            if 'interface' in interface_parent.attributes.keys():
                serial_number = device_parent.attributes['serial'].decode('utf-8') # Serial number needed for decrypting packets
                return (device.device_node, serial_number)
        return None

    def populate_devices(self):
        hidraw_devices = [x for x in self.context.list_devices(subsystem='hidraw')]

        for dev in hidraw_devices:
            res = self.process_hidraw(dev)
            if res != None:
                hidraw_path = res[0]; serial_number = res[1]
                self.devices[hidraw_path] = serial_number
                epoc = EPOC(serial_number)
                self.epocs[serial_number] = epoc
                print(serial_number, hidraw_path)
                if self.active_epoc is not None:
                    self.active_epoc.disconnect()
                self.active_epoc = self.epocs[serial_number]
                self.active_epoc.connect(hidraw_path, self.outlet)
                print('Active EPOC is now SN:{}'.format(serial_number))

    def add_event(self, action, device):
        self.hidraw_event_queue.put((action, device))

    def process_events(self):
        while True:
            try:
                action, device = self.hidraw_event_queue.get_nowait()
            except queue.Empty:
                gevent.sleep(0.002)
            else:
                if action == 'add':
                    res = self.process_hidraw(device)
                    if res != None:
                        hidraw_path = res[0]; serial_number = res[1]
                        print('EPOC ({0}) added at {1}'.format(serial_number, hidraw_path))
                        self.devices[hidraw_path] = serial_number
                        if serial_number not in self.epocs:
                            epoc = EPOC(serial_number)
                            self.epocs[serial_number] = epoc
                        # Stop active epoc and make the connected one active
                        if self.active_epoc is not None:
                            self.active_epoc.disconnect()
                        self.active_epoc = self.epocs[serial_number]
                        self.active_epoc.connect(hidraw_path, self.outlet)

                if action == 'remove':
                    hidraw_path = device.device_node
                    if hidraw_path in self.devices:
                        if self.epocs[self.devices[hidraw_path]] is self.active_epoc:
                            self.active_epoc.disconnect()
                            # FIXME: Set other connected EPOC as connected
                        print('EPOC ({0}) at {1} removed'.format(self.devices[hidraw_path], hidraw_path))
                        del self.devices[hidraw_path]

    def get_epoc(self, name):
        # Do we have an epoc by this name
        if name in self.names and self.names[name] in self.epocs:
            return self.epocs[self.names[name]]
        # Perhaps we're being asked directly by serial number
        elif name in self.epocs:
            return self.epocs[name]
        else:
            return None

if __name__ == "__main__":
    manager = EPOCManager()
    #epoc = manager.get_epoc('gamma')

    while True:
        gevent.sleep(1)
