#!/usr/bin/env python
# Released under GNU General Public License v3
# https://github.com/Cr0wTom/caringcaribounext
# Original repo released under GNU General Public License v3
# https://github.com/CaringCaribou/caringcaribou

import argparse
import can
import errno
from .utils import can_actions
import traceback
import pkg_resources
from caringcaribounext.utils.can_listener import start_listener
from caringcaribounext.utils.common import list_to_hex_str


VERSION = "1.1"


def show_script_header():
    """Show script header"""
    print(r"""
{0}
CARING CARIBOU NEXT v{1}
{0}
""".format("-"*(92 + len(VERSION)), VERSION))


def fancy_header():
    """
    Returns a fancy header string.

    :rtype: str
    """
    return r"""{0}
CARING CARIBOU NEXT v{1}
    \_\_    _/_/                 ______   ______    .__   __.  __________   ___ .__________.
        \__/                    /      | /      |   |  \ |  | |   ____\  \ /  / |           |
        (oo)\_______           |  ,----'|  ,----'   |   \|  | |  |__   \  V  /  `---|  |---`
        (__)\       )\/        |  |     |  |        |  . `  | |   __|   >   <       |  |     
            ||-----||          |  `----.|  `----.   |  |\   | |  |____ /  .  \      |  |     
            ||     ||           \______| \______|   |__| \__| |_______/__/ \__\     |__|    
{0}

""".format("-"*(92 + len(VERSION)), VERSION)


def available_modules_dict():
    available_modules = dict()
    for entry_point in pkg_resources.iter_entry_points("caringcaribounext.modules"):
        nicename = str(entry_point).split("=")[0].strip()
        available_modules[nicename] = entry_point
    return available_modules


def available_modules():
    """
    Get a string showing available CaringCaribouNext modules.
    Modules are listed in setup.py: entry_points['caringcaribounext.modules']

    :return: A string listing available modules
    :rtype: str
    """
    modules = list(available_modules_dict().keys())
    modules.sort()
    mod_str = "available modules:\n  "
    mod_str += ", ".join(modules)
    return mod_str
    

def parse_arguments():
    """
    Argument parser for interface, module name and module arguments.

    :return: Namespace containing module name and arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="{0}A fork of a friendly car security exploration tool".format(fancy_header()),
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=available_modules())
    parser.add_argument("-i", dest="interface", default=None,
                        help="force interface, e.g. 'socketcan' or 'kvaser'")
    parser.add_argument("-c", dest="channel", default=None,
                        help="force channel, e.g. 'can1' or 'vcan0'")
    parser.add_argument("-b", dest="bitrate", default=None,
                        help="force bitrate, e.g. '250000' or '500000'")
    parser.add_argument("-fd", dest="fd", default=0,
                        help="CAN-FD support, 0 = False, 1 = True (default: 0)")
    parser.add_argument("-d", dest="dump", default='0',
                        help="generation of CAN dump file for further evaluation after each scan\n"
                        "Set to 1 to start dumping to file can_messages.log. (default: 0)\n")
    parser.add_argument("module",
                        help="Name of the module to run")
    parser.add_argument("module_args", metavar="...", nargs=argparse.REMAINDER,
                        help="Arguments to module")
    args = parser.parse_args()
    return args


def load_module(module_name):
    """
    Dynamically imports module_name from the folder specified by MODULES_DIR.

    :param str module_name: Name of the module to import as referenced in entry_points
                            e.g. "dcm", "uds", "listener"
    :return: a module on success, None otherwise
    """
    try:
        print("Loading module '{0}'\n".format(module_name))
        cc_mod = available_modules_dict()[module_name]
        return cc_mod
    except KeyError as e:
        print("Load module failed: module {0} is not available".format(e))
        return None
    

def main():
    """Main execution handler"""
    # Parse and validate arguments
    args = parse_arguments()
    # Show header
    show_script_header()
    # Save interface to can_actions, for use in modules
    if args.interface:
        can_actions.DEFAULT_INTERFACE = args.interface
        can_actions.DEFAULT_CHANNEL = args.channel
        can_actions.DEFAULT_BITRATE = args.bitrate
        can_actions.DEFAULT_FD = args.fd
        
        if args.dump == '1':
            # Create a list to store received CAN messages
            can_messages = []
            # Create a CAN bus instance for the listener
            bus = can.interface.Bus(channel=can_actions.DEFAULT_CHANNEL, bustype=can_actions.DEFAULT_INTERFACE)
            listener_thread = start_listener(bus, can_messages)


    try:
        # Load module
        cc_mod = load_module(args.module).load()
        cc_mod.module_main(args.module_args)
        if args.dump == '1':
            # Save the collected CAN messages to a file
            with open('can_messages.log', 'w') as file:
                for message in can_messages:
                    file.write('{0}: 0x{1:04x} {2}\n'.format(message.timestamp, message.arbitration_id, list_to_hex_str(message.data, " ")))

    except AttributeError as e:
        pass


# Main wrapper
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except can.CanError as e:
        print("\nCanError: {0}".format(e))
    except can.CanInterfaceNotImplementedError as e:
        print("An error occurred:", e)
        print("\nPlease set the interface, channel and bitrate. Use --help for help.")
    except IOError as e:
        if e.errno is errno.ENODEV:
            # Specifically catch "[Errno 19] No such device", which is caused by using an invalid interface
            print("\nIOError: {0}. This might be caused by an invalid or inactive CAN interface.".format(e))
        else:
            # Print original stack trace
            traceback.print_exc()
    finally:
        print("")
