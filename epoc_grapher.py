from lsltools import vis
import sys


def main(stream_name):
    streams = vis.pylsl.resolve_byprop("name", stream_name)
    eeg_graph = vis.Grapher(streams[0], 128 * 5, 'y')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        streams = vis.pylsl.resolve_streams()

        print('Visible streams:')
        for stream in streams:
            print(stream.name())
    elif len(sys.argv) == 2:
        main(sys.argv[1])
