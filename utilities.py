import re
from scipy import signal
from numpy import fromfile
import os


def _convert(text):
    if text.isdigit():
        return int(text)
    return text


def natural_sorting(key):
    return [_convert(c) for c in re.split('([0-9]+)', key)]


def read_dat(filename):
    fid = open(filename, 'r')
    filesize = os.path.getsize(filename)  # in bytes
    num_samples = filesize // 2  # int16 = 2 bytes
    v = fromfile(fid, 'int16', num_samples)
    fid.close()

    v = v * 0.195  # convert to microvolts
    return v


def apply_bandpass(data, f_sampling, f_low, f_high, ellip_order):
    wl = f_low / (f_sampling / 2.)
    wh = f_high / (f_sampling / 2.)
    wn = [wl, wh]

    # Designs a ellip_order-order Elliptic band-pass filter which passes
    # frequencies between 0.03 and 0.6, and with 0.1 dB of ripple in the
    # passband, and 40 dB of attenuation in the stopband.
    b, a = signal.ellip(ellip_order, 0.1, 40, wn, 'bandpass', analog=False)
    # To match Matlab output, we change default padlen from
    # 3*(max(len(a), len(b))) to 3*(max(len(a), len(b)) - 1)
    return signal.filtfilt(b, a, data, padlen=3 * (max(len(a), len(b)) - 1))
