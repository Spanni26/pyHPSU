#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# v 0.0.3 by Vanni Brutto (Zanac)

import sys
import configparser
try:
    import can
except Exception:
    pass


class CanPI(object):
    hpsu = None
    timeout = None
    retry = None

    def __init__(self, hpsu=None):
        self.hpsu = hpsu
        try:
            self.bus = can.interface.Bus(channel='can0', bustype='socketcan')

        except can.CanInterfaceNotImplementedError:
            self.bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
        except Exception:
            self.hpsu.printd('exception', 'Error opening bus can0')
            sys.exit(9)
        config = configparser.ConfigParser()
        iniFile = '%s/%s.conf' % (self.hpsu.pathCOMMANDS, "pyhpsu")
        config.read(iniFile)
        self.timeout = float(self.get_with_default(config=config, section="CANPI", name="timeout", default=0.05))
        self.retry = float(self.get_with_default(config=config, section="CANPI", name="retry", default=15))

    def get_with_default(self, config, section, name, default):
        if config.has_option(section, name):
            return config.get(section, name)
        else:
            return default

    def __del__(self):
        try:
            self.bus.shutdown()
        except Exception:
            self.hpsu.printd('exception', 'Error shutdown canbus')"""

    def make_can_message(self, receiver, data):
        try:
            # New python-can version
            return can.Message(
                arbitration_id=receiver,
                data=data,
                is_extended_id=False
            )
        except TypeError:
            # Old python-can version
            return can.Message(
                arbitration_id=receiver,
                data=data,
                extended_id=False,
                dlc=len(data)
            )

    def sendCommandWithID(self, cmd, setValue=None, priority=1):
        if setValue is not None:
            receiver_id = 0x680
        else:
            receiver_id = int(cmd["id"], 16)
        command = cmd["command"]

        if setValue is not None:
            command = command[:1] + '2' + command[2:]
            if command[6:8] != "FA":
                command = command[:3] + "00 FA" + command[2:8]
            command = command[:14]
            """ if cmd["unit"] == "deg":
                setValue = int(setValue)
                if setValue < 0:
                    setValue = 0x10000+setValue
                command = command+" %02X %02X" % (setValue >> 8, setValue & 0xff)"""
            if cmd["type"] == "longint":
                setValue = int(setValue)
                command = command + " 00 %02X" % (setValue)
            if cmd["type"] == "int":
                setValue = int(setValue)
                command = command + " %02X 00" % (setValue)
            if cmd["type"] == "float":
                setValue = int(setValue)
                if setValue < 0:
                    setValue = 0x10000 + setValue
                command = command + " %02X %02X" % (setValue >> 8, setValue & 0xff)
            if cmd["type"] == "value":
                setValue = int(setValue)
                command = command + " 00 %02X" % (setValue)

        msg_data = [int(r, 16) for r in command.split(" ")]
        notTimeout = True
        i = 0

        try:
            # msg = can.Message(arbitration_id=receiver_id, data=msg_data, is_extended_id=False, dlc=7)
            msg = self.make_can_message(receiver_id, msg_data)
            self.bus.send(msg)

        except Exception as e:
            self.hpsu.printd('exception', f'Error sending msg: {e}')

        if setValue is not None:
            return "OK"

        while notTimeout:
            i += 1
            timeout = self.timeout
            rcBUS = None
            try:
                rcBUS = self.bus.recv(timeout)

            except Exception:
                self.hpsu.printd('exception', 'Error recv')

            if rcBUS:
                if (msg_data[2] == 0xfa and msg_data[3] == rcBUS.data[3] and msg_data[4] == rcBUS.data[4]) or (
                        msg_data[2] != 0xfa and msg_data[2] == rcBUS.data[2]):
                    rc = "%02X %02X %02X %02X %02X %02X %02X" % (rcBUS.data[0], rcBUS.data[1], rcBUS.data[2],
                                                                 rcBUS.data[3], rcBUS.data[4], rcBUS.data[5],
                                                                 rcBUS.data[6])
                    notTimeout = False
                    # print("got:  " + str(rc))
                else:
                    self.hpsu.printd('error', 'SEND:%s' % (str(msg_data)))
                    self.hpsu.printd('error', 'RECV:%s' % (str(rcBUS.data)))
            else:
                self.hpsu.printd('error', 'Not aquired bus')

            if notTimeout:
                self.hpsu.printd('warning', 'msg not sync, retry: %s' % i)
                if i >= self.retry:
                    self.hpsu.printd('error', 'msg not sync, timeout')
                    notTimeout = False
                    rc = "KO"

        return rc
