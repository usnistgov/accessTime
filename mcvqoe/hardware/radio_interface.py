import io
import math
import re
from warnings import warn

import serial
import serial.tools.list_ports


# custom exception for commands
class CommandError(Exception):
    pass


class RadioInterface:
    
    #USB PID/VID to use in search. Devices matching this PID/VID will be checked
    #This is a generic TI PID/VID that could get used by other things
    #TODO : do we want our own?
    _USB_VID = 0x2047 # RadioInterface Vendor ID (VID)
    _USB_PID = 0x0300 # RadioInterface Product ID (PID)

    def __init__(self, port=None, debug=False):

        self.debug = debug

        if not port:
            ports = serial.tools.list_ports.comports()
            for p in ports:
                #check for matching PID/VID
                if(not (p.vid==self._USB_VID and p.pid==self._USB_PID)):
                    if self.debug:
                        print(f"Skipping {p.device}, PID/VID does not match")
                    #skip this device
                    continue
                try:
                    self._openPort(p.device)
                    # send device type command
                    dt = self.devtype()

                    if self.debug:
                        print(f"{p.device} Devtype : {dt}")

                    if dt.startswith("MCV radio interface"):
                        # port found, done
                        break
                    else:
                        # close serial port
                        self.sobj.close()
                except (CommandError, serial.SerialException, UnicodeDecodeError) as e:
                    if self.debug:
                        print(e)
            else:
                # port not found, give error
                raise RuntimeError("No radio interface found")
        else:
            # open port
            self._openPort(port)

    def __enter__(self):

        return self

    def ptt(self, state, num=1):
        """
            PTT - change the push-to-talk status of the radio interface

            PTT(state) if state is true then the PTT is set to transmit. if state is
        False then the radio is set to not transmit

        PTT(state,num) same as above but control the ptt of radio number num
        instead of radio number 1
        """

        # check what the state is
        if state:
            # state is on
            state = "on"
        else:
            # state is off
            state = "off"

        # send command
        self._command(f"ptt {num} {state}")

    def led(self, num, state):
        """turn on or off LED's on the radio interface board

        LED(num,state) changes the state of the LED given by num. If state is
        true turn the LED on if state is False turn the LED off"""

        # determine LED state string
        if state:
            ststr = "on"
            if self.debug:
                print("state is on", flush=True)
        else:
            ststr = "off"
            if self.debug:
                print("state is off", flush=True)
        # send command
        self._command(f"LED {num} {ststr}")

    def devtype(self):
        """get the devicetype string from the radio interface

        dt = DEVTYPE() where dt is the devicetype string"""

        # flush input from buffer

        # send devtype command
        self._command("devtype")
        # get devtype line
        return self.textin.readline()

    def get_id(self):
        """Get the ID string from radio interface"""

        # Send ptt command with no arguments
        self._command("id")

        # Get response line
        ri_id = self.textin.readline()
        # Strip whitespace
        ri_id = ri_id.strip()

        return ri_id

    def get_version(self):
        """Get the version number from radio interface"""

        # Get devtype, this will have version
        devtype = self.devtype()
        parts = devtype.split(":")

        if len(parts) == 2:
            ver = parts[1]
            ver = ver.strip()
        else:
            ver = "old"
            warn("Unexpected devtype format, old RadioInterface firmware?")

        return ver

    def pttState(self):
        """returns the pttState for a radioInterface object. This is called
        automatically when pttState is accessed"""

        # flush input from buffer

        # send ptt command with no arguments
        self._command("ptt")
        # get response line
        resp = self.textin.readline()
        # extract number of PTT outputs
        m = re.match("(?P<num>\d+) PTT outputs:", resp)
        # check for match
        if not m:
            raise RuntimeError(f"could not parse '{resp}'")
        # parse outputs
        num = int(m.group("num"))
        # preallocate value
        value = num * [None]
        # loop through all outputs
        for k in range(num):
            # get response line
            resp = self.textin.readline()
            # get state from response
            m = re.match("PTT(\d+) status : (?:(?P<on>on)|(?P<off>off))", resp)
            # check that state was parsed correctly
            if m:
                if m.group("on"):
                    value[k] = True
                elif m.group("off"):
                    value[k] = False
                else:
                    value[k] = None
            else:
                value[k] = None
            #if there was a problem, print response in debug mode
            if value[k] is None and self.debug:
                print(f'Could not parse line : \'{resp}\'')

        return value

    def waitState(self):
        """returns the WaitState for a radioInterface object. this is called
        automatically when WaitState is accessed"""

        self._command("ptt state")
        # get response line
        resp = self.textin.readline()
        # parse PTT state
        m = re.match('PTT state : "(?P<state>.*?)"', resp)
        if m:
            return m.group("state")
        else:
            err_str = "Error : "
            if resp.startswith(err_str):
                raise RuntimeError(resp[len(err_str) :])
            else:
                raise RuntimeError(f"Unknown response '{resp}' received")

    def ptt_delay(self, delay, num=1, use_signal=False):
        """setup the radio interface to key the radio after a delay

        PTT_DELAY(dly) set the radio to be keyed in dly seconds.

        PTT_DELAY(dly,use_signal=True) set the radio to be keyed dly seconds
        after the start signal is detected.

        PTT_DELAY(dly,num=n,__) same as above but used key radio number n
        instead of radio number one

        delay=PTT_DELAY(dly,__) same as above but return the actual delay set on
        the microcontroller. This is different because of rounding and limits on
        the possible delay
        """

        # check which ptt command to use
        if use_signal:
            # delay is relative to signal
            delay_type = "Sdelay"
        else:
            # delay is relative to when command processed
            delay_type = "delay"

        # send ptt command with no arguments
        self._command(f"ptt {num} {delay_type} {delay}")
        # get response line
        resp = self.textin.readline()
        # get delay from string
        m = re.match(
            "(?:Error : (?P<err>.+)$)|(?:PTT in (?P<dly>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) sec)",
            resp,
        )

        # check for match
        if not m:
            raise RuntimeError(f"Unable to parse esponse {resp}")

        # check PTT delay was found
        if m.group("dly"):
            return float(m.group("dly"))
        elif m.group("err"):
            raise RuntimeError(m.group("err"))
        else:
            # unable to parse error
            raise RuntimeError("Unknown Error")

    def temp(self):
        """read value from temperature sensors

        [ext,int]=temp() - returns the temperature measured by the thermistor
        external to the radiointerface or the temperature sensor built into the
        MSP430
        """

        # send temp command
        self._command("temp")

        # get internal temp line
        intl = self.textin.readline()
        # get external temp line
        extl = self.textin.readline()

        # parse internal temperature
        m_int = re.match("int = (?P<temp>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) C", intl)
        # check for match
        if m_int:
            # get temperature value
            t_int = float(m_int.group("temp"))
        else:
            raise RuntimeError(f"could not parse internal temperature from '{intl}'")
        # parse external temp value
        m_ext = re.match("ext = (?P<val>\d+)", extl)
        # check for match
        if m_ext:
            # get integer ADC value
            v_ext = int(m_ext.group("val"))
        else:
            raise RuntimeError(f"could not parse external temperature from '{extl}'")
        # B value of thermistor
        B = 3470
        # compute external temperature
        t_ext = (
            B / math.log(10e3 / ((2 ** 12 - 1) / v_ext - 1) / (10e3 * math.exp(-B / (273.15 + 25))))
            - 273.15
        )

        return (t_int, t_ext)

    # delete method
    def __del__(self):
        
        #check if we have a serial object
        if hasattr(self, "sobj"):
            # check if port is open
            if self.sobj:
                # closeout command, turn off LEDS and ptt
                self.sobj.write(b"closeout\n")

                # wait for all data to write out
                self.sobj.flush()

            # flush and close text wrapper
            self.textin.close()

    def __exit__(self, exc_type, exc_value, exc_traceback):

        # check if we have a serial object
        if hasattr(self, "sobj"):
            # check if we had a serial problem
            if (not exc_type) or "serial" not in exc_type.__name__.lower():
                self._command("closeout")
            else:
                print("Problem with serial port detected, no cleanup performed")

    def _openPort(self, port):

        self.sobj = serial.Serial(port, timeout=0.5)
        # buffer serial data
        self.textin = io.TextIOWrapper(io.BufferedReader(self.sobj))

        self.connPort = port

    def _command(self, cmd):
        """low level command function to send command to the MSP430"""

        # trim extraneous white space from command
        cmd = cmd.strip()

        if self.debug:
            print(f"sending '{cmd}'")

        # assemble string and encode to bytes
        cmd_b = (cmd + "\n").encode("utf-8")
        # send command
        self.sobj.write(cmd_b)

        # line buffer
        l = ""

        # maximum number of iterations
        mi = 3

        # check command responses for echo
        while cmd not in l:
            # get response
            l = self.textin.readline()

            # strip whitespace
            l = l.strip()

            if self.debug and l:
                print(f"recived '{l}'")

            # subtract one from count
            mi -= 1
            # check if we should timeout
            if mi <= 0:
                # throw error
                raise CommandError("Command response timeout")
