## How to use
The best way to understand how to use Caring Caribou Next is to look at ccn.py's help menu:
    
    ccn.py --help

This will list all available modules at the bottom of the output:

```
$ ccn.py --help
usage: ccn.py [-h] [-i INTERFACE] [-c CHANNEL] [-b BITRATE] [-d DUMP] module ...

---------------------------------------------------------------------------------------------
CARING CARIBOU NEXT v0.x
    \_\_    _/_/                 ______   ______    .__   __.  __________   ___ .__________.
        \__/                    /      | /      |   |  \ |  | |   ____\  \ /  / |           |
        (oo)\_______           |  ,----'|  ,----'   |   \|  | |  |__   \  V  /  `---|  |---`
        (__)\       )\/        |  |     |  |        |  . `  | |   __|   >   <       |  |     
            ||-----||          |  `----.|  `----.   |  |\   | |  |____ /  .  \      |  |     
            ||     ||           \______| \______|   |__| \__| |_______/__/ \__\     |__|    
---------------------------------------------------------------------------------------------

A fork of a friendly car security exploration tool

positional arguments:
  module        Name of the module to run
  ...           Arguments to module

options:
  -h, --help    show this help message and exit
  -i INTERFACE  force interface, e.g. 'socketcan' or 'kvaser'
  -c CHANNEL    force channel, e.g. 'can1' or 'vcan0'
  -b BITRATE    force bitrate, e.g. '250000' or '500000'
  -d DUMP       generation of CAN dump file for further evaluation after each scan

available modules:
  dcm, doip, dump, fuzzer, listener, send, test, uds, uds_fuzz, xcp
```

So in order to see usage information for e.g. the `uds` module, run

    $ ccn.py uds --help

which will show both module specific arguments and some usage examples:

```
$ ccn.py uds -h

---------------------------------------------------------------------------------------------
CARING CARIBOU NEXT v0.x
---------------------------------------------------------------------------------------------

Loading module 'uds'

usage: ccn.py uds [-h] {discovery,services,subservices,ecu_reset,testerpresent,security_seed,dump_dids,auto,dump_mem,write_dids,routine_control_dump} ...

Universal Diagnostic Services module for CaringCaribouNext

positional arguments:
  {discovery,services,subservices,ecu_reset,testerpresent,security_seed,dump_dids,auto,dump_mem,write_dids,routine_control_dump}

options:
  -h, --help            show this help message and exit

Example usage:
  ccn.py uds discovery
  ccn.py uds discovery -blacklist 0x123 0x456
  ccn.py uds services 0x733 0x633
  ccn.py uds subservices 0x02 0x27 0x733 0x633
  ccn.py uds ecu_reset 1 0x733 0x633
  ccn.py uds testerpresent 0x733
  ccn.py uds security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  ccn.py uds dump_dids 0x733 0x633
  ccn.py uds write_dids 0x733 0x633 --min_did 0x6300 --max_did 0x9fff -t 0.1
  ccn.py uds auto -min 0x733 --min_did 0x6300 --max_did 0x6fff --max_routine 0x1000
  ccn.py uds dump_mem 0x733 0x633 --start_addr 0x0200 --mem_length 0x10000
  ccn.py uds routine_control_dump 0x733 0x633 --dsc 0x02 --subfunction 0x02 
```

Any sub-commands (in this case, `discovery`) have their own help screen as well. Let's have a look at the `discovery` option:

```
$ ccn.py uds discovery -h

---------------------------------------------------------------------------------------------
CARING CARIBOU NEXT v0.x
---------------------------------------------------------------------------------------------

Loading module 'uds'

usage: ccn.py uds discovery [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N] [-sv] [-d D] [-p P] [-np]

options:
  -h, --help            show this help message and exit
  -min MIN              min arbitration ID to send request for
  -max MAX              max arbitration ID to send request for
  -b B [B ...], --blacklist B [B ...]
                        arbitration IDs to blacklist responses from
  -ab N, --autoblacklist N
                        listen for false positives for N seconds and blacklist matching arbitration IDs before running discovery
  -sv, --skipverify     skip verification step (reduces result accuracy)
  -d D, --delay D       D seconds delay between messages (default: 0.01)
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```

### Non-default interface
In order to use a non-default CAN interface for any module, you can always provide the `-i INTERFACE` flag before the module name.

For instance, in oder to send the message `c0 ff ee` with arbitration ID `0xf00` on virtual CAN bus `vcan0`, you would run

    $ ccn.py -i vcan0 send message 0xf00#c0.ff.ee

More information on the different modules is available here:
+ [uds-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/uds.md)
+ [dcm-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/dcm.md)
+ [doip-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/doip.md)
+ [dump-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/dump.md)
+ [fuzzer-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/fuzzer.md)
+ [listener-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/listener.md)
+ [send-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/send.md)
+ [uds_fuzz-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/uds_fuzz.md)
+ [xcp-module](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/xcp.md)

### Virtual CAN bus
In order to communicate over CAN without access to a physical CAN bus, it is possible to use a virtual CAN bus instead. Doing this in Linux is generally as easy as running the following commands:

    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up

## Example use
In this example we have connected a compatible [hardware](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/README.md#hardware-requirements) (PiCAN) to our client computer (a Raspberry Pi) and installed the software according to the [instructions](https://github.com/Cr0wTom/caringcaribounext/blob/master/documentation/howtoinstall.md#raspberry-pi).

The PiCAN is then connected to a CAN bus that features one or more ECUs. Since we know very little about the target ECUs, a great start is to do some discovery. Currently three types of discovery is available; dcm discovery, xcp discovery and the listener.

#### The listener
Let's start with the listener:

    ccn.py -h
    ccn.py listener -h
    ccn.py listener

(you can stop the listener with ctrl-C)

```
Last ID: 0x002 (total found: 30)

Detected arbitration IDs:
Arb id 0x001 114 hits
Arb id 0x002 13 hits
```

On our system we found two active arbitration IDs - probably sending some important signal/measurement repeatedly. Let's investigate if diagnostics are present on some ECUs.

#### UDS Diagnostic discovery

    ccn.py uds -h
    ccn.py uds discovery -h
    ccn.py -i socketcan -c can0 -b 500000 uds discovery


```
Loading module 'uds'

Sending Diagnostic Session Control to 0x07e0
  Verifying potential response from 0x07e0
    Resending 0x7e0...  No response
    Resending 0x7df...  Success
Found diagnostics server listening at 0x07df, response at 0x075c
Sending Diagnostic Session Control to 0x07ff

Identified diagnostics:

+------------+------------+
| CLIENT ID  | SERVER ID  |
+------------+------------+
| 0x000007df | 0x0000075c |
+------------+------------+
```

Great! Now we now what arbitration ID to use when we look for services and subfunctions:

    ccn.py -i socketcan -c can0 -b 500000 uds services 0x7df 0x75c

```
Loading module 'uds'

Probing service 0xff (255/255): found 11
Done!

Supported service 0x10: DIAGNOSTIC_SESSION_CONTROL
Supported service 0x11: ECU_RESET
Supported service 0x14: CLEAR_DIAGNOSTIC_INFORMATION
Supported service 0x19: READ_DTC_INFORMATION
Supported service 0x22: READ_DATA_BY_IDENTIFIER
Supported service 0x27: SECURITY_ACCESS
Supported service 0x2e: WRITE_DATA_BY_IDENTIFIER
Supported service 0x2f: INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
Supported service 0x31: ROUTINE_CONTROL
Supported service 0x3e: TESTER_PRESENT
Supported service 0x85: CONTROL_DTC_SETTING
```

This gives us that the service READ_DATA_BY_IDENTIFIER (0x22) is available. 0x22 is typically followed by a two byte parameter ID (PID). To enumerate we can use the dedicated submodule:

    ccn.py -i socketcan -c can0 -b 500000 uds dump_dids 0x7df 0x75c --min_did 0xf150

```
Loading module 'uds'

Dumping DIDs in range 0xf150-0xffff

Identified DIDs:
DID    Value (hex)
('0xf163', '04')

Terminated by user
```

Similarly, more subnmodules can be used for further enumeration and exploitation of the research target.

#### XCP discovery
Enough with diagnostics, let's investigate XCP in more or less the same way

    ccn.py xcp -h
    ccn.py xcp discovery -h
    ccn.py -i socketcan -c can5 -b 500000 xcp discovery -min 0x003

(no need to do discovery on 0x001 and 0x002)

```
Loaded module 'xcp'

Starting XCP discovery
Sending XCP Connect to 0x03e8 > DECODE CONNECT RESPONSE

Resource protection status
(...skipping)

COMM_MODE_BASIC
(...skipping)

Found XCP at arb ID 0x03e8, reply at 0x03e9
```

For XCP you can get more information by running

    ccn.py -i socketcan -c can5 -b 500000 xcp info 0x3e8 0x3e9

and you can try to dump parts of the memory by using

    ccn.py -i socketcan -c can5 -b 500000 xcp dump 0x3e8 0x3e9 0x1f0000000 0x4800 -f bootloader.hex
