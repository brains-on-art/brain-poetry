from lsltools import vis

streams = vis.pylsl.resolve_byprop("name","EPOC")
eeg_graph = vis.Grapher(streams[0],512*5,'y')
