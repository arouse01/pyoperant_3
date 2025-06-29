import time
import datetime
import serial
import logging
from pyoperant.interfaces import base_
from pyoperant import utils, InterfaceError, ArduinoException
import os

logger = logging.getLogger(__name__)
logger.info("Arduino logging enabled")


## TODO: Attempt to reconnect device if it can't be reached
# TODO: Allow device to be connected to through multiple python instances.
#       This kind of works but needs to be tested thoroughly.
# TODO: Polling pins

class ArduinoInterface(base_.BaseInterface):
    """Creates a pyserial interface to communicate with an Arduino via the serial connection.
    Communication is through two byte messages where the first byte specifies the channel and the second byte specifies
    the action.
    Valid actions are:
    0. Read input value
    1. Set output to ON
    2. Set output to OFF
    3. Sets channel as an output
    4. Sets channel as an input
    5. Sets channel as an input with a pullup resistor (basically inverts the input values)
    :param device_name: The address of the device on the local system (e.g. /dev/tty.usbserial)
    :param baud_rate: The baud (bits/second) rate for serial communication. If this is changed, then it also needs to be
            changed in the arduino project code.
    """

    _default_state = dict(invert=False,
                          held=False,
                          )

    def __init__(self, device_name, baud_rate=115200, inputs=None, outputs=None, *args, **kwargs):

        super(ArduinoInterface, self).__init__(*args, **kwargs)

        self.device_name = device_name
        self.baud_rate = baud_rate
        self.device = None

        self.read_params = ('channel', 'pullup')
        self._state = dict()
        self.inputs = []
        self.outputs = []

        self.open()
        if inputs is not None:
            for input_ in inputs:
                self._config_read(*input_)
        if outputs is not None:
            for output in outputs:
                self._config_write(output)

    def __str__(self):

        return "Arduino device at %s: %d input channels and %d output channels configured" % (
            self.device_name, len(self.inputs), len(self.outputs))

    def __repr__(self):
        # Add inputs and outputs to this
        return "ArduinoInterface(%s, baud_rate=%d)" % (self.device_name, self.baud_rate)

    def open(self):
        """Open a serial connection for the device
        :return: None
        """

        logger.debug("Opening device %s" % self)
        # self.device = serial.Serial(port=self.device_name, baudrate=self.baud_rate, timeout=5)
        self.device = serial.Serial(exclusive=True)
        self.device.port = self.device_name
        self.device.baudrate = self.baud_rate
        self.device.timeout = 1
        self.device.setDTR(False)
        self.device.open()

        if self.device is None:
            raise InterfaceError('Could not open serial device %s' % self.device_name)

        logger.debug("Waiting for device to open")
        self.device.readline()
        self.device.flushInput()
        logger.info("Successfully opened device %s" % self)

    def close(self):
        """Close a serial connection for the device
        :return: None
        """

        logger.debug("Closing %s" % self)
        self.device.close()

    def _config_read(self, channel, pullup=False, **kwargs):
        """ Configure the channel to act as an input
        :param channel: the channel number to configure
        :param pullup: the channel should be configured in pullup mode. On the arduino this has the effect of
        returning HIGH when unpressed and LOW when pressed. The returned value will have to be inverted.
        :return: None
        """

        logger.debug("Configuring %s, channel %d as input" % (self.device_name, channel))
        if pullup is False:
            self.device.write(self._make_arg(channel, 4))
        else:
            self.device.write(self._make_arg(channel, 5))

        if channel in self.outputs:
            self.outputs.remove(channel)
        if channel not in self.inputs:
            self.inputs.append(channel)

        self._state.setdefault(channel, self._default_state.copy())
        self._state[channel]["invert"] = pullup

    def _config_write(self, channel, **kwargs):
        """ Configure the channel to act as an output
        :param channel: the channel number to configure
        :return: None
        """

        logger.debug("Configuring %s, channel %d as output" % (self.device_name, channel))
        self.device.write(self._make_arg(channel, 3))
        if channel in self.inputs:
            self.inputs.remove(channel)
        if channel not in self.outputs:
            self.outputs.append(channel)
        self._state.setdefault(channel, self._default_state.copy())

    def _read_bool(self, channel, **kwargs):
        """ Read a value from the specified channel
        :param channel: the channel from which to read
        :return: value

        Raises
        ------
        ArduinoException
            Reading from the device failed.
        """

        if channel not in self._state:
            raise InterfaceError("Channel %d is not configured on device %s" % (channel, self.device_name))

        if self.device.inWaiting() > 0:  # There is currently data in the input buffer
            self.device.flushInput()
        self.device.write(self._make_arg(channel, 0))
        # Also need to make sure self.device.read() returns something that ord can work with. Possibly except TypeError
        while True:  # is this While loop necessary? can it just call the try statement once?
            try:
                t = self.device.read()
                # logger.debug("Read value of %s from channel %d on %s" % (t, channel, self))
            except serial.SerialException:
                # This is to make it robust in case it accidentally disconnects or you try to access the arduino in
                # multiple ways
                # self.reconnect_panel()
                logger.info('Serial connection issue - serialException')
                raise ArduinoException("Serial connection interrupted")

            try:
                if len(t) == 0:  # t == 0 if channel is false (serialjava.py changes actual value of -1)
                    v = 0
                else:
                    v = ord(t)
                break
            except TypeError:
                logger.error("Device %s returned unexpected value of %d on reading channel %d" % (self, t, channel))
                raise ArduinoException("returned unexpected value of %d on reading channel %d" % (t, channel))
                # raise InterfaceError("Serial connection not responding")

        logger.debug("Read value of %d from channel %d on %s" % (v, channel, self))
        if v in [0, 1]:
            if self._state[channel]["invert"]:
                v = 1 - v
            return v == 1
        else:
            logger.error("Device %s returned unexpected value of %d on reading channel %d" % (self, v, channel))
            # raise InterfaceError('Could not read from serial device "%s", channel %d' % (self.device, channel))

    def _poll(self, channel, timeout=None, wait=None, suppress_longpress=True, **kwargs):
        """ runs a loop, querying for pecks. returns peck time or None if polling times out
        :param channel: the channel from which to read
        :param timeout: the time, in seconds, until polling times out. Defaults to no timeout.
        :param wait: the time, in seconds, between subsequent reads. Defaults to 0.
        :param suppress_longpress: only return a successful read if the previous read was False. This can be helpful
        when using a button, where a press might trigger multiple times.

        :return: timestamp of True read
        """

        if timeout is not None:
            start = time.time()
        else:
            start = ''

        logger.debug("Begin polling from device %s" % self.device_name)
        while True:
            try:
                result = self._read_bool(channel)
            except (InterfaceError, ArduinoException):
                # self.reconnect_panel()
                logger.info('InterfaceError during polling')
                raise ArduinoException('InterfaceError during polling')

            if not result:
                logger.debug("Polling: %s" % False)
                # Read returned False. If the channel was previously "held" then that flag is removed
                if self._state[channel]["held"]:
                    self._state[channel]["held"] = False
            else:
                logger.debug("Polling: %s" % True)
                # As long as the channel is not currently held, or longpresses are not being supressed,
                # register the press
                if (not self._state[channel]["held"]) or (not suppress_longpress):
                    break

            if timeout is not None:
                if time.time() - start >= timeout:  # Return GoodNite exception?
                    logger.debug("Polling timed out. Returning")
                    return None

            # Wait for a specified amount of time before continuing on with the next loop
            if wait is not None:
                utils.wait(wait)

        self._state[channel]["held"] = True
        logger.debug("Input detected. Returning")
        return datetime.datetime.now()

    def _write_bool(self, channel, value, **kwargs):
        """Write a value to the specified channel
        :param channel: the channel to write to
        :param value: the value to write
        :return: value written if succeeded
        """

        if channel not in self._state:
            raise InterfaceError("Channel %d is not configured on device %s" % (channel, self))

        logger.debug("Writing %s to device %s, channel %d" % (value, self, channel))
        if value:
            s = self.device.write(self._make_arg(channel, 1))
        else:
            s = self.device.write(self._make_arg(channel, 2))
        if s:
            return value
        else:
            # self.reconnect_panel()
            raise ArduinoException('Could not write to serial device %s, channel %d' % (self.device, channel))

    # # ENABLE IF USING TEENSY WAV PLAYBACK
    # def _play_wav(self, value, **kwargs):
    #     channel = 99
    #     """Start audio playback
    #     :param channel: the channel to write to (60 is built into the arduino code to handle audio)
    #     :param value: the file type
    #     :return: value written if succeeded
    #     """
    #
    #     # if channel not in self._state:
    #     #     raise InterfaceError("Channel %d is not configured on device %s" % (channel, self))
    #
    #     logger.debug("Writing %s to device %s, audio" % (value, self))
    #     if value:
    #         s = self.device.write(self._make_arg(channel, 1))
    #     else:
    #         s = self.device.write(self._make_arg(channel, 2))
    #     if s:
    #         return value
    #     else:
    #         raise InterfaceError('Could not write to serial device %s, audio' % (self.device, channel))
    #
    # def _stop_wav(self, value, **kwargs):
    #     channel = 99
    #     """Stop audio playback
    #     :param channel: the channel to write to (60 is built into the arduino code to handle audio)
    #     :param value: the file type
    #     :return: value written if succeeded
    #     """
    #
    #     # if channel not in self._state:
    #     #     raise InterfaceError("Channel %d is not configured on device %s" % (channel, self))
    #
    #     logger.debug("Stopping audio on device %s, audio" % (self))
    #     s = self.device.write(self._make_arg(channel, 0))
    #     if s:
    #         return value
    #     else:
    #         raise InterfaceError('Could not write to serial device %s, audio' % (self.device, channel))
    #
    # def _queue_wav(self):
    #     # Not used but required by pyoperant
    #     return

    def reconnect_panel(self):
        # If hardware connection is interrupted, like serial communication fails,
        """:return: None
        """
        logger.info('Serial device %s not responding, reconnecting' % self.device_name)
        self.device.close()
        try:
            self.device.open()
        except:
            raise InterfaceError('Could not open serial device %s' % self.device_name)

        logger.debug("Waiting for device to open")
        self.device.readline()
        self.device.flushInput()
        logger.info("Successfully reopened device %s" % self.device_name)

        # Reinitiate the inputs and outputs
        for channelIn in self.inputs:
            self._config_read(channelIn)
        for channelOut in self.outputs:
            self._config_write(channelOut)
        # Reconnect sound
        # audioDevice = self.panel.interfaces['pyaudio'].device
        # audioDevice.close()
        # try:
        #     audioDevice.open()
        # except:
        #     raise InterfaceError('could not find pyaudio device %s' % self.device_name)

        # logger.info("Successfully reconnected sound for device %s" % self.device_name)

        # self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])

    @staticmethod
    def _make_arg(channel, value):
        """ Turns a channel and boolean value into a 2 byte hex string to be fed to the arduino
        :return: 2-byte hex string for input to arduino
        """

        return "".join([chr(channel), chr(value)]).encode('utf-8')


