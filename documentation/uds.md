# UDS - Unified Diagnostics Services
This module can be used to discover and utilize various diagnostics services. It is built upon the ISO 14229-1 protocol implementation in Caring Caribou and
replaces the old [DCM](./dcm.md) module.

The UDS protocol uses a server-client model, where the client (e.g. a diagnostics tool or Caring Caribou) sends requests on a specific arbitration ID, which a server (ECU) listens to. The server sends responses on another specific arbitration ID.

Supported modes:
* discovery - Scan for arbitration IDs where ECUs listen and respond to incoming diagnostics requests
* services - Scan for diagnostics services supported by an ECU
* subservices - Subservice enumeration of supported diagnostics services by an ECU
* ecu_reset - Reset an ECU
* testerpresent - Force an elevated diagnostics session against an ECU to stay active
* dump_dids - Dumps values of Dynamic Data Identifiers (DIDs)
* auto - Fully automated diagnostics scan, by using the already existing UDS submodules
* write_dids - Writes values of accessible Dynamic Data Identifiers (DIDs)
* dump_mem - Dumps memory of ECU
* routine_control_dump - Dump available routines for Routine Control service


As always, module help can be shown by adding the `-h` flag (as shown below). You can also show help for a specific mode by specifying the mode followed by `-h`, e.g. `ccn.py uds discovery -h` or `ccn.py uds testerpresent -h`

```
$ ccn.py uds -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

usage: ccn.py uds [-h] {discovery,services,subservices,ecu_reset,testerpresent,security_seed,dump_dids,auto,dump_mem,write_dids,routine_control_dump} ...

Universal Diagnostic Services module for CaringCaribouNext

positional arguments:
  {discovery,services,subservices,ecu_reset,testerpresent,security_seed,dump_dids,auto,dump_mem,write_dids,routine_control_dump}

options:
  -h, --help            show this help message and exit

Example usage:
  ccn.py uds discovery
  ccn.py uds discovery -blacklist 0x123 0x456
  ccn.py uds discovery -autoblacklist 10
  ccn.py uds services 0x733 0x633
  ccn.py uds ecu_reset 1 0x733 0x633
  ccn.py uds testerpresent 0x733
  ccn.py uds security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  ccn.py uds dump_dids 0x733 0x633
  ccn.py uds dump_dids 0x733 0x633 --min_did 0x6300 --max_did 0x6fff -t 0.1
```

## Discovery
Scans for arbitration IDs where an ECU responds to UDS requests.

The ID of both the request and the matching response are printed. These are typically used as inputs for other UDS modes.

```
$ ccn.py uds discovery -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

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

## Services
Scans an ECU (or rather, a given pair of request/response arbitration IDs) for supported diagnostics services.

```
$ ccn.py uds services -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

usage: ccn.py uds services [-h] [-t T] [-p P] [-np] src dst

positional arguments:
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

options:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout (default: 0.2)
  -p P, --padding P  padding to be used in target messages (default: 0)
  -np, --no_padding  trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```

## Sub-services
Scans a diagnostics service ID for supported sub-service IDs.

```
$ ccn.py uds subservices -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loading module 'uds'

usage: ccn.py uds subservices [-h] [-t T] [-p P] [-np] dtype stype src dst

positional arguments:
  dtype              Diagnostic Session Control Subsession Byte
  stype              Service ID
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

options:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout (default: 0.02)
  -p P, --padding P  padding to be used in target messages (default: 0)
  -np, --no_padding  trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```


## ECU Reset
Requests a restart of an ECU.

It is common for an ECU to support multiple reset types.

```
$ ccn.py uds ecu_reset -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

usage: ccn.py uds ecu_reset [-h] [-t T] [-p P] [-np] type src dst

positional arguments:
  type               Reset type: 1=hard, 2=key off/on, 3=soft, 4=enable rapid power shutdown, 5=disable rapid power shutdown
  src                arbitration ID to transmit to
  dst                arbitration ID to listen to

options:
  -h, --help         show this help message and exit
  -t T, --timeout T  wait T seconds for response before timeout
  -p P, --padding P  padding to be used in target messages (default: 0)
  -np, --no_padding  trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```

## Tester Present
Sends Tester Present messages to keep an elevated diagnostics session alive.

Elevated sessions (often referred to as "unlocked servers") automatically fall back to default session ("re-lock") once no Tester Present message has been seen for a certain amount of time.

By continuing to send Tester Present messages after a server (ECU) has been unlocked (e.g. by an official diagnostics tool), it can be kept in an unlocked state for an arbitrary amount of time in order to allow continued access to protected services.

```
$ ccn.py uds testerpresent -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

usage: ccn.py uds testerpresent [-h] [-d D] [-dur S] [-spr] [-p P] [-np] src

positional arguments:
  src                   arbitration ID to transmit to

options:
  -h, --help            show this help message and exit
  -d D, --delay D       send TesterPresent every D seconds (default: 0.5)
  -dur S, --duration S  automatically stop after S seconds
  -spr                  suppress positive response
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```

## Dump DIDs
Scans a range of Dynamic Data Identifiers (DIDs) and dumps their values.

```
$ ccn.py uds dump_dids -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loaded module 'uds'

usage: ccn.py uds dump_dids [-h] [-t T] [--min_did MIN_DID] [--max_did MAX_DID] [-p P] [-np] [-r REPORTING] src dst

positional arguments:
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

options:
  -h, --help            show this help message and exit
  -t T, --timeout T     wait T seconds for response before timeout
  --min_did MIN_DID     minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID     maximum device identifier (DID) to read (default: 0xFFFF)
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
  -r REPORTING, --reporting REPORTING
                        reporting to text file, to enable set the option to 1. (default: 0)
```

## Write DIDs
Tests a range of Dynamic Data Identifiers (DIDs) and tries to write them with the UDS service Write Data by Identifier, under the supplied diagnostic session.

```
$ ccn.py uds write_dids -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loading module 'uds'

usage: ccn.py uds write_dids [-h] [-t T] [--min_did MIN_DID] [--max_did MAX_DID] [-r REPORTING] dtype src dst

positional arguments:
  dtype                 Diagnostic Session Control Subsession Byte
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

options:
  -h, --help            show this help message and exit
  -t T, --timeout T     wait T seconds for response before timeout
  --min_did MIN_DID     minimum device identifier (DID) to write (default: 0x0000)
  --max_did MAX_DID     maximum device identifier (DID) to write (default: 0xFFFF)
  -r REPORTING, --reporting REPORTING
                        reporting to text file, to enable set the option to 1. (default: 0)
```

## Auto
Performs a fully automated diagnostics scan from start to finish, by using the already existing CC modules.

```
$ ccn.py uds auto -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loading module 'uds'

usage: ccn.py uds auto [-h] [-min MIN] [-max MAX] [-b B [B ...]] [-ab N] [-sv] [-d D] [-t T] [--min_did MIN_DID] [--max_did MAX_DID] [-p P] [-np] [-r REPORTING]

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
  -t T, --timeout T     wait T seconds for response before timeout (default: 0.2)
  --min_did MIN_DID     minimum device identifier (DID) to read (default: 0x0000)
  --max_did MAX_DID     maximum device identifier (DID) to read (default: 0xFFFF)
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
  -r REPORTING, --reporting REPORTING
                        reporting to text file, to enable set the option to 1. (default: 0)
```

## Memory Dump
Performs a memory dump using the service read_memory_by_address.

```
$ ccn.py uds dump_mem -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loading module 'uds'

usage: ccn.py uds dump_mem [-h] [-t T] [--start_addr START_ADDR] [--mem_length MEM_LENGTH] [--mem_size MEM_SIZE] [--address_byte_size ADDRESS_BYTE_SIZE] [--memory_length_byte_size MEMORY_LENGTH_BYTE_SIZE] [--sess_type SESS_TYPE] [-p P] [-np] src dst

positional arguments:
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

options:
  -h, --help            show this help message and exit
  -t T, --timeout T     wait T seconds for response before timeout
  --start_addr START_ADDR
                        starting address (default: 0x0000)
  --mem_length MEM_LENGTH
                        number of bytes to read (default: 1)
  --mem_size MEM_SIZE   numbers of bytes to return per request (default: 1)
  --address_byte_size ADDRESS_BYTE_SIZE
                        numbers of bytes of the address (default: 2)
  --memory_length_byte_size MEMORY_LENGTH_BYTE_SIZE
                        numbers of bytes of the memory length parameter (default: 1)
  --sess_type SESS_TYPE
                        Session Type for activating service (default: 3)
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```

## Routine Control Dump
Performs a routine control dump using the service routine_control.

```
$ ccn.py uds routine_control_dump -h

-------------------------
CARING CARIBOU NEXT v0.x
-------------------------

Loading module 'uds'

usage: ccn.py uds routine_control_dump [-h] [--dsc dtype] [--subfunction subfunction] [-t T] [--min_routine MIN_ROUTINE] [--max_routine MAX_ROUTINE] [-p P] [-np] src dst

positional arguments:
  src                   arbitration ID to transmit to
  dst                   arbitration ID to listen to

options:
  -h, --help            show this help message and exit
  --dsc dtype           Diagnostic Session Control Subsession Byte
  --subfunction subfunction
                        Routine Control Subfunction Byte: 0x01 startRoutine 0x02 stopRoutine 0x03 requestRoutineResults 0x00, 0x04–0x7F ISOSAEReserved
  -t T, --timeout T     wait T seconds for response before timeout
  --min_routine MIN_ROUTINE
                        minimum routine to execute (default: 0x0000)
  --max_routine MAX_ROUTINE
                        maximum routine to execute (default: 0xFFFF)
  -p P, --padding P     padding to be used in target messages (default: 0)
  -np, --no_padding     trigger for cases where no padding is required, to enable set the option to 1. (default: 0)
```