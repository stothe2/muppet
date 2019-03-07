import argparse
import configparser
import os
import json
from utilities import natural_sorting, read_dat, apply_bandpass
from numpy import ceil, arange, nanmean, median, abs, array, concatenate, diff, nonzero


def main(project_dir, date, channel):
    # TODO: Maybe add checks to ensure params.json and config.ini information match?

    # Get names of all directories with the specified 'date'.
    with os.scandir(os.path.join(project_dir, 'intanraw')) as it:
        dirs = [entry.name for entry in it if (entry.is_dir() and entry.name.find(date) is not -1)]
    dirs.sort(key=natural_sorting)

    # Loop through each directory, and detect spikes.
    for d in dirs:
        # Check if the parameters file---where all data is going to be stored---exists.
        # TODO: Change this to a braintree location
        assert os.path.isfile(os.path.join(project_dir, 'proc', d + '_parameters.json'))

        with open(os.path.join(project_dir, 'proc', d + '_parameters.json')) as f:
            parameters = json.load(f)

        # TODO: Unnecessary check since merge.py already kinda does this?
        assert os.path.isfile(os.path.join(project_dir, 'intanraw', d, 'amp-' +
                                           parameters['neuroid']['neuroid_id'][channel] + '.dat'))

        # Read raw data.
        v = read_dat(os.path.join(project_dir, 'intanraw', d, 'amp-' +
                                  parameters['neuroid']['neuroid_id'][channel] + '.dat'))

        nrSegments = parameters['chunks_for_threshold']
        nrPerSegment = int(ceil(len(v) / nrSegments))
        spike_times = []

        # TODO: Detect for both positive and negative thresholds?
        for i in range(nrSegments):
            time_idxs = arange(i * nrPerSegment, (i + 1) * nrPerSegment) / parameters['f_sampling']  # in seconds

            # Apply IIR Filter.
            v1 = apply_bandpass(v[i * nrPerSegment:(i + 1) * nrPerSegment], parameters['f_sampling'],
                                parameters['f_low'], parameters['f_high'], parameters['ellip_order'])
            v2 = v1 - nanmean(v1)

            # Apply threshold.
            noise_level = -parameters['threshold_sd'] * median(abs(v2)) / 0.6745
            outside = array(v2) < noise_level  # Spits a logical array

            outside = outside.astype(int)  # Convert logical array to int array for diff to work

            cross = concatenate(([outside[0]], diff(outside, n=1) > 0))

            idxs = nonzero(cross)[0]
            spike_times.extend(time_idxs[idxs])

        spk_data = {
            parameters['neuroid']['neuroid_id'][channel]: {}
        }
        # Loop through each image.
        for i, item in parameters['item']['id'].items():
            spk_data[parameters['neuroid']['neuroid_id'][channel]][str(item)] = {}
            # Loop through each trial.
            for trial in range(parameters['n_trials']):
                spikes = list(filter(lambda x: x >= parameters['trial_times'][str(item)][str(trial+1)] -
                                     parameters['start_time'], spike_times))  # TODO: Add check for +- sign
                spikes = list(filter(lambda x: x <= parameters['trial_times'][str(item)][str(trial+1)] +
                                     parameters['stop_time'], spikes))  # TODO: Better way to do this
                # Align spikes to stimulus onset (SO)
                spikes = [_ - parameters['trial_times'][str(item)][str(trial+1)] for _ in spikes]
                spk_data[parameters['neuroid']['neuroid_id'][channel]][str(item)][str(trial+1)] = spikes

        # Make temp directory if it does not exist.
        if not os.path.isdir(os.path.join(project_dir, 'temp')):
            os.mkdir(os.path.join(project_dir, 'temp'))

        # Make experiment directory inside temp if it does not exist.
        if not os.path.isdir(os.path.join(project_dir, 'temp', d)):
            os.mkdir(os.path.join(project_dir, 'temp', d))

        with open(os.path.join(project_dir, 'temp', d, 'spk_' + channel + '.json'), 'w') as f:
            json.dump(spk_data, f, indent=4)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-unit activity analysis tools.')
    parser.add_argument('num', metavar='N', type=int,
                        help='channel number or slurm job array id')
    # TODO: Think of a better way to get access to this information than re-reading config
    parser.add_argument('--config', type=str, help='full path and name of the .ini file '
                                                   'defining the experiment parameters')
    args = parser.parse_args()

    assert args.config is not None
    assert os.path.isfile(args.config)

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation(),
                                       inline_comment_prefixes=('#', ';'))
    config.read(args.config)

    # TODO: Add checks for config again?

    # Get date and project_dir
    date = config['Experiment Information']['date_range'].split('-')  # TODO: Fix temporary hack
    date = date[0][-2:] + date[1] + date[2]
    project_dir = config['File IO']['project_dir']

    main(project_dir, date, str(args.num))
