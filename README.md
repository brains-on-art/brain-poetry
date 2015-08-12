# Brain Poetry
Brain Poetry by Brains on Art

# Pre-requisites
- Python 2.7 __and__ 3.4
- Numpy (>= 1.8.0)
- Scipy (>= 0.12)
- pyserial (>= 2.6)
- pyzmq (>= 14.0.1)
- pyudev (>= 0.16.1)
- gevent (>= 1.1)
- pycrypto (>= 2.6.1)
- MIDAS (see https://github.com/bwrc/midas)
- lsltools (see https://github.com/bwrc/lsltools/)
- Processing

NOTE: Poetry generation code must be installed separately. Please contact Jukka Toivanen for more info. 

# Install
    git clone https://github.com/brains-on-art/brain-poetry.git
    cd brain-poetry
    cp poem_server.py $POEM_GENERATION_ROOT
$POEM_GENERATION_ROOT is the root folder of the poetry generation code.
  
# Running
  python3 brain_poetry.py
