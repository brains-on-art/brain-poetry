import serial
import textwrap
import time


def parse_poem(raw_poem, linewidth=50, indent='       '):
    # Removes white space and empty lines, splits and indents lines that are too
    # long
    raw_poem = raw_poem.strip().split('\n')
    res = []
    for line in raw_poem:
        if len(line) <= linewidth:
            res.append(line)
        else:
            [res.append(x) for x in textwrap.wrap(line, width=linewidth,
                                                  subsequent_indent=indent)]
    return '\n'.join(res)


def print_poem(raw_poem, username):
    print('Raw poem: {}'.format(raw_poem))
    print('Username: {}'.format(username))
    ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=3.0)
    time.sleep(2.0)

    poem = parse_poem(raw_poem, linewidth=32, indent='  ').split('\n')
    print('Printing: ', poem[0])
    ser.write((u'+k3w+'+poem[0]+u'\n').encode('utf-8'))
    ser.flush()
    response = ser.read(1)
    print('Response: %s' % response)
    for line in poem[1:]:
        # line=line.replace("ü","\x81")
        # line=line.replace("Ü","\x81")
        # line=line.replace("â","\x83")
        # line=line.replace("ê","\x88")
        # line=line.replace("ô","\x93")
        # line=line.replace("ß","\xE1")
        print('Printing: %s' % line)
        ser.write((line+'\n').encode('utf-8'))
        ser.flush()
        response = ser.read(1)
        print('Response: %s' % response)
        # jari modifioi

    print('Printing username %s %s' % (username, type(username)))
    ser.write((u'*n7r*'+username+u'\n').encode('utf-8'))
    ser.flush()
    response = ser.read(1)
    print('Response: %s' % response)

    ser.close()
