# MUPPET (Multi-Unit Processing Pipeline: Experiment to Tests)

Inspired from [Ha's](https://github.com/hahong) [project](https://github.com/hahong/maru).

## Usage

```
        +--------+         +--------------------+
        | MWorks |         | Intan Technologies |
        +--------+         +--------------------+
             |                       |
             v                       v
           (.mwk)                  (.dat)
             |                       |
             .                       |
             .                       |
             .                       |
             v                       |
           (.mat)                    |
             |                       |
             v                       v
   +----------------------------------------------+              +----------------+
   | muppet-merge --config=<.ini file name>       | <- (.json) - | Array metadata |
   |   merge behavior .mwk files and neural       |              +----------------+
   |   signal files .dat to produce a merged      |
   |   .json file with all experiment related     |              +----------------+
   |   metadata and trial times                   | <- (.json) - | Image metadata |
   +---------------------+------------------------+              +----------------+
                         |
                         v
       +------- (Merged .json file)
       |                 |
       |                 v
       |    +-------------------------------------------------------+
       |    | muppet-spk_detect <channel> --config=<.ini file name> |
       |    |   collect spike time information                      |
       |    +----------------------+--------------------------------+
       |                           |
       |                +----------+-----------+
       |                |          |           |
       |              (spk_0)    (spk_1) ... (spk_n)
       |                |          |           |
       |                v          v           v
       |    +-----------------------------------------------+
       |    | muppet-clean_up --config=<.ini file name>     |
       +--> |   combine individual spike files and delete   |
            |   any intermediate generated files            |
            +----------------------+------------------------+
                                   |
                                   v
                            (session_data.json)
                                   |
                                   |
                                   |
                                   .
                                   .  x n_sessions
                                   .
                                   V
            +-------------------------------------------------------------+
            | muppet-concat <file_1.json> <file_2.json> ... <file_n.json> |
            |   combines individual session files into a single file      |
            +----------------------+--------------------------------------+
                                   |
                                   V
                            (experiment_data.json)
                                   |
                                   V
            +-------------------------------------------------------+
            | muppet-add_metrics --data <.json file name>           |
            |   runs metrics on the data and saves output in a      |
            |   `passed_metrics` variable in the original data file |
            +----------------------+--------------------------------+
                                   |
                                   V
                            (experiment_data.json)
```

## Data file

Fields

* `experiment_name` Experiment name
* `experiment_paradigm` Experiment paradigm
* `date` Date on which the experiment was run
* `f_sampling` Sampling rate (in Hz)
* `n_channels` Number of channels
* `n_trials` Number of trials
* `item` Stimulus information
    * `id`
    * `category_name`
* `neuroid` Neuroid information
    * `col`
    * `row`
    * `bank`
    * `elec`
    * `label`
    * `arr`
    * `hemisphere`
    * `subregion`
    * `region`
    * `animal`
    * `neuroid_id`
* `spikes` Spike times, aligned to stimulus onset (in sec)
    * `neuroid_id`
        * `item`
            * `trial`
* `baseline`
    * `n_grey` Number of blank items used for baseline correction
    * `n_other` Number of other items used for baseline correction
    * `spikes` Spike times for baseline images, aligned to stimulus onset (in sec)
        * `neuroid_id`
            * `item`
                * `trial`
* `threshold_sd` Threshold for detection
* `chunks_for_threshold` Number of chunks used to determine threshold for detection
* `f_low` Low pass frequency
* `f_high` High pass frequency
* `ellip_order` Order of elliptic filter
* `start_time` Time before stimulus onset when looking for spikes (in sec)
* `stop_time` Time after stimulus onset when looking for spikes (in sec)
* `stim_on_time` Length of time the stimulus was displayed for (in ms)
* `stim_off_time` Inter-stimulus interval (in ms)
* `stim_on_delay` Delay time from start of fixation until start of a trial (in ms)
* `inter_trial_interval` Inter-trial interval (in ms)
* `stim_size` Size of the stimulus (in degrees of visual angle)
* `fixation_point_size` Size of the fixation point (in degrees of visual angle)
* `fixation_window_size` Size of the fixation window (in degrees of visual angle)
* `passed_metrics` Boolean value for each neuroid indicating whether it passed our quality checks or not.
    * `neuroid_id`
* `grouping_idx` A list of _n_ lists (where _n_ is number of dates/sessions), to keep track of which trials\
were recorded on which dates/sessions (important for normalizing if data collected across multiple dates\sessions).
