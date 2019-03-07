import configparser
import argparse
import os
import re
from read_header import read_header
from scipy.io import loadmat
from numpy import where, bincount, fromfile, nonzero
import json
from utilities import natural_sorting


def main():
    # logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Muli-unit activity analysis tools.')
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
    # TODO: Use waveform information...
    assert config.has_section('Waveform')

    # Check if the necessary options are present in the configuration file.
    assert config.has_option('Experiment Information', 'experiment_name')
    assert config.has_option('Experiment Information', 'experiment_paradigm')
    assert config.has_option('Experiment Information', 'date_range')
    assert config.has_option('Experiment Information', 'users')
    assert config.has_option('Metadata', 'array_metadata')
    assert config.has_option('Metadata', 'image_metadata')
    assert config.has_option('File IO', 'project_dir')
    assert config.has_option('Thresholding', 'threshold_sd')
    assert config.has_option('Thresholding', 'chunks_for_threshold')
    assert config.has_option('Filtering', 'f_low')
    assert config.has_option('Filtering', 'f_high')
    assert config.has_option('Filtering', 'ellip_order')
    assert config.has_option('Detection', 'start_time')
    assert config.has_option('Detection', 'stop_time')
    assert config.has_option('Waveform', 't_before')
    assert config.has_option('Waveform', 't_after')

    # Check if necessary options are not None.
    # TODO: Checks for all variables, or just necessary ones?
    # TODO: Add float and int checks
    assert config['Experiment Information']['date_range'] is not None
    assert config['Metadata']['array_metadata'] is not None
    assert config['Metadata']['image_metadata'] is not None
    assert config['File IO']['project_dir'] is not None
    assert config['Thresholding']['threshold_sd'] is not None
    assert config['Thresholding']['chunks_for_threshold'] is not None
    assert config['Filtering']['f_low'] is not None
    assert config['Filtering']['f_high'] is not None
    assert config['Filtering']['ellip_order'] is not None
    assert config['Detection']['start_time'] is not None
    assert config['Detection']['stop_time'] is not None
    assert config['Waveform']['t_before'] is not None
    assert config['Waveform']['t_after'] is not None

    # Check if project directory exists.
    assert os.path.isdir(config['File IO']['project_dir'])
    assert os.path.isdir(os.path.join(config['File IO']['project_dir'], 'intanraw'))
    assert os.path.isdir(os.path.join(config['File IO']['project_dir'], 'mworksproc'))

    # Check if date is in a valid format.
    assert re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', config['Experiment Information']['date_range'])
    # Temporary hack to change date_range to a format that is currently valid. TODO: Change this
    date = config['Experiment Information']['date_range'].split('-')
    date = date[0][-2:] + date[1] + date[2]

    # Check if Intan directory for the particular date exists, as well as the corresponding Intan files.
    with os.scandir(os.path.join(config['File IO']['project_dir'], 'intanraw')) as it:
        dirs = [entry.name for entry in it if entry.is_dir() and entry.name.find(date) is not -1]
    dirs.sort(key=natural_sorting)
    assert len(dirs) != 0

    # TODO: maybe a better way for checking this?
    for _ in dirs:
        assert os.path.isfile(os.path.join(config['File IO']['project_dir'], 'intanraw', _, 'info.rhd'))
        f = open(os.path.join(config['File IO']['project_dir'], 'intanraw', _, 'info.rhd'), 'rb')
        header = read_header(f)
        assert header['num_amplifier_channels'] != 0
        assert header['num_board_dig_in_channels'] == 2
        f.close()

    # Check if MWorks file for the particular date exists.
    # TODO: Use pymworks or equivalent to unpack .mwk files within this pipeline
    with os.scandir(os.path.join(config['File IO']['project_dir'], 'mworksproc')) as it:
        mfiles = [entry.name for entry in it if entry.name.find(date) is not -1]
    mfiles.sort(key=natural_sorting)
    assert len(mfiles) != 0

    # Check for equal number of Intan dirs and MWorks files.
    assert len(dirs) == len(mfiles)

    # Check if image metadata file exists.
    assert os.path.isfile(config['Metadata']['image_metadata'])

    # Check if array metadata file exists.
    assert os.path.isfile(config['Metadata']['array_metadata'])

    # Create a dictionary with all the parameters.
    parameters = dict()
    parameters['experiment_name'] = config['Experiment Information']['experiment_name']
    parameters['experiment_paradigm'] = config['Experiment Information']['experiment_paradigm']
    parameters['date'] = config['Experiment Information']['date_range']

    # Get image metadata and store it in parameters before starting the loop.
    # TODO: Add checks for metadata file?
    parameters['item'] = {}
    with open(config['Metadata']['image_metadata']) as f:
        parameters['item'] = json.load(f)

    # Get array metadata and store it in parameters before starting the loop.
    # TODO: Add checks for metadata file?
    parameters['neuroid'] = {}
    with open(config['Metadata']['array_metadata']) as f:
        parameters['neuroid'] = json.load(f)

    # Loop through each directory, and create and save a metadata structure.
    for i, d in enumerate(dirs):
        # Get experimental sampling rate and channel count information.
        f = open(os.path.join(config['File IO']['project_dir'], 'intanraw', d, 'info.rhd'), 'rb')
        header = read_header(f)
        f.close()

        parameters['f_sampling'] = header['sample_rate']
        parameters['n_channels'] = header['num_amplifier_channels']

        # Check if channel count information from array metadata matches experimental output.
        assert parameters['n_channels'] == len(parameters['neuroid']['neuroid_id'])

        # Get information on number of trials from MWorks data.
        behavior_data = loadmat(os.path.join(config['File IO']['project_dir'], 'mworksproc', mfiles[i]),
                                squeeze_me=True)
        fixation_correct = behavior_data['fixation_correct']
        image_order = behavior_data['image_order']

        correct_trials = image_order[where(fixation_correct == 1)]

        repetition_count = []
        for _, item in parameters['item']['id'].items():
            repetition_count.append(len(correct_trials[correct_trials == item]))
        most_frequent_rep_num = bincount(repetition_count).argmax()

        parameters['n_trials'] = int(most_frequent_rep_num)  # Convert from numpy.int64 to int for JSON serialization

        # Create a "spikes" field in the parameters dictionary so it can be populated easily later.
        parameters['spikes'] = {}

        # Create a "baseline" field in the parameters dictionary so it can be populated easily later.
        parameters['baseline'] = {}

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

        # Merge and store trial time data.
        parameters['trial_times'] = {}
        for _, item in parameters['item']['id'].items():
            parameters['trial_times'][item] = {}
            rows = where((image_order == item) & (fixation_correct == 1))[0]
            for trial in range(parameters['n_trials']):
                parameters['trial_times'][item][trial+1] = samp_on[rows[trial]]  # +1 to get around zero-indexing

        # Store all params in the parameters dict too so that methods that work on top of it know where to look
        # without accessing the config file.
        # TODO: Do this earlier?
        parameters['project_dir'] = config['File IO']['project_dir']
        parameters['threshold_sd'] = config.getfloat('Thresholding', 'threshold_sd')
        parameters['chunks_for_threshold'] = config.getint('Thresholding', 'chunks_for_threshold')
        parameters['f_low'] = config.getfloat('Filtering', 'f_low')
        parameters['f_high'] = config.getfloat('Filtering', 'f_high')
        parameters['ellip_order'] = config.getint('Filtering', 'ellip_order')
        parameters['start_time'] = config.getfloat('Detection', 'start_time')
        parameters['stop_time'] = config.getfloat('Detection', 'stop_time')

        # Make proc directory if it does not exist.
        if not os.path.isdir(os.path.join(config['File IO']['project_dir'], 'proc')):
            os.mkdir(os.path.join(config['File IO']['project_dir'], 'proc'))

        # Store data.
        with open(os.path.join(config['File IO']['project_dir'], 'proc', d + '_parameters.json'), 'w') as f:
            json.dump(parameters, f, indent=4)  # TODO: Store in a braintree directory


if __name__ == '__main__':
    main()
