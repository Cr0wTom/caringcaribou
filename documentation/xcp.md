# XCP
```
-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'xcp'

usage: ccn.py xcp [-h] {discovery,info,dump} ...

XCP module for CaringCaribou

positional arguments:
 {discovery,info,dump}

optional arguments:
 -h, --help            show this help message and exit

Example usage:
 ccn.py xcp discovery
 ccn.py xcp info 1000 1001
 ccn.py xcp dump 0x3e8 0x3e9 0x1fffb000 0x4800 -f bootloader.hex
 ```
 
## Discovery
 ```
-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'xcp'

usage: ccn.py xcp discovery [-h] [-min MIN] [-max MAX]

optional arguments:
 -h, --help            show this help message and exit
 -min MIN
 -max MAX
 ```
 
## Info
 
 ```
-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'xcp'

usage: ccn.py xcp info [-h] src dst

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to

optional arguments:
 -h, --help            show this help message and exit
 ```
 
## Dump
 
 ```
-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'xcp'

usage: ccn.py xcp dump [-h] [-f F] src dst start length

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to
  start       start adress
  length      dump length

optional arguments:
 -h, --help            show this help message and exit
 -f F, -file F         output file
 ```
