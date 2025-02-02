from __future__ import print_function
from caringcaribounext.utils.can_actions import auto_blacklist
from caringcaribounext.utils.common import list_to_hex_str, parse_int_dec_or_hex
from caringcaribounext.utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED
from caringcaribounext.utils.constants import ARBITRATION_ID_MIN
from caringcaribounext.utils.iso15765_2 import IsoTp
from caringcaribounext.utils.iso14229_1 import Constants, Iso14229_1, NegativeResponseCodes, Services, ServiceID
from caringcaribounext.modules.uds_fuzz import seed_randomness_fuzzer, find_duplicates
from sys import stdout, version_info, stderr
import argparse
import datetime
import time

# Handle large ranges efficiently in both python 2 and 3
if version_info[0] == 2:
    range = xrange

UDS_SERVICE_NAMES = {
    0x10: "DIAGNOSTIC_SESSION_CONTROL",
    0x11: "ECU_RESET",
    0x14: "CLEAR_DIAGNOSTIC_INFORMATION",
    0x19: "READ_DTC_INFORMATION",
    0x20: "RETURN_TO_NORMAL",
    0x22: "READ_DATA_BY_IDENTIFIER",
    0x23: "READ_MEMORY_BY_ADDRESS",
    0x24: "READ_SCALING_DATA_BY_IDENTIFIER",
    0x27: "SECURITY_ACCESS",
    0x28: "COMMUNICATION_CONTROL",
    0x29: "AUTHENTICATION",
    0x2A: "READ_DATA_BY_PERIODIC_IDENTIFIER",
    0x2C: "DYNAMICALLY_DEFINE_DATA_IDENTIFIER",
    0x2D: "DEFINE_PID_BY_MEMORY_ADDRESS",
    0x2E: "WRITE_DATA_BY_IDENTIFIER",
    0x2F: "INPUT_OUTPUT_CONTROL_BY_IDENTIFIER",
    0x31: "ROUTINE_CONTROL",
    0x34: "REQUEST_DOWNLOAD",
    0x35: "REQUEST_UPLOAD",
    0x36: "TRANSFER_DATA",
    0x37: "REQUEST_TRANSFER_EXIT",
    0x38: "REQUEST_FILE_TRANSFER",
    0x3D: "WRITE_MEMORY_BY_ADDRESS",
    0x3E: "TESTER_PRESENT",
    0x7F: "NEGATIVE_RESPONSE",
    0x83: "ACCESS_TIMING_PARAMETER",
    0x84: "SECURED_DATA_TRANSMISSION",
    0x85: "CONTROL_DTC_SETTING",
    0x86: "RESPONSE_ON_EVENT",
    0x87: "LINK_CONTROL",
    0xBA: "SYSTEM_SUPPLIER_BA",
    0xBB: "SYSTEM_SUPPLIER_BB",
    0xBC: "SYSTEM_SUPPLIER_BC",
    0xBD: "SYSTEM_SUPPLIER_BD",
    0xBE: "SYSTEM_SUPPLIER_BE",
}

NRC_NAMES = {
    0x00: "POSITIVE_RESPONSE",
    0x10: "GENERAL_REJECT",
    0x11: "SERVICE_NOT_SUPPORTED",
    0x12: "SUB_FUNCTION_NOT_SUPPORTED",
    0x13: "INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT",
    0x14: "RESPONSE_TOO_LONG",
    0x21: "BUSY_REPEAT_REQUEST",
    0x22: "CONDITIONS_NOT_CORRECT",
    0x24: "REQUEST_SEQUENCE_ERROR",
    0x25: "NO_RESPONSE_FROM_SUBNET_COMPONENT",
    0x26: "FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION",
    0x31: "REQUEST_OUT_OF_RANGE",
    0x33: "SECURITY_ACCESS_DENIED",
    0x34: "AUTHENTICATION_REQUIRED",
    0x35: "INVALID_KEY",
    0x36: "EXCEEDED_NUMBER_OF_ATTEMPTS",
    0x37: "REQUIRED_TIME_DELAY_NOT_EXPIRED",
    0x70: "UPLOAD_DOWNLOAD_NOT_ACCEPTED",
    0x71: "TRANSFER_DATA_SUSPENDED",
    0x72: "GENERAL_PROGRAMMING_FAILURE",
    0x73: "WRONG_BLOCK_SEQUENCE_COUNTER",
    0x78: "REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING",
    0x7E: "SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION",
    0x7F: "SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION",
    0x81: "RPM_TOO_HIGH",
    0x82: "RPM_TOO_LOW",
    0x83: "ENGINE_IS_RUNNING",
    0x84: "ENGINE_IS_NOT_RUNNING",
    0x85: "ENGINE_RUN_TIME_TOO_LOW",
    0x86: "TEMPERATURE_TOO_HIGH",
    0x87: "TEMPERATURE_TOO_LOW",
    0x88: "VEHICLE_SPEED_TOO_HIGH",
    0x89: "VEHICLE_SPEED_TOO_LOW",
    0x8A: "THROTTLE_PEDAL_TOO_HIGH",
    0x8B: "THROTTLE_PEDAL_TOO_LOW",
    0x8C: "TRANSMISSION_RANGE_NOT_IN_NEUTRAL",
    0x8D: "TRANSMISSION_RANGE_NOT_IN_GEAR",
    0x8F: "BRAKE_SWITCHES_NOT_CLOSED",
    0x90: "SHIFT_LEVER_NOT_IN_PARK",
    0x91: "TORQUE_CONVERTER_CLUTCH_LOCKED",
    0x92: "VOLTAGE_TOO_HIGH",
    0x93: "VOLTAGE_TOO_LOW"
}

DELAY_DISCOVERY = 0.01
DELAY_TESTER_PRESENT = 0.5
DELAY_SECSEED_RESET = 0.01
TIMEOUT_SERVICES = 0.2
TIMEOUT_SUBSERVICES = 0.02

# Max number of arbitration IDs to backtrack during verification
VERIFICATION_BACKTRACK = 5
# Extra time in seconds to wait for responses during verification
VERIFICATION_EXTRA_DELAY = 0.5

BYTE_MIN = 0x00
BYTE_MAX = 0xFF

DUMP_DID_MIN = 0x0000
DUMP_DID_MAX = 0xFFFF
DUMP_DID_TIMEOUT = 0.2

DUMP_ROUTINE_MIN = 0x0000
DUMP_ROUTINE_MAX = 0xFFFF
DUMP_ROUTINE_TIMEOUT = 0.1

MEM_START_ADDR = 0
MEM_LEN = 1
MEM_SIZE = 1
ADDR_BYTE_SIZE = 2
MEM_LEN_BYTE_SIZE = 1
SESSION_TYPE = 3

PADDING_DEFAULT = 0x00

PADDING = []
NP = [0]

REPORT = 0
DOCUMENT = 0


def uds_discovery(min_id, max_id, blacklist_args, auto_blacklist_duration,
                  delay, verify, print_results=True):
    """Scans for diagnostics support by brute forcing session control
        messages to different arbitration IDs.

    Returns a list of all (client_arb_id, server_arb_id) pairs found.

    :param min_id: start arbitration ID value
    :param max_id: end arbitration ID value
    :param blacklist_args: blacklist for arbitration ID values
    :param auto_blacklist_duration: seconds to scan for interfering
      arbitration IDs to blacklist automatically
    :param delay: delay between each message
    :param verify: whether found arbitration IDs should be verified
    :param print_results: whether results should be printed to stdout
    :type min_id: int
    :type max_id: int
    :type blacklist_args: [int]
    :type auto_blacklist_duration: float
    :type delay: float
    :type verify: bool
    :type print_results: bool
    :return: list of (client_arbitration_id, server_arbitration_id) pairs
    :rtype [(int, int)]
    """
    # Set defaults
    if min_id is None:
        min_id = ARBITRATION_ID_MIN
    if max_id is None:
        if min_id <= ARBITRATION_ID_MAX:
            max_id = ARBITRATION_ID_MAX
        else:
            # If min_id is extended, use an extended default max_id as well
            max_id = ARBITRATION_ID_MAX_EXTENDED
    if auto_blacklist_duration is None:
        auto_blacklist_duration = 0
    if blacklist_args is None:
        blacklist_args = []

    # Sanity checks
    if max_id < min_id:
        raise ValueError("max_id must not be smaller than min_id -"
                         " got min:0x{0:x}, max:0x{1:x}".format(min_id, max_id))
    if auto_blacklist_duration < 0:
        raise ValueError("auto_blacklist_duration must not be smaller "
                         "than 0, got {0}'".format(auto_blacklist_duration))

    diagnostic_session_control = Services.DiagnosticSessionControl
    service_id = diagnostic_session_control.service_id
    sub_function = diagnostic_session_control.DiagnosticSessionType.DEFAULT_SESSION
    session_control_data = [service_id, sub_function]

    valid_session_control_responses = [0x50, 0x7F]

    def is_valid_response(message):
        return (len(message.data) >= 2 and
                message.data[1] in valid_session_control_responses)

    found_arbitration_ids = []

    with IsoTp(None, None) as tp:

        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        blacklist = set(blacklist_args)

        # Perform automatic blacklist scan
        if auto_blacklist_duration > 0:
            auto_bl_arb_ids = auto_blacklist(tp.bus,
                                             auto_blacklist_duration,
                                             is_valid_response,
                                             print_results)
            blacklist |= auto_bl_arb_ids

        # Prepare session control frame
        sess_ctrl_frm = tp.get_frames_from_message(session_control_data)
        send_arb_id = min_id - 1
        while send_arb_id < max_id:
            send_arb_id += 1
            if print_results:
                print("\rSending Diagnostic Session Control to 0x{0:04x}"
                      .format(send_arb_id), end="")
                stdout.flush()
            # Send Diagnostic Session Control
            tp.transmit(sess_ctrl_frm, send_arb_id, None)
            end_time = time.time() + delay
            # Listen for response
            while time.time() < end_time:
                msg = tp.bus.recv(0)
                if msg is None:
                    # No response received
                    continue
                if msg.arbitration_id in blacklist:
                    # Ignore blacklisted arbitration IDs
                    continue
                if is_valid_response(msg):
                    # Valid response
                    if verify:
                        # Verification - backtrack the latest IDs and
                        # verify that the same response is received
                        verified = False
                        # Set filter to only receive messages for the
                        # arbitration ID being verified
                        tp.set_filter_single_arbitration_id(msg.arbitration_id)
                        if print_results:
                            print("\n  Verifying potential response from "
                                  "0x{0:04x}".format(send_arb_id))
                        verify_id_range = range(send_arb_id,
                                                send_arb_id - VERIFICATION_BACKTRACK,
                                                -1)
                        for verify_arb_id in verify_id_range:
                            if print_results:
                                print("    Resending 0x{0:0x}... "
                                      .format(verify_arb_id), end=" ")
                            tp.transmit(sess_ctrl_frm,
                                        verify_arb_id,
                                        None)
                            # Give some extra time for verification, in
                            # case of slow responses
                            verification_end_time = (time.time()
                                                     + delay
                                                     + VERIFICATION_EXTRA_DELAY)
                            while time.time() < verification_end_time:
                                verification_msg = tp.bus.recv(0)
                                if verification_msg is None:
                                    continue
                                if is_valid_response(verification_msg):
                                    # Verified
                                    verified = True
                                    # Update send ID - if server responds
                                    # slowly, initial value may be faulty.
                                    # Also ensures we resume searching on
                                    # the next arb ID after the actual
                                    # match, rather than the one after the
                                    # last potential match (which could lead
                                    # to false negatives if multiple servers
                                    # listen to adjacent arbitration IDs and
                                    # respond slowly)
                                    send_arb_id = verify_arb_id
                                    break
                            if print_results:
                                # Print result
                                if verified:
                                    print("Success")
                                else:
                                    print("No response")
                            if verified:
                                # Verification succeeded - stop checking
                                break
                        # Remove filter after verification
                        tp.clear_filters()
                        if not verified:
                            # Verification failed - move on
                            if print_results:
                                print("  False match - skipping")
                            continue
                    if print_results:
                        if not verify:
                            # Blank line needed
                            print()
                        print("Found diagnostics server "
                              "listening at 0x{0:04x}, "
                              "response at 0x{1:04x}"
                              .format(send_arb_id, msg.arbitration_id))
                    # Add found arbitration ID pair
                    found_arb_id_pair = (send_arb_id,
                                         msg.arbitration_id)
                    found_arbitration_ids.append(found_arb_id_pair)
        if print_results:
            print()
    return found_arbitration_ids


def __uds_discovery_wrapper(args):
    """Wrapper used to initiate a UDS discovery scan"""
    min_id = args.min
    max_id = args.max
    blacklist = args.blacklist
    auto_blacklist_duration = args.autoblacklist
    delay = args.delay
    verify = not args.skipverify
    print_results = True
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    try:
        arb_id_pairs = uds_discovery(min_id, max_id, blacklist,
                                     auto_blacklist_duration,
                                     delay, verify, print_results)
        if len(arb_id_pairs) == 0:
            # No UDS discovered
            print("\nDiagnostics service could not be found.")
        else:
            # Print result table
            print("\nIdentified diagnostics:\n")
            table_line = "+------------+------------+"
            print(table_line)
            print("| CLIENT ID  | SERVER ID  |")
            print(table_line)
            for (client_id, server_id) in arb_id_pairs:
                print("| 0x{0:08x} | 0x{1:08x} |"
                      .format(client_id, server_id))
            print(table_line)
    except ValueError as e:
        print("Discovery failed: {0}".format(e))


def service_discovery(arb_id_request, arb_id_response, timeout,
                      min_id=BYTE_MIN, max_id=BYTE_MAX, print_results=True):
    """Scans for supported UDS services on the specified arbitration ID.
       Returns a list of found service IDs.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: delay between each request sent
    :param min_id: first service ID to scan
    :param max_id: last service ID to scan
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float
    :type min_id: int
    :type max_id: int
    :type print_results: bool
    :return: list of supported service IDs
    :rtype [int]
    """
    found_services = []

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        # Send requests
        try:
            for service_id in range(min_id, max_id + 1):
                tp.send_request([service_id])
                if print_results:
                    print("\rProbing service 0x{0:02x} ({0}/{1}): found {2}"
                          .format(service_id, max_id, len(found_services)),
                          end="")
                stdout.flush()
                # Get response
                msg = tp.bus.recv(timeout)
                if msg is None:
                    # No response received
                    continue
                # Parse response
                if len(msg.data) > 3:
                    # Since service ID is included in the response, mapping is correct even if response is delayed
                    response_id = msg.data[1]
                    response_service_id = msg.data[2]
                    status = msg.data[3]
                    if response_id != Constants.NR_SI:
                        request_id = Iso14229_1.get_service_request_id(response_id)
                        found_services.append(request_id)
                    elif status != NegativeResponseCodes.SERVICE_NOT_SUPPORTED:
                        # Any other response than "service not supported" counts
                        found_services.append(response_service_id)
            if print_results:
                print("\nDone!\n")
        except KeyboardInterrupt:
            if print_results:
                print("\nInterrupted by user!\n")
    return found_services


def __service_discovery_wrapper(args):
    """Wrapper used to initiate a service discovery scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    # Probe services
    found_services = service_discovery(arb_id_request,
                                       arb_id_response, timeout)
    # Print results
    for service_id in found_services:
        service_name = UDS_SERVICE_NAMES.get(service_id, "Unknown service")
        print("Supported service 0x{0:02x}: {1}"
              .format(service_id, service_name))


def sub_discovery(arb_id_request, arb_id_response, diagnostic, service, timeout, print_results=True):
    """Scans for supported UDS Diagnostic Session Control subservices on the specified arbitration ID.
       Returns a list of found Diagnostic Session Control subservice IDs.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: delay between each request sent
    :param diagnostic: the diagnostic session control subfunction in which the target service is accessible
    :param service: the target service to be enumerated
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float
    :type diagnostic: int
    :type service: int
    :type print_results: bool
    :return: list of supported service IDs
    :rtype [int]
    """
    found_subservices = []
    subservice_status = []

    try:
        for i in range(0, 256):

            if service != Services.DiagnosticSessionControl:
                raw_send(arb_id_request, arb_id_response, ServiceID.DIAGNOSTIC_SESSION_CONTROL, diagnostic)
            else:
                raw_send(arb_id_request, arb_id_response, ServiceID.DIAGNOSTIC_SESSION_CONTROL, 1)

            time.sleep(0.1)

            response = raw_send(arb_id_request, arb_id_response, service, i)

            service_name = UDS_SERVICE_NAMES.get(service, "Unknown service")

            print("\rProbing sub-service ID 0x{0:02x} for service {1} (0x{2:02x}).".format(i, service_name, service),
                  end="")

            if response is None:
                # No response received
                continue

            # Parse response
            if len(response) >= 2:
                response_id = response[0]
                response_service_id = response[1]
                if len(response) >= 3:
                    status = response[2]
                else:
                    status = None
                if Iso14229_1.is_positive_response(response):
                    found_subservices.append(i)
                    subservice_status.append(0x00)
                elif response_id == Constants.NR_SI and response_service_id == service and status != NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED:
                    # Any other response than "service not supported" counts
                    found_subservices.append(i)
                    subservice_status.append(response_service_id)

            time.sleep(timeout)

    except KeyboardInterrupt:
        if print_results:
            print("\nInterrupted by user!\n")
    return found_subservices, subservice_status


def __sub_discovery_wrapper(args):
    """Wrapper used to initiate a subservice discovery scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    diagnostic = args.dsc
    service = args.service
    timeout = args.timeout
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    # Probe subservices
    found_subservices, subservice_status = sub_discovery(arb_id_request,
                                                         arb_id_response, diagnostic, service, timeout)

    service_name = UDS_SERVICE_NAMES.get(service, "Unknown service")
    
    # Print results
    if len(found_subservices) == 0:
        print("\nNo Sub-Services were discovered for service {0:02x} - {1}.\n".format(service, service_name, end=' '))
    else:
        print("\nSub-Services Discovered for Service {0:02x} - {1}:\n".format(service, service_name, end=' '))
        for subservice_id in found_subservices:
            nrc_description = NRC_NAMES.get(subservice_status[found_subservices.index(subservice_id)])
            print("\n0x{0:02x} : {1}".format(subservice_id, nrc_description), end=' ')


def raw_send(arb_id_request, arb_id_response, service, session_type):
    """Helper function to initate raw message send when needed, instead of extended_session"""

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        request = [0] * 2
        request[0] = service
        request[1] = session_type

        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            tp.send_request(request)
            response = uds.receive_response(Iso14229_1.P3_CLIENT)
            return response


def padding_set(padding, no_padding):
    """Helper function to set the needed padding for the target scan/message"""
    if no_padding == True:
        NP[0] = 1

    PADDING.append(padding)


def tester_present(arb_id_request, delay, duration,
                   suppress_positive_response):
    """Sends TesterPresent messages to 'arb_id_request'. Stops automatically
    after 'duration' seconds or runs forever if this is None.

    :param arb_id_request: arbitration ID for requests
    :param delay: seconds between each request
    :param duration: seconds before automatically stopping, or None to
                     continue forever
    :param suppress_positive_response: whether positive responses should
                                       be suppressed
    :type arb_id_request: int
    :type delay: float
    :type duration: float or None
    :type suppress_positive_response: bool
    """
    # SPR simply tells the recipient not to send a positive response to
    # each TesterPresent message
    if suppress_positive_response:
        sub_function = 0x80
    else:
        sub_function = 0x00

    # Calculate end timestamp if the TesterPresent should automatically
    # stop after a given duration
    auto_stop = duration is not None
    end_time = None
    if auto_stop:
        end_time = (datetime.datetime.now()
                    + datetime.timedelta(seconds=duration))

    service_id = Services.TesterPresent.service_id
    message_data = [service_id, sub_function]
    print("Sending TesterPresent to arbitration ID {0} (0x{0:02x})"
          .format(arb_id_request))
    print("\nPress Ctrl+C to stop\n")
    with IsoTp(arb_id_request, None) as can_wrap:

        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        counter = 1
        while True:
            can_wrap.send_request(message_data)
            print("\rCounter:", counter, end="")
            stdout.flush()
            time.sleep(delay)
            counter += 1
            if auto_stop and datetime.datetime.now() >= end_time:
                break


def __tester_present_wrapper(args):
    """Wrapper used to initiate a TesterPresent session"""
    arb_id_request = args.src
    delay = args.delay
    duration = args.duration
    suppress_positive_response = args.spr
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    tester_present(arb_id_request, delay, duration,
                   suppress_positive_response)


def ecu_reset(arb_id_request, arb_id_response, reset_type, timeout):
    """Sends an ECU Reset message to 'arb_id_request'. Returns the first
        response received from 'arb_id_response' within 'timeout' seconds
        or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param reset_type: value corresponding to a reset type
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response int
    :type reset_type: int
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if not BYTE_MIN <= reset_type <= BYTE_MAX:
        raise ValueError("reset type must be within interval "
                         "0x{0:02x}-0x{1:02x}"
                         .format(BYTE_MIN, BYTE_MAX))
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("timeout value ({0}) cannot be negative"
                         .format(timeout))

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.ecu_reset(reset_type=reset_type)
            return response


def __ecu_reset_wrapper(args):
    """Wrapper used to initiate ECU Reset"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset_type
    timeout = args.timeout
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    print("Sending ECU reset, type 0x{0:02x} to arbitration ID {1} "
          "(0x{1:02x})".format(reset_type, arb_id_request))
    try:
        response = ecu_reset(arb_id_request, arb_id_response,
                             reset_type, timeout)
    except ValueError as e:
        print("ValueError: {0}".format(e))
        return

    # Decode response
    if response is None:
        print("No response was received")
    else:
        response_length = len(response)
        if response_length == 0:
            # Empty response
            print("Received empty response")
        elif response_length == 1:
            # Invalid response length
            print("Received response [{0:02x}] (1 byte), expected at least "
                  "2 bytes".format(response[0], len(response)))
        elif Iso14229_1.is_positive_response(response):
            # Positive response handling
            response_service_id = response[0]
            subfunction = response[1]
            expected_response_id = \
                Iso14229_1.get_service_response_id(
                    Services.EcuReset.service_id)
            if (response_service_id == expected_response_id
                    and subfunction == reset_type):
                # Positive response
                pos_msg = "Received positive response"
                if response_length > 2:
                    # Additional data can be seconds left to reset
                    # (powerDownTime) or manufacturer specific
                    additional_data = list_to_hex_str(response[2:], ",")
                    pos_msg += (" with additional data: [{0}]"
                                .format(additional_data))
                print(pos_msg)
            else:
                # Service and/or subfunction mismatch
                print("Response service ID 0x{0:02x} and subfunction "
                      "0x{1:02x} do not match expected values 0x{2:02x} "
                      "and 0x{3:02x}".format(response_service_id,
                                             subfunction,
                                             Services.EcuReset.service_id,
                                             reset_type))
        else:
            # Negative response handling
            print_negative_response(response)


def print_negative_response(response):
    """
    Helper function for decoding and printing a negative response received
    from a UDS server.

    :param response: Response data after CAN-TP layer has been removed
    :type response: [int]

    :return: Nothing
    """
    nrc = response[2]
    nrc_description = NRC_NAMES.get(nrc, "Unknown NRC value")
    print("Received negative response code (NRC) 0x{0:02x}: {1}"
          .format(nrc, nrc_description))


def __security_seed_wrapper(args):
    """Wrapper used to initiate security seed dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset
    session_type = args.sess_type
    level = args.sec_level
    num_seeds = args.num
    reset_delay = args.delay
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    seed_list = []
    try:
        print("Security seed dump started. Press Ctrl+C to stop.\n")
        while num_seeds > len(seed_list) or num_seeds == 0:
            # Extended diagnostics
            response = extended_session(arb_id_request,
                                        arb_id_response,
                                        session_type)
            if not Iso14229_1.is_positive_response(response):
                print("Unable to enter extended session. Retrying...\n")
                continue

            # Request seed
            response = request_seed(arb_id_request, arb_id_response,
                                    level, None, None)
            if response is None:
                print("\nInvalid response")
            elif Iso14229_1.is_positive_response(response):
                seed_list.append(list_to_hex_str(response[2:]))
                print("Seed received: {}\t(Total captured: {})"
                      .format(list_to_hex_str(response[2:]),
                              len(seed_list)), end="\r")
                stdout.flush()
            else:
                print_negative_response(response)
                break
            if reset_type:
                ecu_reset(arb_id_request, arb_id_response, reset_type, None)
                time.sleep(reset_delay)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except ValueError as e:
        print(e)
        return

    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds captured:")
        for seed in seed_list:
            print(seed)


def extended_session(arb_id_request, arb_id_response, session_type):
    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            response = uds.diagnostic_session_control(session_type)
            return response


def request_seed(arb_id_request, arb_id_response, level,
                 data_record, timeout):
    """Sends an Request seed message to 'arb_id_request'. Returns the
       first response received from 'arb_id_response' within 'timeout'
       seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param level: vehicle manufacturer specific access level to request
                  seed for
    :param data_record: optional vehicle manufacturer specific data to
                        transmit when requesting seed
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response: int
    :type level: int
    :type data_record: [int] or None
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if (not Services.SecurityAccess.RequestSeedOrSendKey()
            .is_valid_request_seed_level(level)):
        raise ValueError("Invalid request seed level")
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("Timeout value ({0}) cannot be negative"
                         .format(timeout))

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.security_access_request_seed(level, data_record)
            return response


def send_key(arb_id_request, arb_id_response, level, key, timeout):
    """
    Sends a Send key message to 'arb_id_request'.
    Returns the first response received from 'arb_id_response' within
    'timeout' seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param level: vehicle manufacturer specific access level to send key for
    :param key: key to transmit
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response: int
    :type level: int
    :type key: [int]
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if (not Services.SecurityAccess.RequestSeedOrSendKey()
            .is_valid_send_key_level(level)):
        raise ValueError("Invalid send key level")
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("Timeout value ({0}) cannot be negative"
                         .format(timeout))

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.security_access_send_key(level=level, key=key)
            return response


def __dump_dids_wrapper(args):
    """Wrapper used to initiate data identifier dump"""
    diagnostic = args.dsc
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    min_did = args.min_did
    max_did = args.max_did
    print_results = True
    padding = args.padding
    no_padding = args.no_padding
    reporting = args.reporting

    if reporting == 1:
        global DOCUMENT
        DOCUMENT = 1
        f = open("ccn_uds_did.txt", "w")
        f.write("Caring Caribou Next UDS DID Module\n\n\n")
        f.close()


    padding_set(padding, no_padding)

    dump_dids(arb_id_request, arb_id_response, timeout, reporting, diagnostic, min_did, max_did,
              print_results)


def report_print(text):
    """Helper function to create a .txt report with the contents of the applicable scan"""

    # Check if report is requested
    if REPORT == 1:   
        # print the supplied text 
        print(text)
        # write text to applicable file
        if DOCUMENT == 0:
            report = open("ccn_uds_auto_report.txt", "a")
            report.write(text)
            report.write("\n")
            report.close()
        elif DOCUMENT == 1:
            report = open("ccn_uds_did.txt", "a")
            report.write(text)
            report.write("\n")
            report.close()
        elif DOCUMENT == 2:
            report = open("ccn_uds_wdid.txt", "a")
            report.write(text)
            report.write("\n")
            report.close()
    else:
        print(text)
    

def __auto_wrapper(args):
    """Wrapper used to initiate automated UDS scan"""
    min_id = args.min
    max_id = args.max
    blacklist = args.blacklist
    auto_blacklist_duration = args.autoblacklist
    delay = args.delay
    verify = not args.skipverify
    print_results = True
    timeout = args.timeout
    min_did = args.min_did
    max_did = args.max_did
    min_routine = args.min_routine
    max_routine = args.max_routine
    padding = args.padding
    no_padding = args.no_padding
    reporting = args.reporting

    padding_set(padding, no_padding)

    # set reporting functionality and create file
    if reporting == 1:
        global REPORT
        REPORT = 1
        global DOCUMENT
        DOCUMENT = 0
        f = open("ccn_uds_auto_report.txt", "w")
        f.write("Caring Caribou Next UDS Auto Module Report\n\n\n")
        f.close()

    try:
        # Perform UDS discovery
        arb_id_pairs = uds_discovery(min_id, max_id, blacklist,
                                     auto_blacklist_duration,
                                     delay, verify, print_results)

        print("\n")
        if len(arb_id_pairs) == 0:
            # No UDS discovered
            report_print("\nDiagnostics service could not be found.")
        else:

            # Print result table of discovered diagnostics
            report_print("\nIdentified diagnostics:\n")
            table_line = "+------------+------------+"
            report_print(table_line)
            report_print("| CLIENT ID  | SERVER ID  |")
            report_print(table_line)
            for (client_id, server_id) in arb_id_pairs:
                report_print("| 0x{0:08x} | 0x{1:08x} |"
                      .format(client_id, server_id))
            report_print(table_line)
            report_print("\n")

            # Enumerate each pair
            for (client_id, server_id) in arb_id_pairs:

                args.src = client_id
                args.dst = server_id

                diag_line = "-" * 100
                report_print(diag_line)

                # Print Client/Server result table
                report_print("\nTarget Diagnostic IDs:\n")
                table_line = "+------------+------------+"
                report_print(table_line)
                report_print("| CLIENT ID  | SERVER ID  |")
                report_print(table_line)
                report_print("| 0x{0:08x} | 0x{1:08x} |"
                      .format(client_id, server_id))
                report_print(table_line)

                print("\nEnumerating Services:\n")

                # Enumerate services
                found_services = service_discovery(client_id, server_id, timeout)
                found_subservices = []

                report_print("\nIdentified services:\n")

                # Print available services result table
                for service_id in found_services:
                    service_name = UDS_SERVICE_NAMES.get(service_id, "Unknown service")
                    report_print("Supported service 0x{0:02x}: {1}"
                          .format(service_id, service_name))

                report_print("\n")

                # Enumerate service 0x22 READ_DATA_BY_IDENTIFIER
                if ServiceID.READ_DATA_BY_IDENTIFIER in found_services:
                    try:
                        dump_dids(client_id, server_id, timeout, reporting, min_did, max_did, print_results)
                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

                # Enumerate service 0x10 DIAGNOSTIC_SESSION_CONTROL
                if ServiceID.DIAGNOSTIC_SESSION_CONTROL in found_services:
                    
                    try:
                        print("\nEnumerating Diagnostic Session Control Service:\n")

                        found_subservices = []
                        subservice_status = []

                        for i in range(1, 256):

                            extended_session(client_id, server_id, 1)

                            response = extended_session(client_id, server_id, i)

                            print("\rProbing diagnostic session control sub-service 0x{0:02x}".format(i), end="")

                            if response is None:
                                # No response received
                                continue

                            # Parse response
                            if len(response) >= 3:
                                response_id = response[0]
                                response_service_id = response[1]
                                status = response[2]
                                if Iso14229_1.is_positive_response(response):
                                    found_subservices.append(i)
                                    subservice_status.append(0x00)
                                elif response_id == Constants.NR_SI and response_service_id == 0x10 and status != NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED:
                                    # Any other response than "service not supported" counts
                                    found_subservices.append(i)
                                    subservice_status.append(response_service_id)

                            time.sleep(timeout)
                    
                        # Print results
                        if len(found_subservices) == 0:
                            report_print("\nNo Diagnostic Session Control Sub-Services were discovered\n")
                        else:
                            report_print("\n")
                            report_print("\nDiscovered Diagnostic Session Control Sub-Services:\n")
                            for subservice_id in found_subservices:
                                nrc_description = NRC_NAMES.get(subservice_status[found_subservices.index(subservice_id)])
                                report_print("\n0x{0:02x} : {1}".format(subservice_id, nrc_description))
                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

                # Enumerate service 0x31 ROUTINE_CONTROL
                if ServiceID.ROUTINE_CONTROL in found_services:
                    try:
                        for subservice_id in found_subservices:
                            subfunction = parse_int_dec_or_hex('0x03')
                            extended_session(client_id, server_id, 1)
                            routine_control_dump(client_id, server_id, timeout, subservice_id, subfunction, min_routine, max_routine)
                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

                # Enumerate service 0x23 WRITE_DATA_BY_IDENTIFIER
                if ServiceID.WRITE_DATA_BY_IDENTIFIER in found_services:
                    try:
                        for subservice_id in found_subservices:
                            print("\n")
                            print("\rProbing service 0x2E under diagnostic session control sub-service 0x{0:02x}".format(subservice_id), end="")
                            print("\n")
                            # diagnostic = parse_int_dec_or_hex(int(subservice_id))
                            try:
                                write_dids(subservice_id, client_id, server_id, timeout, reporting, min_did, max_did, print_results)
                            except ValueError:
                                print("\nNegative response, switching to next Diagnostic Session.\n")
                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

                # Enumerate service 0x11 ECU_RESET
                if ServiceID.ECU_RESET in found_services:
                    
                    try:
                        report_print("\n")
                        print("\nEnumerating ECUReset Service:\n")

                        found_subservices = []
                        subservice_status = []

                        for i in range(1, 5):

                            extended_session(client_id, server_id, 3)

                            response = raw_send(client_id, server_id, 17, i)

                            print("\rProbing ECUReset sub-service 0x{0:02x}".format(i), end="")

                            if response is None:
                                # No response received
                                continue

                            # Parse response
                            if len(response) >= 2:
                                response_id = response[0]
                                response_service_id = response[1]
                                if len(response) >= 3:
                                    status = response[2]
                                else:
                                    status = None
                                if Iso14229_1.is_positive_response(response):
                                    found_subservices.append(i)
                                    subservice_status.append(0x00)
                                elif response_id == Constants.NR_SI and response_service_id == 0x11 and status != NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED:
                                    # Any other response than "service not supported" counts
                                    found_subservices.append(i)
                                    subservice_status.append(response_service_id)

                            time.sleep(timeout)

                        # Print results
                        if len(found_subservices) == 0:
                            report_print("\nNo ECUReset Sub-Services were discovered.\n")
                        else:
                            report_print("\n")
                            report_print("\nDiscovered ECUReset Sub-Services:\n")
                            for subservice_id in found_subservices:
                                nrc_description = NRC_NAMES.get(subservice_status[found_subservices.index(subservice_id)])
                                report_print("\n0x{0:02x} : {1}".format(subservice_id, nrc_description))
                    
                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

                # Enumerate service 0x27 SECURITY_ACCESS
                if ServiceID.SECURITY_ACCESS in found_services:

                    try:

                        found_subdiag = []
                        found_subsec = []
                        report_print("\n")
                        for subservice_id in found_subservices:
                            for level in range(1, 256):
                                print(
                                    "\rProbing security access sub-service 0x{0:02x} in diagnostic session 0x{1:02x}.".format(
                                        level, subservice_id), end=" ")
                                extended_session(client_id, server_id, 1)
                                extended_session(client_id, server_id, subservice_id)
                                response = raw_send(client_id, server_id, 39, level)

                                if response is None:
                                    continue
                                elif Iso14229_1.is_positive_response(response):
                                    found_subdiag.append(subservice_id)
                                    found_subsec.append(level)
                        if len(found_subsec) == 0:
                            report_print("\nNo Security Access Sub-Services were discovered.\n")
                        else:
                            report_print("\n")
                            report_print("\nDiscovered Security Access Sub Services:\n")
                            report_print("\n")
                            table_line_sec = "+----------------------+-------------------+"
                            report_print(table_line_sec)
                            report_print("|  Diagnostic Session  |  Security Access  |")
                            report_print(table_line_sec)
                            for counter in range(len(found_subsec)):
                                diag = found_subdiag[counter]
                                sec = found_subsec[counter]
                                report_print("|         0x{0:02x}         |         0x{1:02x}      |"
                                    .format(diag, sec))
                                counter += 1
                            report_print(table_line_sec)

                            # Evaluate the Seed Randomness 
                            if input("Do you want to perform seed randomness evaluation with uds_fuzz module? (y/n)") == "y":
                                for counter in range(len(found_subsec)):
                                    diag = found_subdiag[counter]
                                    sec = found_subsec[counter]
                                    report_print("\n")
                                    report_print("\nTarget Security Access Subservice:\n")
                                    report_print("\n")
                                    table_line_sec = "+----------------------+-------------------+"
                                    report_print(table_line_sec)
                                    report_print("|  Diagnostic Session  |  Security Access  |")
                                    report_print(table_line_sec)
                                    for counter in range(len(found_subsec)):
                                        diag = found_subdiag[counter]
                                        sec = found_subsec[counter]
                                        report_print("|         0x{0:02x}         |         0x{1:02x}      |"
                                            .format(diag, sec))
                                        counter += 1
                                    report_print(table_line_sec)
                                    if ServiceID.ECU_RESET in found_services:
                                        reset_type = parse_int_dec_or_hex('1')
                                        session_type = "10{0:02x}27{1:02x}".format(diag, sec)
                                        iterations = parse_int_dec_or_hex('100')
                                        reset_delay = 3.901
                                        reset_method = parse_int_dec_or_hex('1')
                                        inter = 0.1
                                        seed_list = seed_randomness_fuzzer(client_id, server_id, reset_type, session_type, iterations, reset_delay, reset_method, inter, padding, no_padding)
                                        # Print captured seeds and found duplicates
                                        if len(seed_list) > 0:
                                            print("\n")
                                            report_print("\nDuplicates discovered: \n")
                                            report_print(find_duplicates(seed_list))
                                            report_print("\n")
                                        else:
                                            report_print("\nNo Duplicates Found in 100 itterations. Consider manual investigation. \n")
                                            report_print("\n")
                                    else:
                                        print("ECUReset service not available. Skipping Seed Randomness evaluation.")

                    except KeyboardInterrupt:
                        print("Current test interrupted by user.")

    except ValueError as e:
        report_print("\nDiscovery failed: {0}".format(e))


def dump_dids(arb_id_request, arb_id_response, timeout, reporting, diagnostic, 
              min_did=DUMP_DID_MIN, max_did=DUMP_DID_MAX, print_results=True):
    """
    Sends read data by identifier (DID) messages to 'arb_id_request'.
    Returns a list of positive responses received from 'arb_id_response' within
    'timeout' seconds or an empty list if no positive responses were received.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :param min_did: minimum device identifier to read
    :param max_did: maximum device identifier to read
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float or None
    :type min_did: int
    :type max_did: int
    :type print_results: bool
    :return: list of tuples containing DID and response bytes on success,
             empty list if no responses
    :rtype [(int, [int])] or []
    """

    try:
        # Sanity checks
        if isinstance(timeout, float) and timeout < 0.0:
            raise ValueError("Timeout value ({0}) cannot be negative"
                            .format(timeout))

        if max_did < min_did:
            raise ValueError("max_did must not be smaller than min_did -"
                            " got min:0x{0:x}, max:0x{1:x}".format(min_did, max_did))

        if reporting == 1:
            global REPORT
            REPORT = 1

        response_diag = extended_session(arb_id_request, arb_id_response, diagnostic)
        if not Iso14229_1.is_positive_response(response_diag):
            raise ValueError("Supplied Diagnostic Session Control subservice results in Negative Response")
        
        responses = []
        with IsoTp(arb_id_request=arb_id_request,
                arb_id_response=arb_id_response) as tp:
            
            IsoTp.NP[0] = NP[0]
            IsoTp.PADDING[0] = PADDING[0]

            # Setup filter for incoming messages
            tp.set_filter_single_arbitration_id(arb_id_response)
            with Iso14229_1(tp) as uds:
                # Set timeout
                if timeout is not None:
                    uds.P3_CLIENT = timeout

                if print_results:
                    print('Dumping DIDs in range 0x{:04x}-0x{:04x}\n'.format(
                        min_did, max_did))
                    report_print('Identified DIDs:')
                    report_print('DID    Value (hex)')
                for identifier in range(min_did, max_did + 1):
                    print(f'Current DID: 0x{identifier:04x}', end='\r', file=stderr)
                    response = uds.read_data_by_identifier(identifier=[identifier])

                    # Only keep positive responses
                    if response and Iso14229_1.is_positive_response(response):
                        # sometimes there are other modules reading DIDs at the same time
                        # try to filter out extranous DID reads by comparing the value
                        if identifier != int(list_to_hex_str(response[1:3]), 16):
                            continue
                        
                        responses.append((identifier, response))
                        if print_results:
                            did = '0x{:04x}'.format(identifier), list_to_hex_str(response[3:])
                            report_print(str(did))

                if print_results:
                    print("\nDone!")
                    print("\033[K", file=stderr) # clear line
                    report_print("\n")
                return responses
            
    except KeyboardInterrupt:
        print("\033[K", file=stderr) # clear line
        print("Interrupted by user.\n")
        return responses
    except ValueError as e:
        print(e)
        return


def __dump_mem_wrapper(args):
    """Wrapper used to initiate data memory dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    start_addr = args.start_addr
    mem_length = args.mem_length
    mem_size = args.mem_size
    address_byte_size = args.address_byte_size
    memory_length_byte_size = args.memory_length_byte_size
    session_type = args.sess_type
    print_results = True
    padding = args.padding
    no_padding = args.no_padding
    

    padding_set(padding, no_padding)

    dump_memory(arb_id_request, arb_id_response, timeout, start_addr, mem_length, mem_size, address_byte_size,
                memory_length_byte_size, session_type, print_results)
    
def dump_memory(arb_id_request, arb_id_response, timeout,
                start_addr=MEM_START_ADDR, mem_length=MEM_LEN, mem_size=MEM_SIZE, address_byte_size=ADDR_BYTE_SIZE,
                memory_length_byte_size=MEM_LEN_BYTE_SIZE, session_type=3, print_results=True):
    """
    Sends read memory by address messages to 'arb_id_request'.
    Returns a memory dump received from 'arb_id_response' within
    'timeout' seconds or an empty list if no positive responses were received.
    """
    _max_memory_space = (2 ** (8 * address_byte_size) - 1)
    # Sanity checks
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("Timeout value ({0}) cannot be negative"
                         .format(timeout))
    if start_addr < 0:
        raise ValueError("Start Address '{:x}' must be a positive integer".format(start_addr))
    if start_addr + mem_length > _max_memory_space:
        raise OverflowError("Start Address (0x{:x}) plus Memory Length (0x{:x}) "
                            "will exceed the maximum memory address space (0x{:x})"
                            .format(start_addr, mem_length, _max_memory_space))
    # Extended diagnostics
    response = extended_session(arb_id_request,
                                arb_id_response,
                                session_type)
    if not Iso14229_1.is_positive_response(response):
        raise ValueError("Unable to enter extended session...\n")
    responses = []
    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        
        IsoTp.NP[0] = NP[0]
        IsoTp.PADDING[0] = PADDING[0]

        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout
            if print_results:
                print('Dumping Memory in range 0x{:x}-0x{:x}\n'.format(
                    start_addr, start_addr + mem_length))
                print('Identified Addresses:')
                print('Address    Value (hex)')
            for identifier in range(start_addr, start_addr + mem_length, mem_size):
                response = uds.read_memory_by_address(memory_address=identifier, memory_size=mem_size,

                                                      address_and_length_format=(memory_length_byte_size << 4) + address_byte_size)

                # Only keep positive responses
                if response and Iso14229_1.is_positive_response(response):
                    responses.append((identifier, response))
                    if print_results:
                        print('0x{:x}'.format(identifier), list_to_hex_str(response))
            if print_results:
                print("\nDone!")
            return responses
        
def __write_dids_wrapper(args):
    """Wrapper used to initiate data identifier dump"""
    diagnostic = args.dsc
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    min_did = args.min_did
    max_did = args.max_did
    print_results = True
    reporting = args.reporting
    padding = args.padding
    no_padding = args.no_padding

    if reporting == 1:
        global DOCUMENT
        DOCUMENT = 2
        f = open("cc_uds_wdid.txt", "w")
        f.write("Caring Caribou Next UDS Write DID Module\n\n\n")
        f.close()

    padding_set(padding, no_padding)

    write_dids(diagnostic, arb_id_request, arb_id_response, timeout, reporting, min_did, max_did,
              print_results)

def write_dids(diagnostic, arb_id_request, arb_id_response, timeout, reporting,
              min_did=DUMP_DID_MIN, max_did=DUMP_DID_MAX, print_results=True):
    """
    Sends write data by identifier (DID) messages to 'arb_id_request'.
    Returns a list of positive responses received from 'arb_id_response' within
    'timeout' seconds or an empty list if no positive responses were received.
    """
    try:
        # Sanity checks
        if isinstance(timeout, float) and timeout < 0.0:
            raise ValueError("Timeout value ({0}) cannot be negative"
                            .format(timeout))

        if max_did < min_did:
            raise ValueError("max_did must not be smaller than min_did -"
                            " got min:0x{0:x}, max:0x{1:x}".format(min_did, max_did))
        
        if reporting == 1:
            global REPORT
            REPORT = 1

        response_diag = extended_session(arb_id_request, arb_id_response, diagnostic)
        if not Iso14229_1.is_positive_response(response_diag):
            raise ValueError("Supplied Diagnostic Session Control subservice results in Negative Response")

        responses = []
        with IsoTp(arb_id_request=arb_id_request,
                arb_id_response=arb_id_response) as tp:
            # Setup filter for incoming messages

            IsoTp.NP[0] = NP[0]
            IsoTp.PADDING[0] = PADDING[0]

            tp.set_filter_single_arbitration_id(arb_id_response)
            with Iso14229_1(tp) as uds:
                # Set timeout
                if timeout is not None:
                    uds.P3_CLIENT = timeout

                if print_results:
                    print('Testing DIDs in range 0x{:04x}-0x{:04x}\n'.format(
                        min_did, max_did))
                    report_print("\n")
                    report_print('Identified Writable DIDs:')
                    report_print('DID    Value After Write (hex)')

                for identifier in range(min_did, max_did + 1):

                    print(f'Current DID: 0x{identifier:04x}', end='\r', file=stderr)

                    response_read = uds.read_data_by_identifier(identifier=[identifier])

                    # Only keep positive responses
                    if response_read and Iso14229_1.is_positive_response(response_read):

                        data = []

                        for id in range(len(response_read) - 3):
                        
                            data.append(0xAA)

                        response_write = uds.write_data_by_identifier(identifier=[identifier], data=data)
                        if response_write and Iso14229_1.is_positive_response(response_write):

                            response_read = uds.read_data_by_identifier(identifier=[identifier])
                        
                            responses.append((identifier, response_read))

                            if print_results:
                                did = '0x{:04x}'.format(identifier), list_to_hex_str(response_read[3:])
                                report_print(str(did))
                
                if print_results:
                    print("\nDone!")
                    print("\033[K", file=stderr) # clear line
                    print("Done!")
                    report_print("\n")
                return responses
            
    except KeyboardInterrupt:
        print("\033[K", file=stderr) # clear line
        print("Interrupted by user.\n")
        return responses
    except ValueError as e:
        print(e)
        return

def __routine_control_dump_wrapper(args):
    """Wrapper used to initiate routine dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    diagnostic = args.dsc
    subfunction = args.subfunction
    timeout = args.timeout
    min_routine = args.min_routine
    max_routine = args.max_routine
    padding = args.padding
    no_padding = args.no_padding

    padding_set(padding, no_padding)

    routine_control_dump(arb_id_request, arb_id_response, timeout, diagnostic, subfunction, min_routine, max_routine)
    
    
def routine_control_dump(arb_id_request, arb_id_response, timeout, diagnostic, subfunction,
              min_routine=DUMP_ROUTINE_MIN, max_routine=DUMP_ROUTINE_MAX):
    """
    Sends start routine messages to 'arb_id_request'.
    """

    found_routines = []

    try:
        # Sanity checks
        if isinstance(timeout, float) and timeout < 0.0:
            raise ValueError("Timeout value ({0}) cannot be negative"
                            .format(timeout))

        if max_routine < min_routine:
            raise ValueError("max_routine must not be smaller than min_routine -"
                            " got min:0x{0:x}, max:0x{1:x}".format(min_routine, max_routine))

        with IsoTp(arb_id_request=arb_id_request,
                arb_id_response=arb_id_response) as tp:
            
            IsoTp.NP[0] = NP[0]
            IsoTp.PADDING[0] = PADDING[0]

            # Setup filter for incoming messages
            tp.set_filter_single_arbitration_id(arb_id_response)
            with Iso14229_1(tp) as uds:
                # Set timeout
                if timeout is not None:
                    uds.P3_CLIENT = timeout

                print('Enumerating Routines with attributes:')
                
                print('Diagnostic Session Control: 0x{0:02x}'.format(diagnostic))
                print('Routine Control Sub Function: 0x{0:02x}'.format(subfunction))
                print('Minimum Routine: 0x{:04x}'.format(min_routine))
                print('Maximum Routine: 0x{:04x}'.format(max_routine))
                
                response_diag = extended_session(arb_id_request, arb_id_response, diagnostic)
                if not Iso14229_1.is_positive_response(response_diag):
                    raise ValueError("Supplied Diagnostic Session Control subservice results in Negative Response")
                
                for routine in range(min_routine, max_routine + 1):
                    response = uds.routine_control(subfunction, routine=[routine])
                    print(f'Current Routine: 0x{routine:04x}', end='\r', file=stderr)

                    # Parse response
                    if response is None or len(response) == 0:
                        continue
                    if len(response) >= 2:
                        if Iso14229_1.is_positive_response(response):
                            found_routines.append('0x{:04x}'.format(routine))

                print("\033[K", file=stderr)
                
                print("\nDiscovered Routines:")
                # Print results
                for routine_id in found_routines:
                    print(routine_id)
            
    except KeyboardInterrupt:
        print("Interrupted by user.\n")
        # Print results
        for routine_id in found_routines:
            print(routine_id)
        return
    
    except ValueError as e:
        print(e)
        return

def __parse_args(args):
    """Parser for module arguments"""
    parser = argparse.ArgumentParser(
        prog="ccn.py uds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Universal Diagnostic Services module for "
                    "CaringCaribouNext",
        epilog="""Example usage:
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
  ccn.py uds routine_control_dump 0x733 0x633 --dsc 0x02 --subfunction 0x02 """)
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for diagnostics discovery
    parser_discovery = subparsers.add_parser("discovery")
    parser_discovery.add_argument("-min",
                                  type=parse_int_dec_or_hex, default=None,
                                  help="min arbitration ID "
                                       "to send request for")
    parser_discovery.add_argument("-max",
                                  type=parse_int_dec_or_hex, default=None,
                                  help="max arbitration ID "
                                       "to send request for")
    parser_discovery.add_argument("-b", "--blacklist", metavar="B",
                                  type=parse_int_dec_or_hex, default=[],
                                  nargs="+",
                                  help="arbitration IDs to blacklist "
                                       "responses from")
    parser_discovery.add_argument("-ab", "--autoblacklist", metavar="N",
                                  type=float, default=0,
                                  help="listen for false positives for N seconds "
                                       "and blacklist matching arbitration "
                                       "IDs before running discovery")
    parser_discovery.add_argument("-sv", "--skipverify",
                                  action="store_true",
                                  help="skip verification step (reduces "
                                       "result accuracy)")
    parser_discovery.add_argument("-d", "--delay", metavar="D",
                                  type=float, default=DELAY_DISCOVERY,
                                  help="D seconds delay between messages "
                                       "(default: {0})".format(DELAY_DISCOVERY))
    parser_discovery.add_argument("-p", "--padding", metavar="P",
                                    type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                                    help="padding to be used in target messages (default: 0)")
    parser_discovery.add_argument("-np", "--no_padding",
                                    action="store_true",
                                    help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_discovery.set_defaults(func=__uds_discovery_wrapper)

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src",
                             type=parse_int_dec_or_hex,
                             help="arbitration ID to transmit to")
    parser_info.add_argument("dst",
                             type=parse_int_dec_or_hex,
                             help="arbitration ID to listen to")
    parser_info.add_argument("-t", "--timeout", metavar="T",
                             type=float, default=TIMEOUT_SERVICES,
                             help="wait T seconds for response before "
                                  "timeout (default: {0})"
                             .format(TIMEOUT_SERVICES))
    parser_info.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_info.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")    
    parser_info.set_defaults(func=__service_discovery_wrapper)

    # Parser for diagnostics session control subservice discovery
    parser_sub = subparsers.add_parser("subservices")
    parser_sub.add_argument("dsc", metavar="dtype",
                            type=parse_int_dec_or_hex, default="0x01",
                            help="Diagnostic Session Control Subsession Byte")
    parser_sub.add_argument("service", metavar="stype",
                            type=parse_int_dec_or_hex,
                            help="Service ID")
    parser_sub.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_sub.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_sub.add_argument("-t", "--timeout", metavar="T",
                            type=float, default=TIMEOUT_SUBSERVICES,
                            help="wait T seconds for response before "
                                 "timeout (default: {0})"
                            .format(TIMEOUT_SUBSERVICES))
    parser_sub.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_sub.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_sub.set_defaults(func=__sub_discovery_wrapper)

    # Parser for ECU Reset
    parser_ecu_reset = subparsers.add_parser("ecu_reset")
    parser_ecu_reset.add_argument("reset_type", metavar="type",
                                  type=parse_int_dec_or_hex,
                                  help="Reset type: 1=hard, 2=key off/on, "
                                       "3=soft, "
                                       "4=enable rapid power shutdown, "
                                       "5=disable rapid power shutdown")
    parser_ecu_reset.add_argument("src",
                                  type=parse_int_dec_or_hex,
                                  help="arbitration ID to transmit to")
    parser_ecu_reset.add_argument("dst",
                                  type=parse_int_dec_or_hex,
                                  help="arbitration ID to listen to")
    parser_ecu_reset.add_argument("-t", "--timeout",
                                  type=float, metavar="T",
                                  help="wait T seconds for response before "
                                       "timeout")
    parser_ecu_reset.add_argument("-p", "--padding", metavar="P",
                                    type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                                    help="padding to be used in target messages (default: 0)")
    parser_ecu_reset.add_argument("-np", "--no_padding",
                                    action="store_true",
                                    help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_ecu_reset.set_defaults(func=__ecu_reset_wrapper)

    # Parser for TesterPresent
    parser_tp = subparsers.add_parser("testerpresent")
    parser_tp.add_argument("src",
                           type=parse_int_dec_or_hex,
                           help="arbitration ID to transmit to")
    parser_tp.add_argument("-d", "--delay", metavar="D",
                           type=float, default=DELAY_TESTER_PRESENT,
                           help="send TesterPresent every D seconds "
                                "(default: {0})".format(DELAY_TESTER_PRESENT))
    parser_tp.add_argument("-dur", "--duration", metavar="S",
                           type=float,
                           help="automatically stop after S seconds")
    parser_tp.add_argument("-spr", action="store_true",
                           help="suppress positive response")
    parser_tp.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_tp.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_tp.set_defaults(func=__tester_present_wrapper)

    # Parser for SecuritySeedDump
    parser_secseed = subparsers.add_parser("security_seed")
    parser_secseed.add_argument("sess_type", metavar="stype",
                                type=parse_int_dec_or_hex,
                                help="Session Type: 1=defaultSession "
                                     "2=programmingSession 3=extendedSession "
                                     "4=safetySession [0x40-0x5F]=OEM "
                                     "[0x60-0x7E]=Supplier "
                                     "[0x0, 0x5-0x3F, 0x7F]=ISOSAEReserved")
    parser_secseed.add_argument("sec_level", metavar="level",
                                type=parse_int_dec_or_hex,
                                help="Security level: "
                                     "[0x1-0x41 (odd only)]=OEM "
                                     "0x5F=EOLPyrotechnics "
                                     "[0x61-0x7E]=Supplier "
                                     "[0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved")
    parser_secseed.add_argument("src",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to transmit to")
    parser_secseed.add_argument("dst",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to listen to")
    parser_secseed.add_argument("-r", "--reset", metavar="RTYPE",
                                type=parse_int_dec_or_hex,
                                help="Enable reset between security seed "
                                     "requests. Valid RTYPE integers are: "
                                     "1=hardReset, 2=key off/on, 3=softReset, "
                                     "4=enable rapid power shutdown, "
                                     "5=disable rapid power shutdown. "
                                     "(default: None)")
    parser_secseed.add_argument("-d", "--delay", metavar="D",
                                type=float, default=DELAY_SECSEED_RESET,
                                help="Wait D seconds between reset and "
                                     "security seed request. You'll likely "
                                     "need to increase this when using RTYPE: "
                                     "1=hardReset. Does nothing if RTYPE "
                                     "is None. (default: {0})"
                                .format(DELAY_SECSEED_RESET))
    parser_secseed.add_argument("-n", "--num", metavar="NUM", default=0,
                                type=parse_int_dec_or_hex,
                                help="Specify a positive number of security"
                                     " seeds to capture before terminating. "
                                     "A '0' is interpreted as infinity. "
                                     "(default: 0)")
    parser_secseed.add_argument("-p", "--padding", metavar="P",
                                type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                                help="padding to be used in target messages (default: 0)")
    parser_secseed.add_argument("-np", "--no_padding",
                                action="store_true",
                                help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_secseed.set_defaults(func=__security_seed_wrapper)

    # Parser for dump_did
    parser_did = subparsers.add_parser("dump_dids")
    parser_did.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_did.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_did.add_argument("-t", "--timeout",
                            type=float, metavar="T",
                            default=DUMP_DID_TIMEOUT,
                            help="wait T seconds for response before "
                                 "timeout")
    parser_did.add_argument("--dsc", metavar="dtype",
                            type=parse_int_dec_or_hex, default="0x01",
                            help="Diagnostic Session Control Subsession Byte")
    parser_did.add_argument("--min_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MIN,
                            help="minimum device identifier (DID) to read (default: 0x0000)")
    parser_did.add_argument("--max_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MAX,
                            help="maximum device identifier (DID) to read (default: 0xFFFF)")
    parser_did.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_did.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_did.add_argument("-r", "--reporting", default=0,
                            type=parse_int_dec_or_hex,
                            help="reporting to text file, to enable set the option to 1. (default: 0)")
    parser_did.set_defaults(func=__dump_dids_wrapper)

    # Parser for auto
    parser_auto = subparsers.add_parser("auto")
    parser_auto.add_argument("-min",
                             type=parse_int_dec_or_hex, default=None,
                             help="min arbitration ID "
                                  "to send request for")
    parser_auto.add_argument("-max",
                             type=parse_int_dec_or_hex, default=None,
                             help="max arbitration ID "
                                  "to send request for")
    parser_auto.add_argument("-b", "--blacklist", metavar="B",
                             type=parse_int_dec_or_hex, default=[],
                             nargs="+",
                             help="arbitration IDs to blacklist "
                                  "responses from")
    parser_auto.add_argument("-ab", "--autoblacklist", metavar="N",
                             type=float, default=0,
                             help="listen for false positives for N seconds "
                                  "and blacklist matching arbitration "
                                  "IDs before running discovery")
    parser_auto.add_argument("-sv", "--skipverify",
                             action="store_true",
                             help="skip verification step (reduces "
                                  "result accuracy)")
    parser_auto.add_argument("-d", "--delay", metavar="D",
                             type=float, default=DELAY_DISCOVERY,
                             help="D seconds delay between messages "
                                  "(default: {0})".format(DELAY_DISCOVERY))
    parser_auto.add_argument("-t", "--timeout", metavar="T",
                             type=float, default=TIMEOUT_SERVICES,
                             help="wait T seconds for response before "
                                  "timeout (default: {0})"
                             .format(TIMEOUT_SERVICES))
    parser_auto.add_argument("--min_did",
                             type=parse_int_dec_or_hex,
                             default=DUMP_DID_MIN,
                             help="minimum device identifier (DID) to read (default: 0x0000)")
    parser_auto.add_argument("--max_did",
                             type=parse_int_dec_or_hex,
                             default=DUMP_DID_MAX,
                             help="maximum device identifier (DID) to read (default: 0xFFFF)")
    parser_auto.add_argument("--min_routine",
                            type=parse_int_dec_or_hex,
                            default=DUMP_ROUTINE_MIN,
                            help="minimum routine to execute (default: 0x0000)")
    parser_auto.add_argument("--max_routine",
                            type=parse_int_dec_or_hex,
                            default=DUMP_ROUTINE_MAX,
                            help="maximum routine to execute (default: 0xFFFF)")
    parser_auto.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_auto.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_auto.add_argument("-r", "--reporting", default=0,
                            type=parse_int_dec_or_hex,
                            help="reporting to text file, to enable set the option to 1. (default: 0)")
    parser_auto.set_defaults(func=__auto_wrapper)


    # Parser for dump_mem
    parser_mem = subparsers.add_parser("dump_mem")
    parser_mem.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_mem.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_mem.add_argument("-t", "--timeout",
                            type=float, metavar="T",
                            default=DUMP_DID_TIMEOUT,
                            help="wait T seconds for response before "
                                 "timeout")
    parser_mem.add_argument("--start_addr",
                            type=parse_int_dec_or_hex,
                            default=MEM_START_ADDR,
                            help="starting address (default: 0x0000)")
    parser_mem.add_argument("--mem_length",
                            type=parse_int_dec_or_hex,
                            default=MEM_LEN,
                            help="number of bytes to read (default: 1)")
    parser_mem.add_argument("--mem_size",
                            type=parse_int_dec_or_hex,
                            default=MEM_SIZE,
                            help="numbers of bytes to return per request (default: 1)")
    parser_mem.add_argument("--address_byte_size",
                            type=parse_int_dec_or_hex,
                            default=ADDR_BYTE_SIZE,
                            help="numbers of bytes of the address (default: 2)")
    parser_mem.add_argument("--memory_length_byte_size",
                            type=parse_int_dec_or_hex,
                            default=ADDR_BYTE_SIZE,
                            help="numbers of bytes of the memory length parameter (default: 1)")
    parser_mem.add_argument("--sess_type",
                            type=parse_int_dec_or_hex,
                            default=SESSION_TYPE,
                            help="Session Type for activating service (default: 3)")
    parser_mem.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_mem.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_mem.set_defaults(func=__dump_mem_wrapper)


    # Parser for write_did
    parser_wdid = subparsers.add_parser("write_dids")
    parser_wdid.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_wdid.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_wdid.add_argument("--dsc", metavar="dtype",
                            type=parse_int_dec_or_hex, default="0x03",
                            help="Diagnostic Session Control Subsession Byte")
    parser_wdid.add_argument("-t", "--timeout",
                            type=float, metavar="T",
                            default=DUMP_DID_TIMEOUT,
                            help="wait T seconds for response before "
                                 "timeout")
    parser_wdid.add_argument("--min_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MIN,
                            help="minimum device identifier (DID) to write (default: 0x0000)")
    parser_wdid.add_argument("--max_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MAX,
                            help="maximum device identifier (DID) to write (default: 0xFFFF)")
    parser_wdid.add_argument("-r", "--reporting", default=0,
                            type=parse_int_dec_or_hex,
                            help="reporting to text file, to enable set the option to 1. (default: 0)")
    parser_wdid.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_wdid.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_wdid.set_defaults(func=__write_dids_wrapper)

    # Parser for dump_routine
    parser_routine = subparsers.add_parser("routine_control_dump")
    parser_routine.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_routine.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_routine.add_argument("--dsc", metavar="dtype",
                            type=parse_int_dec_or_hex, default="0x01",
                            help="Diagnostic Session Control Subsession Byte")
    parser_routine.add_argument("--subfunction", metavar="subfunction",
                            type=parse_int_dec_or_hex, default="0x01",
                            help="Routine Control Subfunction Byte:\n"
                                 "0x01 startRoutine\n"
                                 "0x02 stopRoutine\n"
                                 "0x03 requestRoutineResults\n"
                                 "0x00, 0x04–0x7F ISOSAEReserved")
    parser_routine.add_argument("-t", "--timeout",
                            type=float, metavar="T",
                            default=DUMP_ROUTINE_TIMEOUT,
                            help="wait T seconds for response before "
                                 "timeout")
    parser_routine.add_argument("--min_routine",
                            type=parse_int_dec_or_hex,
                            default=DUMP_ROUTINE_MIN,
                            help="minimum routine to execute (default: 0x0000)")
    parser_routine.add_argument("--max_routine",
                            type=parse_int_dec_or_hex,
                            default=DUMP_ROUTINE_MAX,
                            help="maximum routine to execute (default: 0xFFFF)")
    parser_routine.add_argument("-p", "--padding", metavar="P",
                            type=parse_int_dec_or_hex, default=PADDING_DEFAULT,
                            help="padding to be used in target messages (default: 0)")
    parser_routine.add_argument("-np", "--no_padding",
                            action="store_true",
                            help="trigger for cases where no padding is required, to enable set the option to 1. (default: 0)")
    parser_routine.set_defaults(func=__routine_control_dump_wrapper)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    """Module main wrapper"""
    try:
        args = __parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
