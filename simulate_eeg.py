#!/usr/bin/env python3

# A simulated EEG streamer for testing and debugging purposes
# Brains on Art - 2015
#
# For license information see LICENSE.md

from lsltools.sim import EEGData


def main():
    print("Starting EEG stream...")
    eeg = EEGData(stream_name="EPOC", nch=14, srate=128)
    eeg.start()
    input("Press ENTER to stop streaming!")
    eeg.stop()

if __name__ == "__main__":
    main()
