# MUPPET (Multi-Unit Processing Pipeline: Experiment to Tests)

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
       +--> |   combine invidual spike files and delete     |
            |   any intermediate genrated files             |
            +----------------------+------------------------+
                                   |
                                   v
                               (data.json)              
```