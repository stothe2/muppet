import os
import sys
import json
from utilities import read_json


def main(files):
    # We're done if there's only one file.
    if len(files) == 1:
        return

    # Check if files exist.
    for file in files:
        assert os.path.isfile(file)

    data = []
    for i, file in enumerate(files):
        # Load files.
        data.append(read_json(file))
        # Check if necessary fields are present in all files.
        # TODO: Maybe make a function to do this, since it's used often? Also, is this really necessary here?
        assert 'experiment_name' in data[i]
        assert 'experiment_paradigm' in data[i]
        assert 'date' in data[i]
        assert 'neuroid' in data[i]
        assert 'animal' in data[i]['neuroid']
        assert 'f_sampling' in data[i]
        assert 'f_low' in data[i]
        assert 'f_high' in data[i]
        assert 'ellip_order' in data[i]
        assert 'threshold_sd' in data[i]
        assert 'chunks_for_threshold' in data[i]
        assert 'start_time' in data[i]
        assert 'stop_time' in data[i]
        assert 'spikes' in data[i]
        assert 'baseline' in data[i]
        assert 'spikes' in data[i]['baseline']
        assert 'n_grey' in data[i]['baseline']
        assert 'n_other' in data[i]['baseline']
        assert 'n_trials' in data[i]
        assert 'n_channels' in data[i]
        assert 'stim_on_time' in data[i]
        assert 'stim_off_time' in data[i]
        assert 'stim_on_delay' in data[i]
        assert 'inter_trial_interval' in data[i]
        assert 'stim_size' in data[i]
        assert 'fixation_point_size' in data[i]
        assert 'fixation_window_size' in data[i]

    # Check if necessary field values match in all files.
    # TODO: Check if neuroid ids match too?
    assert all(session_data['experiment_name'] == data[0]['experiment_name'] for session_data in data)
    assert all(session_data['experiment_paradigm'] == data[0]['experiment_paradigm'] for session_data in data)
    assert all(session_data['neuroid']['animal'] == data[0]['neuroid']['animal'] for session_data in data)
    assert all(session_data['f_sampling'] == data[0]['f_sampling'] for session_data in data)
    assert all(session_data['f_low'] == data[0]['f_low'] for session_data in data)
    assert all(session_data['f_high'] == data[0]['f_high'] for session_data in data)
    assert all(session_data['ellip_order'] == data[0]['ellip_order'] for session_data in data)
    assert all(session_data['threshold_sd'] == data[0]['threshold_sd'] for session_data in data)
    assert all(session_data['chunks_for_threshold'] == data[0]['chunks_for_threshold'] for session_data in data)
    assert all(session_data['start_time'] == data[0]['start_time'] for session_data in data)
    assert all(session_data['stop_time'] == data[0]['stop_time'] for session_data in data)
    assert all(session_data['n_channels'] == data[0]['n_channels'] for session_data in data)
    assert all(session_data['stim_on_time'] == data[0]['stim_on_time'] for session_data in data)
    assert all(session_data['stim_off_time'] == data[0]['stim_off_time'] for session_data in data)
    assert all(session_data['stim_on_delay'] == data[0]['stim_on_delay'] for session_data in data)
    assert all(session_data['inter_trial_interval'] == data[0]['inter_trial_interval'] for session_data in data)
    assert all(session_data['stim_size'] == data[0]['stim_size'] for session_data in data)
    assert all(session_data['fixation_point_size'] == data[0]['fixation_point_size'] for session_data in data)
    assert all(session_data['fixation_window_size'] == data[0]['fixation_window_size'] for session_data in data)
    assert all(session_data['baseline']['n_grey'] == data[0]['baseline']['n_grey'] for session_data in data)
    assert all(session_data['baseline']['n_other'] == data[0]['baseline']['n_other'] for session_data in data)

    # Populate the new dictionary which will contain all the merged data.
    concatenated_data = dict()
    for key, value in data[0].items():
        if key in ['spikes', 'baseline', 'trial_times', 'date', 'n_trials']:
            continue
        concatenated_data[key] = value

    # Merge dates on which the experiment was run.
    dates = list(set([session_data['date'] for session_data in data]))
    concatenated_data['date'] = ', '.join(dates)

    # Merge the number of trials.
    concatenated_data['n_trials'] = sum(session_data['n_trials'] for session_data in data)

    # Merge spikes.
    # TODO: a more efficient way?
    concatenated_data['spikes'] = {}
    for channel in data[0]['spikes']:
        concatenated_data['spikes'][channel] = {}
        for item in data[0]['spikes'][channel]:
            _ = {}  # Initialize an empty dictionary that will contain data for all trials.
            trial_counter = 0  # Initialize a counter for trial number.
            for session_data in data:
                for trial_data in session_data['spikes'][channel][item].values():
                    trial_counter += 1
                    _[trial_counter] = trial_data
            concatenated_data['spikes'][channel][item] = _

    # Merge baseline.
    concatenated_data['baseline'] = {}
    concatenated_data['baseline']['n_grey'] = data[0]['baseline']['n_grey']
    concatenated_data['baseline']['n_other'] = data[0]['baseline']['n_other']

    concatenated_data['baseline']['spikes'] = {}
    for channel in data[0]['baseline']['spikes']:
        concatenated_data['baseline']['spikes'][channel] = {}
        for item in data[0]['baseline']['spikes'][channel]:
            _ = {}  # Initialize an empty dictionary that will contain data for all trials.
            trial_counter = 0  # Initialize a counter for trial number.
            for session_data in data:
                for trial_data in session_data['baseline']['spikes'][channel][item].values():
                    trial_counter += 1
                    _[trial_counter] = trial_data
            concatenated_data['baseline']['spikes'][channel][item] = _

    # Store data.
    with open('data.json', 'w') as f:
        json.dump(concatenated_data, f, indent=4)  # TODO: Store in a braintree directory?

    return


if __name__ == '__main__':
    assert len(sys.argv) > 1
    main(sys.argv[1:])

    # concat_data('/Volumes/data2/active/users/sachis/projects/test/monkeys/solo/proc/solo_fbop_181229_100311_data.json',
    #             '/Volumes/data2/active/users/sachis/projects/test/monkeys/solo/proc/solo_fbop_181229_100311_data.json')
