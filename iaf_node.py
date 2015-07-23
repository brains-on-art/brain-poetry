#!/usr/bin/env python3

import sys
import numpy as np
import scipy.signal
import matplotlib.mlab as mlab
from midas.node import BaseNode
from midas import utilities as mu


# ------------------------------------------------------------------------------
# Create an Individual Alpha Peak (IAF) Node basedn the Base Node
# ------------------------------------------------------------------------------
class IAFNode(BaseNode):

    """ IAF MIDAS node """

    def __init__(self, *args):
        """ Initialize example node. """
        super().__init__(*args)
        self.metric_functions.append(self.metric_iaf)

    def metric_iaf(self, x):
        """ Returns the IAF vector calculated from the input data x """
        data = np.asarray(x['data'])
        iaf = [10.0] * data.shape[0]
        for ch, ch_data in enumerate(data):
            pxx, freqs = mlab.psd(ch_data, Fs=128.0, NFFT=256)
            alpha_mask = np.abs(freqs - 10) <= 2.0
            alpha_pxx = 10*np.log10(pxx[alpha_mask])
            alpha_pxx = scipy.signal.detrend(alpha_pxx)
            # iaf[ch] = alpha_pxx.shape
            iaf[ch] = freqs[alpha_mask][np.argmax(alpha_pxx)]
        return iaf


# ------------------------------------------------------------------------------
# Run the node if started from the command line
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    node = mu.midas_parse_config(IAFNode, sys.argv)
    if node is not None:
        node.start()
        node.show_ui()
# ------------------------------------------------------------------------------
# EOF
# ------------------------------------------------------------------------------
