#!/usr/bin/python3
"""
Linux input and pulseaudio based push to talk daemon.

Classes:

PACMD - implements pulseaudio interaction through the
    pacmd command interface

IEV - implements a parser for /dev/input/eventX interfaces

PTT - tracks key positions and adjusts source volume

"""
import collections
import subprocess
import threading
import struct
import select
import queue
import time
import os

TOGGLE_COMBINATION = "29,97,42,54" # both control and shift keys
PTT_COMBINATION = "29,97" # both control keys

VOLUME_ON = 50
VOLUME_OFF = 0

PTTState = collections.namedtuple("PTT_State",
                                  "keys ptt voice")
PTTState.__new__.__defaults__ = (None,) * len(PTTState._fields)

Settings = collections.namedtuple("Settings",
                                  "inputfiles devices pauser "
                                  "volume_on volume_off verbose "
                                  "toggle_combination ptt_combination")
Settings.__new__.__defaults__ = (None,) * len(Settings._fields)

Event = collections.namedtuple("Event",
                               "ev_sec ev_usec ev_type "
                               "ev_code ev_value")

class Flag:
    """
    Simple boolean flag.
    """
    value = False

    def __bool__(self):
        return self.value

    def switch_on(self):
        """
        Turn flag on.
        """
        self.value = True

    def switch_off(self):
        """
        Turn flag off.
        """
        self.value = False

    def toggle(self):
        """
        Toggle flag's value.
        """
        self.value = not self.value

class PACMD:
    """runs pacmd and sends commands to it"""
    def __init__(self, devices, pauser=None):
        self.devices = devices
        self.pauser = pauser
        self.open_pacmd()

    def open_pacmd(self):
        """
        Opens pacmd subprocess and starts a reader thread.
        """
        if self.pauser:
            self.pacmd = subprocess.Popen(
                ["/bin/su", "-", self.pauser, "-c", "pacmd"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        else:
            self.pacmd = subprocess.Popen(
                ["pacmd"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        self.read_thread = threading.Thread(target=self.recvloop)
        self.read_thread.start()

    def recvloop(self):
        """
        The pacmd reader thread (prevents pacmd output locking it up).
        """
        poller = select.poll()
        poller.register(self.pacmd.stdout, select.POLLIN|select.POLLERR)
        while True:
            if poller.poll():
                if not self.pacmd.stdout.read():
                    break
            else:
                time.sleep(1)

    def send(self, cmd):
        """
        Send a command to pacmd (write a line to its input).
        """
        if self.pacmd.poll() is not None:
            self.open_pacmd()
        self.pacmd.stdin.write(bytes(cmd + '\n', 'utf-8'))
        self.pacmd.stdin.flush()

    def close(self):
        """
        Closes pacmd's input (which should cause it to exit).
        """
        self.pacmd.stdin.flush()
        self.pacmd.stdin.close()

    def volume(self, val):
        """
        Set volume for specified devices to val.
        """
        # handle percentage points
        if val < 100:
            val = int(65535/100*val)
        for device in self.devices:
            self.send('set-source-volume {} {}'.format(device, val))

class IEV:
    """
    Reads linux input events.
    """

    def __init__(self, filename, event_queue):
        self.event_filename = filename
        self.event_format = 'llHHI'
        self.event_size = struct.calcsize(self.event_format)
        self.event_file = None
        self.event_queue = event_queue
        self.open_event()
        self.event_thread = threading.Thread(target=self.eventreader)
        self.event_thread.start()

    def open_event(self):
        """
        Opens associated linux input event file in appropriate mode.
        """
        if self.event_file:
            self.close()
        self.event_file = open(self.event_filename, "rb")

    def close(self):
        """
        Tries closing the associated event file, ignores errors.
        """
        try:
            self.event_file.close()
        finally:
            pass

    def eventreader(self):
        """
        Read events from file descriptors and put them on a queue.
        """
        poller = select.poll()
        poller.register(self.event_file, select.POLLIN|select.POLLERR)
        while True:
            if poller.poll(1):
                try:
                    event = self.event_file.read(self.event_size)
                except ValueError: # error reading file
                    return
                (ev_sec, ev_usec, ev_type, ev_code, ev_value) = \
                    struct.unpack(self.event_format, event)
                self.event_queue.put(Event(
                    ev_sec=ev_sec, ev_usec=ev_usec, ev_type=ev_type,
                    ev_code=ev_code, ev_value=ev_value))

class PTT:
    """
    Implements push to talk and toggle.
    """
    def __init__(self, settings):
        self.settings = settings
        self.state = PTTState(keys=dict(), ptt=Flag(), voice=Flag())

    def keys_down(self, *codes):
        """true if keys with codes are down, false otherwise"""
        for code in codes:
            if not self.state.keys.get(code):
                return False
        return True

    # process state based on current event
    def process(self, event, pacmd):
        """process key combinations, update state and call volume
           adjustment as neccessary"""
        if self.settings.verbose:
            print("Event: {}".format(event))
        if event.ev_value == 1 and self.keys_down(*self.settings.toggle_combination):
            self.state.voice.toggle()
            if self.state.voice:
                if self.settings.verbose:
                    print("volume: {}".format(self.settings.volume_on))
                pacmd.volume(self.settings.volume_on)
            else:
                if self.settings.verbose:
                    print("volume: {}".format(self.settings.volume_off))
                pacmd.volume(self.settings.volume_off)
        # both control keys for push to talk
        elif (not self.state.voice and not self.state.ptt and
              event.ev_value == 1 and self.keys_down(*self.settings.ptt_combination)):
            if self.settings.verbose:
                print("volume: {}".format(self.settings.volume_on))
            pacmd.volume(self.settings.volume_on)
            self.state.ptt.switch_on()
        elif (not self.state.voice and self.state.ptt and event.ev_value == 0
              and event.ev_code in self.settings.ptt_combination):
            if self.settings.verbose:
                print("volume: {}".format(self.settings.volume_off))
            pacmd.volume(self.settings.volume_off)
            self.state.ptt.switch_off()

    def run(self):
        """main event loop"""

        # set up queue
        event_queue = queue.Queue()

        # start pulseaudio control channel and mute
        pacmd = PACMD(self.settings.devices, self.settings.pauser)
        pacmd.volume(self.settings.volume_off)

        # start event readers
        ievs = []
        for filename in self.settings.inputfiles:
            ievs.append(IEV(filename, event_queue))

        # event loop
        while True:
            try:
                event = event_queue.get()
                if event.ev_type == 1 and event.ev_code != 0:
                    self.state.keys[event.ev_code] = event.ev_value
                    self.process(event, pacmd)

            except KeyboardInterrupt:
                break

        for iev in ievs:
            iev.close()
            iev.event_thread.join()
        pacmd.close()

class ArgsException(Exception):
    """
    Invalid command line argument exception.
    """
    pass


def main(args):
    """
    Parse args, set up instances and run.
    """

    def parse(option, args, default=None, many=False, exc=ArgsException()):
        """
        Parses the sys.argv array and extracts data.
        """
        # options that can be repeated
        if many:
            ret = []
            i = 0
            for arg in args:
                if arg == option:
                    ret.append(args[i+1])
                i += 1
            if not ret and default is None and exc.args:
                raise exc
            elif not ret and default is not None:
                return default
            return ret
        # options that can only be passed once (only the first is honored)
        else:
            if option in args:
                ret = args[args.index(option)+1]
                return ret
            else:
                if default is None and exc.args:
                    raise exc
            return default

    # specify input device(s)
    exc = ArgsException("You need to specify at least one keyboard to "
                        "monitor (-i /dev/input/eventX).")
    inputfiles = parse('-i', args, many=True, exc=exc)

    # pulseaudio source device(s)
    exc = ArgsException("You need to specify at least one input device "
                        "(-m alsa_input.pci-0000_00_1b.0.analog-stereo).")
    devices = parse('-m', args, many=True, exc=exc)

    # pulseaudio user
    if os.getuid() == 0:
        exc = ArgsException("You need to specify user running pulseaudio "
                            "when running as root (-u user).")
        pauser = parse('-u', args, exc=exc)
    else:
        pauser = None

    # push to talk combination
    ptt_combination = \
        [int(x) for x in parse('-p', args, default=PTT_COMBINATION).split(',')]

    # toggle combination
    toggle_combination = \
        [int(x) for x in parse('-t', args, default=TOGGLE_COMBINATION).split(',')]

    # specify the loud volume (in percent up to 100, then absolute 0-65535)
    volume_on = int(parse('-l', args, default=VOLUME_ON))

    # specify the silent volume (in percent up to 100, then absolute 0-65535)
    volume_off = int(parse('-s', args, default=VOLUME_OFF))

    # be verbose
    verbose = '-v' in args

    # settings
    settings = Settings(inputfiles=inputfiles, devices=devices,
                        pauser=pauser, ptt_combination=ptt_combination,
                        toggle_combination=toggle_combination,
                        volume_on=volume_on, volume_off=volume_off,
                        verbose=verbose)

    ptt = PTT(settings)
    ptt.run()

def usage():
    """
    Usage instructions.
    """
    print("""Usage: {}
    <-i eventX> [-i eventY] ...
    <-m source1> [-m source2] ...
    [-u username] [-p k1,k2,k3] [-t k1,k2,k3] [-l 60] [-s 0] [-v]


    -i /dev/input/event3
        Listen for events from specified keyboard
        (can be specified multiple times, may require root privileges).
    -m alsa_input.pci-0000_00_1b.0.analog-stereo
        Set volume for this pulseaudio source
        (can be specified multiple times).
    -u username
        Run pacmd as this user (only if running as root
        for /dev/input/event* access).
    -p k1,k2,k3
        Talk when these keys are held down
        (comma separated key codes).
    -t k1,k2,k3
        Toggle voice on/off when these keys are pressed
        (comma separated key codes).
    -l 60
        Set volume to this when loud
        (percent for numbers <100, absolute otherwise).
    -s 0
        Set volume to this level when silent
        (percent for numbers <100, absolute otherwise).
    -v
        Be verbose (prints key codes and volume changes).
""")

if __name__ == '__main__':
    import sys
    try:
        main(sys.argv)
    except ArgsException as ex:
        usage()
        print(str(ex))
    except:
        raise
