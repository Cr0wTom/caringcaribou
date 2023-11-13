# Caring Caribou Next
A fork of a friendly automotive security exploration tool.

    \_\_    _/_/                 ______   ______    .__   __.  __________   ___ .__________.
        \__/                    /      | /      |   |  \ |  | |   ____\  \ /  / |           |
        (oo)\_______           |  ,----'|  ,----'   |   \|  | |  |__   \  V  /  `---|  |---`
        (__)\       )\/        |  |     |  |        |  . `  | |   __|   >   <       |  |     
            ||-----||          |  `----.|  `----.   |  |\   | |  |____ /  .  \      |  |     
            ||     ||           \______| \______|   |__| \__| |_______/__/ \__\     |__|    

            

## Rationale
This work was initiated as part of the research project HEAVENS (HEAling Vulnerabilities to ENhance Software Security and Safety), and was forked to act as a quick way to perform changes for personal use, and for people that are intrested on those changes.

While caringcaribounext is not perfect, it can act as a quick evaluation utility, which can help with exploration of a target ECU over several target networks/interfaces. This project is not meant to be a complete one button solution, but a tool that can give researchers a quick and easy head start into the path of ECU exploration.


## Documentation
- [How to install](documentation/howtoinstall.md)
- [How to use](documentation/howtouse.md)
- [Modules](documentation/README.md)
- [Troubleshooting](documentation/troubleshooting.md), common errors and solutions
- [Contributors](documentation/contributors.md)
- [Research](documentation/research.md)

## Get started
Install the tool:

    pip install .

The best way to understand how to use Caring Caribou is to look at the help screen:

    ccn.py --help

This will list all available modules at the bottom of the output. Help for specific modules works the same way. For example, the help screen for the `uds` module is shown by running

    ccn.py uds --help

The module help always includes some usage examples. If the module has multiple sub functions, these have similar help screens as well:

    ccn.py uds discovery -h
    ccn.py uds auto -h

More detailed usage information is available [in the documentation on usage](documentation/README.md).

## Features and Architecture
Caring Caribou Next is based on a main entry point, `ccn.py`, which runs the show. This enables an easy drop-in architecture for new modules, which are located in the `caringcaribounext/modules` folder.

The `caringcaribounext/utils` folder contains various higher level CAN protocol implementations and shared functions, meant to be used by modules.

The `caringcaribounext/tests` folder contains automated test suites and `/documentation` stores documentation files (modules are also documented here).
