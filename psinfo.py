import argparse
import os
import json
from numpy import arange, ndarray, where, mean
import xarray as xr


def main(data, start, stop, tb, path, filename):
    tb = round(tb, 2)
    timebins = arange(start, stop, tb)
    timebins = [round(_, 2) for _ in timebins]

    peristim = ndarray(shape=(data['n_channels'], len(data['item']['id']), len(timebins)), dtype=float, order='F')

    for i, channel in enumerate(data['spikes']):
        for ii, item in enumerate(data['spikes'][channel]):
            spike_density_over_trials = []
            for trial, spike_times in data['spikes'][channel][item].items():
                spike_density = []
                for bin in timebins:
                    spike_density.append(where((spike_times >= bin) & (spike_times <= round(bin + tb, 2)))[0].size)
                spike_density_over_trials.append(spike_density)
            peristim[i][ii] = mean(spike_density_over_trials, axis=0)

    print(peristim)

    neuroid_ids = [value for key, value in data['neuroid']['neuroid_id'].items()]
    items = [str(value) for key, value in data['item']['id'].items()]

    peristim_xr = xr.DataArray(peristim, coords=[neuroid_ids, items, timebins], dims=['neuroid', 'item', 'bin'])
    print(peristim_xr.sel(neuroid='A-000', item='1'))

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-unit activity analysis tools.')
    # TODO: Use ms to get around floating point issues
    parser.add_argument('start', metavar='N', type=float, help='start time (in sec) for peristimulus computation')
    parser.add_argument('stop', metavar='N', type=float, help='stop time (in sec) for peristimulus computation')
    parser.add_argument('tb', metavar='N', type=float, help='bin width (in sec) for peristimulus computation')
    parser.add_argument('--data', type=str, help='full path and name of the .json file '
                                                 'containing spike times and experiment metadata')
    args = parser.parse_args()

    assert args.data is not None
    assert os.path.isfile(args.data)

    # Load data file.
    with open(args.data) as f:
        data = json.load(f)

    # Check if necessary fields are present.
    assert 'start_time' in data
    assert 'stop_time' in data
    assert 'spikes' in data
    assert 'n_channels' in data
    assert 'n_trials' in data
    assert 'neuroid' in data

    # Check if peristim start and stop time are within the range in which spike times have been computed.
    # TODO: Fix this
    if args.start < 0:
        assert args.start <= data['start_time']
    else:
        assert args.start < data['stop_time']
    assert args.stop < data['stop_time']

    # Extract the directory where we'll be saving the data, and the name of the file.
    path = args.data[:args.data.rfind('/')]
    assert os.path.isdir(path)  # TODO: Unnecessary?
    filename = args.data[args.data.rfind('/')+1:args.data.find('_data')]

    main(data, args.start, args.stop, args.tb, path, filename)
