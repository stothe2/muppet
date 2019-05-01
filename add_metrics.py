import argparse
import os
import json
from numpy import arange, ndarray, where, mean, array, argmax, argmin, var, sqrt, divide, logical_and
from numpy.random import binomial
import xarray as xr
from sklearn.model_selection import ShuffleSplit
from scipy.stats import spearmanr, ttest_1samp


def _splithalf_r(data, num_simulation):
    r_values = []
    # Split randomly shuffled data into two equal sized sets over 'trial' dimension.
    random_state = 12883823
    ss = ShuffleSplit(n_splits=num_simulation, test_size=0.5, random_state=random_state)
    # Compute Spearman-Brown corrected correlation between the two sets.
    for train_index, text_index in ss.split(data):
        train = array([data[_] for _ in train_index])
        test = array([data[_] for _ in text_index])
        # Compute Spearman correlation.
        r = spearmanr(train.mean(axis=0), test.mean(axis=0)).correlation
        # Apply Spearman-Brown correction.
        r_corrected = 2 * r / (1 + r)
        r_values.append(r_corrected)
    return mean(r_values)


def iro_reliability(psth_xr):
    num_simulation = 50
    reliability_per_channel = []
    for ch_name, ch_xr in psth_xr.groupby('channel'):
        # Compute Spearman-Brown corrected split-half correlation of image rank-order averaged over
        # 'num_simulation' runs.
        reliability_per_channel.append(_splithalf_r(ch_xr.data.T, num_simulation))
    return array(reliability_per_channel) > 0.6


def _selectivity(data, num_simulation):
    s_values = []
    # Split randomly shuffled data into two equal sized sets over 'trial' dimension.
    random_state = 12883823
    ss = ShuffleSplit(n_splits=num_simulation, test_size=0.5, random_state=random_state)
    for train_index, text_index in ss.split(data):
        train = array([data[_] for _ in train_index])
        test = array([data[_] for _ in text_index])

        # Compute indexes of 'best' and 'worst' stimulus (based on mean spike count rate
        # cross trials) on train set.
        best_idx = argmax(mean(train, axis=0))
        worst_idx = argmin(mean(train, axis=0))

        # Test on test set.
        means = mean(test, axis=0)
        variances = var(test, axis=0)
        s_values.append((means[best_idx] - means[worst_idx]) / sqrt(0.5 * (variances[best_idx] + variances[worst_idx])))
    return mean(s_values)


def selectivity(psth_xr):
    num_simulation = 50
    selectivity_per_channel = []
    for ch_name, ch_xr in psth_xr.groupby('channel'):
        selectivity_per_channel.append(_selectivity(ch_xr.data.T, num_simulation))
    return array(selectivity_per_channel) > 1


# def _visual_drive(data, grey_data):
#     # Mean across trials, then images.
#     mean_response_stim = mean(mean(data, axis=0))
#     mean_response_grey = mean(mean(grey_data, axis=0))
#     # Variance across trials, then mean across images.
#     var_stim = mean(var(data, axis=0))
#     var_grey = mean(var(data, axis=0))
#     return (mean_response_stim - mean_response_grey) / sqrt(0.5 * (var_stim + var_grey))
#
#
# def _flip():
#     """Returns 1 or -1 with equal probability."""
#     return 1 if binomial(1, 0.5) == 1 else -1
#
#
# def perm_test(x, stat='mean'):
#     """Performs a one-sample permutation test.
#
#     Permutations are produced by multiplying observations by +1 or -1, so
#     the total number of permutations possible is 2^n for a sample of size n.
#     """
#     assert stat is 'mean'
#     num_permutations = 10
#     # If number of permutations exceeds 2^(n-1), then it will be ignored
#     # since an exact test will be performed.
#     if num_permutations >= 2 ** (len(x) - 1):
#         num_permutations = 2 ** (len(x) - 1)
#     # Calculate mean of observed data.
#     mu = mean(x)
#     # Calculate mean for all possible permutations of data, and subtract from this
#     # the mean of the observed data.
#     mu_differences = []
#     for _ in range(num_permutations):
#         permuted_x = [_flip() * _ for _ in x]
#         mu_differences.append(mean(permuted_x) - mu)
#     # Take mean of differences in mean of permuted and observed data, which will serve
#     # as our approximation of the p-value.
#     return mean(mu_differences)


def _visual_drive(data, grey_data):
    # We compute d-prime values. Note that for the main stimuli (data), we only take mean
    # across trials and not images. This is because we want to do a one-sample t-test later.
    dprime_values = divide(mean(data, axis=0) - mean(mean(grey_data, axis=0)),
                           sqrt(0.5 * (var(data, axis=0) + mean(var(grey_data, axis=0)))))

    # Do a t-test (null hypothesis is m = 0, that is the difference in means is not significant).
    return ttest_1samp(dprime_values, 0).pvalue


def visual_drive(psth_xr, grey_psth_xr):
    drive_per_channel = []
    for (ch_name, ch_xr), (_, grey_ch_xr) in zip(psth_xr.groupby('channel'), grey_psth_xr.groupby('channel')):
        drive_per_channel.append(_visual_drive(ch_xr.data.T, grey_psth_xr.data.T))
    return array(drive_per_channel) < 0.05


def main(data, path, filename):
    bin_size = 10
    start_time = 70
    stop_time = 170

    timebins = arange(start_time, stop_time, bin_size)

    # peristim = ndarray(shape=(data['n_channels'], len(data['item']['id']), len(timebins)), dtype=float, order='F')
    # for i, channel in enumerate(data['spikes']):
    #     for ii, item in enumerate(data['spikes'][channel]):
    #         spike_density_over_trials = []
    #         for trial, spike_times in data['spikes'][channel][item].items():
    #             spike_density = []
    #             for bin in timebins:
    #                 spike_density.append(where((spike_times >= bin) & (spike_times <= round(bin + tb, 2)))[0].size)
    #             spike_density_over_trials.append(spike_density)
    #         peristim[i][ii] = mean(spike_density_over_trials, axis=0)
    #
    # print(peristim)
    #
    # neuroid_ids = [value for key, value in data['neuroid']['neuroid_id'].items()]
    # items = [str(value) for key, value in data['item']['id'].items()]
    #
    # peristim_xr = xr.DataArray(peristim, coords=[neuroid_ids, items, timebins], dims=['neuroid', 'item', 'bin'])
    # print(peristim_xr.sel(neuroid='A-000', item='1'))

    psth = ndarray(shape=(len(data['item']['id']), data['n_trials'], len(timebins), data['n_channels']),
                   dtype=float, order='F')

    for i, channel in enumerate(data['spikes']):
        for ii, stimulus in enumerate(data['spikes'][channel]):
            for iii, spiketrain in enumerate(data['spikes'][channel][stimulus].values()):
                spiketrain = [_ * 1000 for _ in spiketrain]
                counts = []
                for _ in timebins:
                    counts.append(where((spiketrain >= _) & (spiketrain <= (_ + bin_size)))[0].size)
                psth[ii, iii, :, i] = counts

    stimulus_labels = [str(_) for _ in list(data['item']['id'].values())]
    trial_labels = [str(_) for _ in list(range(1, data['n_trials'] + 1))]
    time_labels = [str(_) + '-' + str(_ + bin_size) for _ in timebins]
    ch_names = list(data['neuroid']['neuroid_id'].values())
    psth_xr = xr.DataArray(psth, coords=[stimulus_labels, trial_labels, time_labels, ch_names],
                           dims=['stimulus', 'trial', 'timebin', 'channel'])

    print('Shape is', psth_xr.shape)

    # We take average of response across the 'timebin' dimension (70-170ms).
    psth_xr = psth_xr.mean('timebin')

    print('Shape is', psth_xr.shape)

    # For computing the visual drive, we require neural responses to grey image.
    # We thus first construct a psth for the baseline stimuli.
    baseline_psth = ndarray(shape=(data['baseline']['n_grey']+data['baseline']['n_other'],
                                      data['n_trials'], len(timebins), data['n_channels']),
                               dtype=float, order='F')

    for i, channel in enumerate(data['baseline']['spikes']):
        for ii, stimulus in enumerate(data['baseline']['spikes'][channel]):
            for iii, spiketrain in enumerate(data['baseline']['spikes'][channel][stimulus].values()):
                spiketrain = [_ * 1000 for _ in spiketrain]
                counts = []
                for _ in timebins:
                    counts.append(where((spiketrain >= _) & (spiketrain <= (_ + bin_size)))[0].size)
                baseline_psth[ii, iii, :, i] = counts

    baseline_labels = [str(_) for _ in list(data['baseline']['spikes'][ch_names[0]].keys())]
    # baseline_labels = [str(_) for _ in list(range(data['baseline']['n_grey']+data['baseline']['n_other']))]
    baseline_psth_xr = xr.DataArray(baseline_psth, coords=[baseline_labels, trial_labels, time_labels, ch_names],
                                    dims=['stimulus', 'trial', 'timebin', 'channel'])

    print('Baseline shape is', baseline_psth_xr.shape)

    # We take average of response across the 'timebin' dimension 70-170ms.
    baseline_psth_xr = baseline_psth_xr.mean('timebin')

    print('Baseline shape is', baseline_psth_xr.shape)

    # Compute the metrics.
    reliability_per_channel = iro_reliability(psth_xr)
    selectivity_per_channel = selectivity(psth_xr)
    drive_per_channel = visual_drive(psth_xr, baseline_psth_xr.isel(stimulus=list(range(data['baseline']['n_grey']))))

    values_per_channel = logical_and(logical_and(reliability_per_channel, selectivity_per_channel), drive_per_channel)
    assert len(ch_names) == len(values_per_channel)
    passed_metrics = {}
    for _, value in zip(ch_names, values_per_channel):
        passed_metrics[_] = int(value)

    # Add metrics values to the original data file and save (locally for now).
    data['passed_metrics'] = passed_metrics
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)  # TODO: Decide on where to save the file.

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-unit activity analysis tools.')
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
    assert 'neuroid_id' in data['neuroid']
    assert 'item' in data
    assert 'id' in data['item']
    assert 'baseline' in data
    assert 'n_grey' in data['baseline']

    # Extract the directory where we'll be saving the data, and the name of the file.
    path = args.data[:args.data.rfind('/')]
    assert os.path.isdir(path)  # TODO: Unnecessary?
    filename = args.data[args.data.rfind('/')+1:args.data.find('_data')]

    main(data, path, filename)
