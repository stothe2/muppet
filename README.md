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
                               (data.json)              
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
* `baseline` Spike times for baseline images (in sec)
* `threshold_sd` Threshold for detection
* `chunks_for_threshold` Number of chunks used to determine threshold for detection
* `f_low` Low pass frequency
* `f_high` High pass frequency
* `ellip_order` Order of elliptic filter
* `start_time` Time before stimulus onset when looking for spikes (in sec)
* `stop_time` Time after stimulus onset when looking for spikes (in sec)
