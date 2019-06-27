import configparser
import argparse
import os
import re
from scipy.io import loadmat
from numpy import where, bincount, fromfile, nonzero
import json
from utilities import natural_sorting, read_rhd


def main():
    # logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Muli-unit activity spike extraction tools.')
    parser.add_argument('--config', type=str, help='full path and name of the .ini file '
                                                   'defining the experiment parameters')
    args = parser.parse_args()

    # Check if config option is not none.
    assert args.config is not None
    # Check if config file exists.
    assert os.path.isfile(args.config)

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation(),
                                       inline_comment_prefixes=('#', ';'))
    config.read(args.config)

    # Check if the necessary sections are present in the configuration file.
    assert config.has_section('Experiment Information')
    assert config.has_section('Metadata')
    assert config.has_section('File IO')
    assert config.has_section('Thresholding')
    assert config.has_section('Filtering')
    assert config.has_section('Detection')
    assert config.has_section('Baseline')
    assert config.has_section('Normalizer Set')

    # Check if the necessary options are present in the configuration file.
    assert config.has_option('Experiment Information', 'experiment_name')
    assert config.has_option('Experiment Information', 'experiment_paradigm')
    assert config.has_option('Experiment Information', 'date_range')
    assert config.has_option('Experiment Information', 'users')
    assert config.has_option('Metadata', 'array_meta')
    assert config.has_option('Metadata', 'image_meta')
    assert config.has_option('File IO', 'project_dir')
    assert config.has_option('Thresholding', 'threshold_sd')
    assert config.has_option('Thresholding', 'chunks_for_threshold')
    assert config.has_option('Filtering', 'f_low')
    assert config.has_option('Filtering', 'f_high')
    assert config.has_option('Filtering', 'ellip_order')
    assert config.has_option('Detection', 't_start')
    assert config.has_option('Detection', 't_stop')
    assert config.has_option('Baseline', 'num_grey')
    assert config.has_option('Normalizer Set', 'num_normalizer')

    # Check if necessary options are not None.
    # TODO: Checks for all variables, or just necessary ones?
    # TODO: Add float and int checks
    assert config['Experiment Information']['date_range'] is not None
    assert config['Metadata']['array_meta'] is not None
    assert config['Metadata']['image_meta'] is not None
    assert config['File IO']['project_dir'] is not None
    assert config['Thresholding']['threshold_sd'] is not None
    assert config['Thresholding']['chunks_for_threshold'] is not None
    assert config['Filtering']['f_low'] is not None
    assert config['Filtering']['f_high'] is not None
    assert config['Filtering']['ellip_order'] is not None
    assert config['Detection']['t_start'] is not None
    assert config['Detection']['t_stop'] is not None
    assert config['Baseline']['num_grey'] is not None
    assert config['Normalizer Set']['num_normalizer'] is not None

    # Check if project directory exists.
    assert os.path.isdir(config['File IO']['project_dir'])
    assert os.path.isdir(os.path.join(config['File IO']['project_dir'], 'intanraw'))
    assert os.path.isdir(os.path.join(config['File IO']['project_dir'], 'mworksproc'))

    # Check if date is in a valid format.
    assert re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', config['Experiment Information']['date_range'])
    # Temporary hack to change date_range to a format that is currently valid. TODO: Change this (maybe?)
    date = config['Experiment Information']['date_range'].split('-')
    date = date[0][-2:] + date[1] + date[2]

    # Check if Intan directory for the particular date exists, as well as the corresponding Intan files.
    with os.scandir(os.path.join(config['File IO']['project_dir'], 'intanraw')) as it:
        dirs = [entry.name for entry in it if entry.is_dir() and entry.name.find(date) is not -1
                and not entry.name.startswith('.')]
    dirs.sort(key=natural_sorting)
    assert len(dirs) != 0

    # Check if the intan raw data directory actually contains neural recording files.
    for _ in dirs:
        assert os.path.isfile(os.path.join(config['File IO']['project_dir'], 'intanraw', _, 'info.rhd'))
        f = open(os.path.join(config['File IO']['project_dir'], 'intanraw', _, 'info.rhd'), 'rb')
        header = read_rhd(f)
        assert header['num_amplifier_channels'] != 0
        assert header['num_board_dig_in_channels'] == 2
        f.close()

    # Check if MWorks file for the particular date exists.
    # TODO: Use pymworks or equivalent to unpack .mwk files within this pipeline
    with os.scandir(os.path.join(config['File IO']['project_dir'], 'mworksproc')) as it:
        mfiles = [entry.name for entry in it if entry.name.find(date) is not -1 and not entry.name.startswith('.')]
    mfiles.sort(key=natural_sorting)
    assert len(mfiles) != 0

    # Check for equal number of Intan dirs and MWorks files.
    assert len(dirs) == len(mfiles)

    # Check if image metadata file exists.
    assert os.path.isfile(config['Metadata']['image_meta'])

    # Check if array metadata file exists.
    assert os.path.isfile(config['Metadata']['array_meta'])

    # Create a dictionary with all the parameters.
    parameters = dict()
    parameters['experiment_name'] = config['Experiment Information']['experiment_name']
    parameters['experiment_paradigm'] = config['Experiment Information']['experiment_paradigm']
    parameters['date'] = config['Experiment Information']['date_range']

    # Get image metadata and store it in parameters before starting the loop.
    # TODO: Add checks for metadata file?
    parameters['item'] = {}
    with open(config['Metadata']['image_meta']) as f:
        parameters['item'] = json.load(f)

    # Get array metadata and store it in parameters before starting the loop.
    # TODO: Add checks for metadata file?
    parameters['neuroid'] = {}
    with open(config['Metadata']['array_meta']) as f:
        parameters['neuroid'] = json.load(f)

    # Loop through each directory, and create and save a metadata structure.
    for i, d in enumerate(dirs):
        # Get experimental sampling rate and channel count information.
        f = open(os.path.join(config['File IO']['project_dir'], 'intanraw', d, 'info.rhd'), 'rb')
        header = read_rhd(f)
        f.close()

        parameters['f_sampling'] = header['sample_rate']
        parameters['n_channels'] = header['num_amplifier_channels']

        # Check if channel count information from array metadata matches experimental output.
        assert parameters['n_channels'] == len(parameters['neuroid']['neuroid_id'])

        # Get information on number of trials from MWorks data.
        behavior_data = loadmat(os.path.join(config['File IO']['project_dir'], 'mworksproc', mfiles[i]),
                                squeeze_me=True)
        assert 'fixation_correct' in behavior_data.keys()
        assert 'image_order' in behavior_data.keys()
        fixation_correct = behavior_data['fixation_correct']
        image_order = behavior_data['image_order']

        correct_trials = image_order[where(fixation_correct == 1)]

        repetition_count = []
        for _, item in parameters['item']['id'].items():
            repetition_count.append(len(correct_trials[correct_trials == item]))
        most_frequent_rep_num = bincount(repetition_count).argmax()

        parameters['num_trials'] = int(most_frequent_rep_num)  # Convert from numpy.int64 to int for JSON serialization

        # Get information on experiment settings from MWorks data.
        assert 'meta' in behavior_data.keys()
        parameters['stim_on_time'] = behavior_data['meta']['stim_on_time'].item()
        parameters['stim_off_time'] = behavior_data['meta']['stim_off_time'].item()
        parameters['stim_on_delay'] = behavior_data['meta']['stim_on_delay'].item()
        parameters['inter_trial_interval'] = behavior_data['meta']['inter_trial_interval'].item()
        parameters['stim_size'] = behavior_data['meta']['stim_size'].item()
        parameters['fixation_point_size'] = behavior_data['meta']['fixation_point_size'].item()
        parameters['fixation_window_size'] = behavior_data['meta']['fixation_window_size'].item()

        # Create a "spikes" field in the parameters dictionary so it can be populated easily later.
        parameters['spikes'] = {}

        # Create a "baseline_spikes" field in the parameters dictionary so it can be populated easily later.
        parameters['baseline'] = {}
        parameters['baseline']['spikes'] = {}

        # Create a "normalizer_spikes" field in the parameters dictionary so it can be populated easily later.
        parameters['normalizer'] = {}
        parameters['normalizer']['spikes'] = {}

        # Get all trial time information.
        filename = os.path.join(config['File IO']['project_dir'], 'intanraw', d,
                                'board-DIGITAL-IN-02.dat')  # TODO: Add check for existence of file
        fid = open(filename, 'r')
        filesize = os.path.getsize(filename)  # in bytes
        num_samples = filesize // 2  # uint16 = 2 bytes
        din02 = fromfile(fid, 'uint16', num_samples)
        fid.close()

        # Look for 0->1 transitions.
        samp_on, = nonzero(din02[:-1] < din02[1:])
        # Previous line returns indexes of 0s seen before spikes, but we want indexes of first spikes.
        samp_on = samp_on + 1
        # Divide by sampling rate to get correct unit of time (in seconds).
        samp_on = samp_on / parameters['f_sampling']
        samp_on *= 1000  # sec to msec

        # Merge and store trial time data.
        parameters['trial_times'] = {}
        for _, item in parameters['item']['id'].items():
            parameters['trial_times'][item] = {}
            rows = where((image_order == item) & (fixation_correct == 1))[0]
            for trial in range(parameters['num_trials']):
                parameters['trial_times'][item][trial+1] = round(samp_on[rows[trial]], 3)  # +1 to get around zero-indexing

        # Store baseline and normalizer metadata.
        # TODO: Add stimulus category names information
        parameters['num_grey'] = config.getint('Baseline', 'num_grey')
        parameters['num_normalizer'] = config.getint('Normalizer Set', 'num_normalizer')

        # Check whether stimulus/item IDs are zero-indexed or not, because that will affect how we compute
        # the IDs for baseline images.
        is_zero_indexed = False
        if parameters['item']['id']['0'] == 0:
            is_zero_indexed = True

        # Store trial time data for baseline images.
        parameters['baseline']['trial_times'] = {}
        for baseline_item in range(len(parameters['item']['id']) + int(not is_zero_indexed),
                                   len(parameters['item']['id']) + parameters['num_grey'] +
                                   int(not is_zero_indexed)):
            parameters['baseline']['trial_times'][baseline_item] = {}
            rows = where((image_order == baseline_item) & (fixation_correct == 1))[0]
            for trial in range(parameters['num_trials']):
                parameters['baseline']['trial_times'][baseline_item][trial+1] = round(samp_on[rows[trial]], 3)  # +1 to get around zero-indexing

        # Store trial time data for normalizer images.
        parameters['normalizer']['trial_times'] = {}
        for normalizer_item in range(len(parameters['item']['id']) + int(not is_zero_indexed) + parameters['num_grey'],
                                     len(parameters['item']['id']) + int(not is_zero_indexed) +
                                     parameters['num_grey'] + parameters['num_normalizer']):
            parameters['normalizer']['trial_times'][normalizer_item] = {}
            rows = where((image_order == normalizer_item) & (fixation_correct == 1))[0]
            for trial in range(parameters['num_trials']):
                parameters['normalizer']['trial_times'][normalizer_item][trial + 1] = round(samp_on[rows[trial]], 3)  # +1 to get around zero-indexing

        # Store all params in the parameters dict too so that methods that work on top of it know where to look
        # without accessing the config file.
        # TODO: Do this earlier?
        parameters['project_dir'] = config['File IO']['project_dir']
        parameters['threshold_sd'] = config.getfloat('Thresholding', 'threshold_sd')
        parameters['chunks_for_threshold'] = config.getint('Thresholding', 'chunks_for_threshold')
        parameters['f_low'] = config.getfloat('Filtering', 'f_low')
        parameters['f_high'] = config.getfloat('Filtering', 'f_high')
        parameters['ellip_order'] = config.getint('Filtering', 'ellip_order')
        parameters['t_start'] = config.getfloat('Detection', 't_start')
        parameters['t_stop'] = config.getfloat('Detection', 't_stop')

        # Make proc directory if it does not exist.
        if not os.path.isdir(os.path.join(config['File IO']['project_dir'], 'proc')):
            os.mkdir(os.path.join(config['File IO']['project_dir'], 'proc'))

        # Make proc/experiment directory if it does not exist.
        if not os.path.isdir(os.path.join(config['File IO']['project_dir'], 'proc', d)):
            os.mkdir(os.path.join(config['File IO']['project_dir'], 'proc', d))

        # Store data (w/o overwriting)
        assert not os.path.isfile(os.path.join(config['File IO']['project_dir'], 'proc', d, d + '_trialtime.json'))
        with open(os.path.join(config['File IO']['project_dir'], 'proc', d, d + '_trialtime.json'), 'w') as f:
            json.dump(parameters, f, indent=4)


if __name__ == '__main__':
    main()
