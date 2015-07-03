#!/usr/bin/env python3

import sys
import time
import numpy as np
from midas.node import BaseNode, lsl
from midas import utilities as mu


# ------------------------------------------------------------------------------
# Create an Individual Alpha Peak (IAF) Node basedn the Base Node
# ------------------------------------------------------------------------------
class IAFNode(BaseNode):
    """ IAF Midas node """

    def __init__(self, *args):
        """ Initialize example node. """
        super().__init__(*args)
        # Specify all metric-functions by adding them to the
        # metric_functions-list. This makes them visible to dispatcher.
        self.metric_functions.append(self.metric_iaf)
        #self.process_list.append(self.process_x)

    # Metric function can be defined as class methods so that they can
    # access the class attributes. This enables some additional functionality.
    def metric_iaf(self, x):
        """ Returns the mean of the input vector calculated from the data. """
        a = 10
        return a

    def _fast_psd(self,data): 
       
        # Computes a fast PSD for the input (1D) data
    
        num_freqs = len(self.frequencies)
    
        # Window the signal and calculate FFT
        windowed_data = self.window_values * data
        fx = np.fft.fft(windowed_data, n=self.NFFT)

        # Calculate power
        psd = (np.conjugate(fx[:num_freqs]) * fx[:num_freqs]).real

        # Scale the spectrum by the norm of the window to compensate for
        # windowing loss; see Bendat & Piersol Sec 11.5.2.
        psd /= self.window_scale

        # Also include scaling factors for one-sided densities and dividing by the
        # sampling frequency, if desired. Scale everything, except the DC component
        # and the NFFT/2 component:
        psd[1:-1] *= 2.0 #self.scaling_factor

        # MATLAB divides by the sampling frequency so that density function
        # has units of dB/Hz and can be integrated by the plotted frequency
        # values. Perform the same scaling here.
        psd /= EEG_SAMPLING_RATE
        
        return psd




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
