import pyaudio
import wave
from pyoperant.interfaces import base_
from pyoperant import InterfaceError
import os


def api_id():
    osName = os.name
    if osName == "posix":
        return 'ALSA'
    else:
        return 'Windows WASAPI'


class PyAudioInterface(base_.BaseInterface):
    """Class which holds information about an audio device

    assign a simple callback function that will execute on each frame
    presentation by writing interface.callback

    interface.callback() should return either True (to continue playback) or
    False (to terminate playback)

    Before assigning any callback function, please read the following:
    https://www.assembla.com/spaces/portaudio/wiki/Tips_Callbacks

    """

    def __init__(self, device_name='default', io_type='output', *args, **kwargs):
        super(PyAudioInterface, self).__init__(*args, **kwargs)
        self.device_info = None
        self.pa = None
        self.device_name = device_name
        self.device_index = None
        self.stream = None
        self.wf = None
        self.io_type = io_type
        self.preferredHost = api_id()
        self.open()

    def get_api_info(self, p: pyaudio.PyAudio):
        api_info, api_index = None, 0
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            if i == 0:
                api_info = current_api_info
            else:
                if current_api_info['name'] == self.preferredHost:
                    api_info, api_index = current_api_info, i
                    break
        return api_info, api_index

    def open(self):
        self.pa = pyaudio.PyAudio()
        api_info, api_index = self.get_api_info(self.pa)
        # warn user if preferred API is not available
        api_name = api_info['name']
        if api_name != self.preferredHost:
            print(f'[WARNING] "{self.preferredHost}" not available on this system, '
                  f'going with "{api_name}" instead')
        numdevices = api_info.get('deviceCount')
        # Get device index based on device name, which is customized in Linux implementations (e.g., 'board01')
        # using get_device_info_by_host_api_device_index because it gets the full device name
        for i in range(numdevices):
            deviceInfo = self.pa.get_device_info_by_host_api_device_index(api_index, i)
            currDeviceName = deviceInfo['name'][:18]
            if self.device_name[:18] == currDeviceName:
                # make sure it's the appropriate input/output
                if ((self.io_type == 'output' and deviceInfo.get('maxOutputChannels') > 0)
                        or (self.io_type == 'input' and deviceInfo.get('maxInputChannels') > 0)):
                    device_index = i
                    break
                else:
                    device_index = None

        if device_index is None:
            raise InterfaceError('could not find pyaudio device %s' % self.device_name)

        self.device_info = self.pa.get_device_info_by_host_api_device_index(api_index, device_index)

        # however, the device index on the API is NOT the same index for get_device_info_by_index()
        self.device_index = self.device_info['index']

    def close(self):
        try:
            self.stream.close()
        except AttributeError:
            self.stream = None
        try:
            self.wf.close()
        except AttributeError:
            self.wf = None
        self.pa.terminate()

    def validate(self):
        if self.wf is not None:
            if self.wf.getnchannels() > 0:  # Trying to track down pyaudio error -9998
                return True
            else:
                raise InterfaceError('Wav file reports invalid number of channels')
        else:
            raise InterfaceError('there is something wrong with this wav file')

    def _get_stream(self, start=False, callback=None):
        """
        """
        if callback is None:
            def callback(in_data, frame_count, time_info, status):
                data = self.wf.readframes(frame_count)
                return data, pyaudio.paContinue

        self.stream = self.pa.open(format=self.pa.get_format_from_width(self.wf.getsampwidth()),
                                   # channels=self.wf.getnchannels(),
                                   channels=2,  # fixed to 1 for single-channel (mono) stimuli
                                   rate=self.wf.getframerate(),
                                   # input=True,
                                   output=True,
                                   output_device_index=self.device_index,
                                   start=start,
                                   stream_callback=callback)

    def _get_input_stream(self, start=False, callback=None):
        """
        """
        if callback is None:
            def callback(in_data, frame_count, time_info, status):
                data = self.wf.readframes(frame_count)
                return data, pyaudio.paContinue

        CHUNK = 4096  # recording chunk size
        RATE = 44100  # recording sampling rate

        self.stream = self.pa.open(format=self.pa.get_format_from_width(self.wf.getsampwidth()),
                                   # channels=self.wf.getnchannels(),
                                   channels=1,  # fixed to 1 for single-channel (mono) stimuli
                                   rate=RATE,
                                   input=True,
                                   input_device_index=self.device_index,
                                   start=start,
                                   frames_per_buffer=CHUNK,
                                   stream_callback=callback)

    def _queue_wav(self, wav_file, start=False, callback=None):
        self.wf = wave.open(wav_file)
        self.validate()
        self._get_stream(start=start, callback=callback)

    def _play_wav(self):
        self.stream.start_stream()

    def _stop_wav(self):
        try:
            self.stream.close()
        except AttributeError:
            self.stream = None
        try:
            self.wf.close()
        except AttributeError:
            self.wf = None

    def _record_input(self):
        pass
