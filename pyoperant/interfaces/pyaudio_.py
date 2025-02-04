import pyaudio
import wave
from pyoperant.interfaces import base_
from pyoperant import InterfaceError


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
        self.device_name = device_name
        self.device_index = None
        self.stream = None
        self.wf = None
        self.io_type = io_type
        self.open()

    def open(self):
        self.pa = pyaudio.PyAudio()
        # Get device index based on device name, which is customized in Linux implementations (e.g., 'board01')
        if self.io_type == 'output':
            for index in range(self.pa.get_device_count()):
                deviceInfo = self.pa.get_device_info_by_index(index)
                truncName = deviceInfo['name']
                # if self.device_name == self.pa.get_device_info_by_index(index)['name']:
                if deviceInfo.get('maxOutputChannels') > 0 and self.device_name[:18] == truncName[:18]:  # only check
                    # the first 7 characters
                    self.device_index = index
                    break
                else:
                    self.device_index = None
        elif self.io_type == 'input':
            for index in range(self.pa.get_device_count()):
                deviceInfo = self.pa.get_device_info_by_index(index)
                truncName = deviceInfo['name']
                # if self.device_name == self.pa.get_device_info_by_index(index)['name']:
                if deviceInfo.get('maxInputChannels') > 0 and self.device_name[:18] == truncName[:18]:  # only check
                    # the first 7 characters
                    self.device_index = index
                    break
                else:
                    self.device_index = None
        if self.device_index is None:
            raise InterfaceError('could not find pyaudio device %s' % self.device_name)

        self.device_info = self.pa.get_device_info_by_index(self.device_index)

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
                                   channels=1,  # fixed to 1 for single-channel (mono) stimuli
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
