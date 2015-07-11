from emokit.emotiv import Emotiv
import gevent
from midas.node import lsl


def start_epoc_stream(stream_name, id=None):
    """ Main loop for EPOC-LabView interface. """

    # Init EPOC
    emotiv = Emotiv(displayOutput=False)
    gevent.spawn(emotiv.setup)
    gevent.sleep(1)
    old_counter = 0
    channel_list = ['AF3', 'AF4', 'ETC']

    # Create LSL outlet
    info = lsl.StreamInfo(stream_name, 'EEG', 14, 128)
    outlet = lsl.StreamOutlet(info)

    # Main-loop
    while True:
        pckg = emotiv.dequeue()
        sample = []
        if pckg.counter != old_counter:
            for ch in channel_list:
                sample.append(pckg.__getattribute__(ch))[0]

            outlet.push_sample(sample)
            old_counter = pckg.counter
        gevent.sleep(0)


if __name__ == "__main__":
    try:
        start_epoc_stream('alpha')
    except Exception, e:
        print e
