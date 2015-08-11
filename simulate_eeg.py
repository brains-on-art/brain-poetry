#!/usr/bin/env python3

# A simulated EEG streamer for testing and debugging purposes
# Brains on Art - 2015
#
# For license information see LICENSE.md
import signal
import time
from lsltools.sim import EEGData

# Refactor to avoid globals
running = True
def signal_handler(signal, frame):
    global running
    print('Stopping')
    running = False


def main():
    signal.signal(signal.SIGINT, signal_handler)

    print('Starting EEG stream...')
    eeg = EEGData(stream_name='EPOC', nch=14, srate=128)
    eeg.start()

    print('Press Ctrl-C to stop streaming')
    while running is True:
        time.sleep(0.3)

    print('Stopping EEG stream...')
    eeg.stop()

if __name__ == "__main__":
    main()
