# DCM
```
$ ccn.py dcm -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dcm'

usage: ccn.py dcm [-h] {discovery,services,subfunc,dtc} ...

Diagnostics module for CaringCaribou

positional arguments:
  {discovery,services,subfunc,dtc}

optional arguments:
  -h, --help            show this help message and exit

Example usage:
  ccn.py dcm discovery
  ccn.py dcm services 0x733 0x633
  ccn.py dcm subfunc 0x733 0x633 0x22 2 3
  ccn.py dcm dtc 0x7df 0x7e8
 ```

## Discovery
```
$ ccn.py dcm discovery -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dcm'

usage: ccn.py dcm discovery [-h] [-min MIN] [-max MAX] [-nostop]
                           [-blacklist B [B ...]] [-autoblacklist N]

optional arguments:
  -h, --help            show this help message and exit
  -min MIN
  -max MAX
  -nostop               scan until end of range
  -blacklist B [B ...]  arbitration IDs to ignore
  -autoblacklist N      scan for interfering signals for N seconds and
                        blacklist matching arbitration IDs
```

## Services
````
$ ccn.py dcm services -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dcm'

usage: ccn.py dcm services [-h] src dst

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to

optional arguments:
  -h, --help  show this help message and exit
````

## Subfunc
````
$ ccn.py dcm subfunc -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dcm'

usage: ccn.py dcm subfunc [-h] [-show] src dst service i [i ...]

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to
  service     service ID (e.g. 0x22 for Read DID)
  i           sub-function indices

optional arguments:
  -h, --help  show this help message and exit
  -show       show data in terminal
````

## DTC
````
$ ccn.py dcm dtc -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dcm'

usage: ccn.py dcm dtc [-h] [-clear] src dst

positional arguments:
  src         arbitration ID to transmit from
  dst         arbitration ID to listen to

optional arguments:
  -h, --help  show this help message and exit
  -clear      Clear DTC / MIL
````
