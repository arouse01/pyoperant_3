import wave
import os
import numpy
import struct
import pydub

folder = '/home/rouse/bird/stim/temp'

wavlist = os.listdir(folder)
wavlist.sort()
for curr_file in range(len(wavlist)):
    wavPath = os.path.join(folder, wavlist[curr_file])
    method = 0
    if method == 1:
        # use pydub instead!
        waveform = pydub.AudioSegment.from_wav(wavPath)
        waveformScaled = waveform + 10
        newFileName = os.path.splitext(wavPath)[0] + '_hi.wav'
        waveformScaled.export(newFileName, format='wav')
    else:
        wav_file = wave.open(wavPath, 'rb')
        params = wav_file.getparams()
        nFrames = params[3]
        nChannels = params[0]
        waveformRaw = wav_file.readframes(nFrames)
        wav_file.close()

        # technically the formula for dbFS is 20*log10(rms*sqrt(2))

        # waveform = struct.unpack("%ih" % nFrames*nChannels, waveformRaw)
        waveform = numpy.fromstring(waveformRaw, dtype=numpy.int16)
        # get scaled waveform
        wfScale = waveform.astype(float) / (pow(2, 15) - 1)
        # max amplitude
        maxAmp = max(float(max(waveform)), abs(float(min(waveform))))

        # current scale
        maxProp = maxAmp/(pow(2, 15)-1)  # 2^15 is max for int16
        print(maxProp)

        # newdB = 10**((dBCurr + dBChange)/20)/numpy.sqrt(2)
        # # scale waveform to maximum
        # waveformFS = waveform/maxProp
        #
        # waveformScaled = waveformFS * 0.75
        # waveformRaw = struct.pack('h'*nFrames, *waveformScaled)
        #
        # newFileName = os.path.splitext(wavPath)[0] + '_hi.wav'
        #
        # wav_file = wave.open(newFileName, 'wb')
        # wav_file.setparams(params)
        # wav_file.writeframes(waveformRaw)
        # wav_file.close()
    print("finished file %d, %s" % (curr_file, wavlist[curr_file]))


