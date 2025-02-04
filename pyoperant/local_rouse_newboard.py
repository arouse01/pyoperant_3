from pyoperant import hwio, components, panels, utils
from pyoperant.interfaces import pyaudio_, arduino_

_ROUSE_MAP = {
    1: ('/dev/teensy01', 2, 0, 2, 8),  # box_id:(subdevice,in_dev,in_chan,out_dev,out_chan)
    2: ('/dev/teensy02', 2, 4, 2, 16),
    3: ('/dev/teensy03', 2, 24, 2, 32),
    4: ('/dev/teensy04', 2, 28, 2, 40),
    5: ('/dev/teensy05', 2, 48, 2, 56),
    6: ('/dev/teensy06', 2, 52, 2, 64),
    7: ('/dev/teensy07', 2, 72, 2, 80),
    8: ('/dev/teensy08', 2, 76, 2, 88),
    9: ('/dev/teensy09', 2, 96, 2, 96)
    }


class RousePanel(panels.BasePanel):
    """class for rouse boxes """

    def __init__(self, panel_id=None, boardtype=None, *args, **kwargs):
        super(RousePanel, self).__init__(*args, **kwargs)
        self.id = panel_id

        # define interfaces
        self.interfaces['pyaudio'] = pyaudio_.PyAudioInterface(device_name='Board%02i: USB Audio' % self.id)
        self.interfaces['arduino'] = arduino_.ArduinoInterface(device_name='/dev/teensy%02i' % self.id)

        # define inputs
        if boardtype == 'v1.4':
            INPUTS = [38,  # Trial IR
                      37,  # Response IR
                      ]

            OUTPUTS = [36,  # Trial LED
                       35,  # Response LED
                       20,  # House lights
                       22,  # Reinforcement solenoid
                       ]
        elif boardtype == 'v2.0':
            # Has two solenoids
            INPUTS = [38,  # Trial IR
                      37,  # Response IR
                      ]

            OUTPUTS = [36,  # Trial LED
                       35,  # Response LED
                       20,  # House lights
                       22,  # Reinforcement solenoid 1
                       21,  # Reinforcement solenoid 2
                       ]
        elif boardtype == 'v4.0':
            # Has two solenoids
            INPUTS = [36,  # Trial IR
                      35,  # Response IR
                      ]

            OUTPUTS = [38,  # Trial LED
                       37,  # Response LED
                       22,  # House lights
                       41,  # Reinforcement solenoid 1
                       40,  # Reinforcement solenoid 2
                       ]

        else:
            INPUTS = [37,  # Trial IR
                      36,  # Response IR
                      ]

            OUTPUTS = [1,  # Trial LED
                       2,  # Response LED
                       3,  # House lights
                       16,  # Reinforcement solenoid
                       ]

        for in_chan in INPUTS:
            self.inputs.append(hwio.BooleanInput(interface=self.interfaces['arduino'],
                                                 params={'channel': in_chan
                                                         },
                                                 )
                               )
        for out_chan in OUTPUTS:
            self.outputs.append(hwio.BooleanOutput(interface=self.interfaces['arduino'],
                                                   params={'channel': out_chan
                                                           },
                                                   )
                                )

        self.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        # self.microphone = hwio.AudioOutput(interface=self.interfaces['pyaudio'])
        # assemble inputs into components
        self.trialSens = components.PeckPort(ir=self.inputs[0], led=self.outputs[0])  #
        self.respSens = components.PeckPort(ir=self.inputs[1], led=self.outputs[1])
        self.house_light = components.HouseLight(light=self.outputs[2], inverted=True)

        self.water = components.WaterValve(solenoid=self.outputs[3])
        if len(self.outputs) > 4:
            self.water2 = components.WaterValve(solenoid=self.outputs[4])
            self.reward2 = self.water2.reward

        # define reward & punishment methods
        self.reward = self.water.reward
        self.punish = self.house_light.punish

    def reset(self):
        for output in self.outputs:
            output.write(False)
        self.house_light.on()
        self.water.off()

    def test(self):
        print('reset')
        self.reset()
        dur = 2.0
        for output in self.outputs:
            print('output %s on' % output)
            output.write(True)
            utils.wait(dur)
            print('output %s off' % output)
            output.write(False)
        print('reset')
        self.reset()
        print('feed')
        self.reward(value=dur)
        print('timeout')
        self.punish(value=dur)
        print('queue file')
        self.speaker.queue('/usr/local/stimuli/A1.wav')
        print('play file')
        self.speaker.play()
        return True


class Rouse1(RousePanel):
    """Rouse1 panel"""
    def __init__(self, boardtype='v1'):
        super(Rouse1, self).__init__(panel_id=1, boardtype=boardtype)


class Rouse2(RousePanel):
    """Rouse2 panel"""
    def __init__(self, boardtype='v1'):
        super(Rouse2, self).__init__(panel_id=2, boardtype=boardtype)


class Rouse3(RousePanel):
    """Rouse3 panel"""
    def __init__(self, boardtype='v1'):
        super(Rouse3, self).__init__(panel_id=3, boardtype=boardtype)


class Rouse4(RousePanel):
    """Rouse4 panel"""
    def __init__(self, boardtype='v1'):
        super(Rouse4, self).__init__(panel_id=4, boardtype=boardtype)


class Rouse5(RousePanel):
    """Rouse4 panel"""
    def __init__(self, boardtype='v1'):
        super(Rouse5, self).__init__(panel_id=5, boardtype=boardtype)


class Rouse6(RousePanel):
    """Rouse6 panel"""

    def __init__(self, **kwargs):
        super(Rouse6, self).__init__(panel_id=6,
                                     **kwargs)  # Not sure if this is the working setup, or if boardtype=boardtype is


class Rouse7(RousePanel):
    """Rouse6 panel"""

    def __init__(self, boardtype='v1.4'):
        super(Rouse7, self).__init__(panel_id=7, boardtype=boardtype)
        # Not sure if this is the working setup, or if boardtype=boardtype is


class Rouse8(RousePanel):
    """Rouse6 panel"""

    def __init__(self, boardtype='v1.4'):
        super(Rouse8, self).__init__(panel_id=8, boardtype=boardtype)
        # Not sure if this is the working setup, or if boardtype=boardtype is


class Rouse9(RousePanel):
    """Rouse6 panel"""

    def __init__(self, boardtype='v1.4'):
        super(Rouse9, self).__init__(panel_id=9, boardtype=boardtype)
        # Not sure if this is the working setup, or if boardtype=boardtype is


# class Rouse7(RousePanel):
#     """Rouse7 panel"""
#     def __init__(self, boardtype='v1'):
#         super(Rouse7, self).__init__(id=7)
#
# class Rouse8(RousePanel):
#     """Rouse8 panel"""
#     def __init__(self, boardtype='v1'):
#         super(Rouse8, self).__init__(id=8)


# in the end, 'PANELS' should contain each operant panel available for use

PANELS = {"1": Rouse1,
          "2": Rouse2,
          "3": Rouse3,
          "4": Rouse4,
          "5": Rouse5,
          "6": Rouse6,
          "7": Rouse7,
          "8": Rouse8,
          "9": Rouse9
          }

BEHAVIORS = ['pyoperant.behavior']

DATA_PATH = '/home/rouse/bird/data/'

# SMTP_CONFIG

DEFAULT_EMAIL = 'andrew.rouse@tufts.edu'

SMTP_CONFIG = {'mailhost': 'localhost',
               'toaddrs': [DEFAULT_EMAIL],
               'fromaddr': 'Aperture <aperturefinch@gmail.com>',
               'subject': '[pyoperant notice] on rouse',
               'credentials': None,
               'secure': None,
               }
