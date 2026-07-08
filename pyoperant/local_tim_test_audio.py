from pyoperant.local_rouse_newboard import Rouse12
if __name__ == "__main__":
    panel = Rouse12()
    panel.test_sound()

# import pyaudio
# pa=pyaudio.PyAudio()
# for i in range(1,23):
#     print(pa.get_device_info_by_index(i))
#     print(pa.get_device_info_by_index(i)['name'].encode('ascii', 'ignore'))
# print(pa.get_device_count)