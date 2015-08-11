#!/usr/bin/env python3
import signal
import subprocess
#from lsltools import vis

# STEP 1: Start the EPOC simulator
eeg_log = open('simulate_eeg.log', 'w')
eeg = subprocess.Popen(['python3','/home/boa/brains-on-art/brain-poetry/simulate_eeg.py'], stdout=eeg_log)

# STEP 2: Find the stream started in step 1 and pass it to the vis.Grapher
visu = subprocess.call(['python', '/home/boa/brains-on-art/brain-poetry/epoc_grapher.py'])
#streams = vis.pylsl.resolve_byprop("name","EPOC")
#eeg_graph = vis.Grapher(streams[0],512*5,'y')

# STEP 3: Enjoy the graph!
eeg.send_signal(signal.SIGINT)
eeg_log.close()
