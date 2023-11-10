import threading
import time
import can

def message_listener(bus, can_messages):
    while True:
        message = bus.recv()
        can_messages.append(message)
        time.sleep(0.01)  # Adjust the sleep duration as needed


def start_listener(bus, can_messages):
    # Create a thread for the message listener function
    listener_thread = threading.Thread(target=message_listener, args=(bus, can_messages))
    listener_thread.daemon = True  # Daemonize the thread so it automatically exits when the main program exits

    # Start the thread
    listener_thread.start()

    return listener_thread
