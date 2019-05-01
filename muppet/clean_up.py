import os
import argparse
import configparser
import json
from muppet.utilities import natural_sorting
import shutil


def main(project_dir, date):
    # TODO: Maybe add checks to ensure params.json and config.ini information match?

    # Get names of all directories with the specified 'date'.
    with os.scandir(os.path.join(project_dir, 'intanraw')) as it:
        dirs = [entry.name for entry in it if (entry.is_dir() and entry.name.find(date) is not -1)]

    # Loop through each directory, and clean up.
    for d in dirs:
        # Check if the parameters file---where all data is going to be stored---exists.
        assert os.path.isfile(os.path.join(project_dir, 'proc', d + '_parameters.json'))

        with open(os.path.join(project_dir, 'proc', d + '_parameters.json')) as f:
            parameters = json.load(f)

        # Check if the temp folder where all the individual spike files live exists.
        assert os.path.isdir(os.path.join(project_dir, 'temp', d))

        # Get names of all the individual spike files.
        with os.scandir(os.path.join(project_dir, 'temp', d)) as it:
            spk_files = [entry.name for entry in it if (entry.name.startswith('spk_') and entry.name.endswith('.json'))]
        spk_files.sort(key=natural_sorting)

        # Check if files for all channels are present.
        # assert len(spk_files) == parameters['n_channels']  # TODO: Add it after finishing testing

        # Loop through all spike files and populate them in parameters.
        for file in spk_files:
            with open(os.path.join(project_dir, 'temp', d, file)) as f:
                spk_data = json.load(f)
                for key, value in spk_data.items():
                    parameters['spikes'][key] = value
            os.remove(os.path.join(project_dir, 'temp', d, file))

        with open(os.path.join(project_dir, 'proc', d + '_data.json'), 'w') as f:
            json.dump(parameters, f, indent=4)

        # Delete the individual spike files.
        os.rmdir(os.path.join(project_dir, 'temp', d))

        # Delete params file.
        os.remove(os.path.join(project_dir, 'proc', d + '_parameters.json'))

    # Delete main temp directory
    shutil.rmtree(os.path.join(project_dir, 'temp'), ignore_errors=True)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-unit activity analysis tools.')
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

    main(project_dir, date)
