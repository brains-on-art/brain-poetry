from lsltools import vis
import sys


def main(stream_name, buffer_size=512):
    streams = vis.pylsl.resolve_byprop("name", stream_name)
    eeg_graph = vis.Grapher(streams[0], buffer_size, 'y')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        streams = vis.pylsl.resolve_streams()

        print('Visible streams:')
        for stream in streams:
            print(stream.name())
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(sys.argv[1], int(sys.argv[2]))
