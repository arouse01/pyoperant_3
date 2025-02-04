import pyaudio
import wave
import re
import time




testFile = '/home/rouse/bird/stim/440 test tone.wav'
soundIn = pyaudio.PyAudio()
tempRecording = 'Box {:02d} level.wav'.format(3)
CHUNK = 4096  # recording chunk size
RATE = 44100  # recording sampling rate
SECONDS = 3  # how long to record
wf = wave.open(testFile)

def callback(in_data, frame_count, time_info, status):
    # necessary for pyaudio to play in non-blocking mode
    data = wf.readframes(frame_count)
    return data, pyaudio.paContinue

testFile = '/home/rouse/bird/stim/440 test tone.wav'
soundOut = pyaudio.PyAudio()

# Get actual device indices
deviceNameOut = 'Board03: USB Audio'
deviceIndexOut = None
for index in range(soundOut.get_device_count()):
    truncName = soundOut.get_device_info_by_index(index)['name']
    if deviceNameOut[:18] == truncName[:18]:  # only check the first 7 characters
        deviceIndexOut = index
        break
    else:
        deviceIndexOut = None
if deviceIndexOut is None:
    raise NameError('could not find pyaudio device %s' % deviceNameOut)
#
FORMAT = soundIn.get_format_from_width(wf.getsampwidth())
# deviceNameIn = 'sound03'
# deviceIndexIn = None
#
# # First get list of cards on computer
# cardFile = '/proc/asound/cards'  # cards file contains list of all cards
# f = open(cardFile, 'r')
# fl = f.readlines()
# # cards file is formatted "number [deviceName     ] so pull values before the matching name to get card number
# matchString = '^(.+?)\s\[' + deviceNameIn
# deviceCardIn = []
# for x in fl:
#     m = re.search(matchString, x)
#     if m is not None:
#         deviceCardIn = int(m.groups()[0])
#         print("ALSA Card number: %d" % deviceCardIn)
#         break
# if not deviceCardIn:
#     raise NameError('could not find input device %s' % deviceNameIn)
#
# # now use ALSA card number to find pyaudio device index
# deviceIndexIn = None
CHANNELS = 1
# for index in range(soundIn.get_device_count()):
#     pyaudioInputIndex = []
#     try:
#         pyaudioInputIndex = re.split('hw:', soundIn.get_device_info_by_index(index)['name'])[1]
#     except IndexError:
#         pass
#     if pyaudioInputIndex:
#         # if hw number returned, compare with ALSA card
#         pyaudioInputIndex = int(re.split(',', pyaudioInputIndex)[0])
#
#         if pyaudioInputIndex == deviceCardIn:
#             deviceIndexIn = int(index)
#             print(deviceIndexIn, soundIn.get_device_info_by_index(deviceIndexIn)['name'], soundIn.get_device_info_by_index(
#                 deviceIndexIn)['index'])
#             break
#
#
print(FORMAT)
streamOut = soundOut.open(format=FORMAT,
                                  channels=1,  # fixed to 1 for single-channel (mono) stimuli
                                  rate=44100,
                                  output=True,
                                  output_device_index=deviceIndexOut,
                                  start=False,
                                  stream_callback=callback)

# streamIn = soundIn.open(format=FORMAT,
#                         channels=1,
#                         rate=RATE,
#                         input=True,
#                         input_device_index=6,
#                         frames_per_buffer=CHUNK
#                         )
streamOut.start_stream()
time.sleep(5)
# streamIn.start_stream()
# recording for SECONDS seconds
rmsMax = 0
frames = []
print("starting recording")
# for i in range(0, int(RATE/CHUNK * SECONDS)):
#     data = streamIn.read(CHUNK)
#     # create wav file
#     frames.append(data)
#
#     # # calculate rms directly
#     # rmsNew = audioop.rms(data, 2)
#     # if rmsNew > rmsMax:
#     #     rmsMax = rmsNew
print("recording finished")
# create temporary wav file
wavFile = wave.open(tempRecording, 'wb')
wavFile.setnchannels(1)
wavFile.setsampwidth(soundIn.get_sample_size(FORMAT))
wavFile.setframerate(RATE)
wavFile.writeframes(b''.join(frames))
wavFile.close()
print("file closed")