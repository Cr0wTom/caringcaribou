# Dump
````
$ ccn.py dump -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'dump'

usage: ccn.py dump [-h] [-f F] [-c] [W [W ...]]

CAN traffic dump module for CaringCaribou

positional arguments:
  W               Arbitration ID to whitelist

optional arguments:
  -h, --help      show this help message and exit
  -f F, --file F  Write output to file F (default: stdout)
  -c              Output on candump format

Example usage:
  ccn.py dump
  ccn.py dump -f output.txt
  ccn.py dump -c -f output.txt 0x733 0x734
 ```
