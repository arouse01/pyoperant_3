import logging, traceback
import os, sys, socket
import datetime as dt
import atexit
from pyoperant import utils, components, local, hwio
from pyoperant import ComponentError, InterfaceError
from pyoperant.behavior import shape

try:
    import simplejson as json
except ImportError:
    import json


def _log_except_hook(*exc_info):  # How uncaught errors are handled
    text = "".join(traceback.format_exception(*exc_info))
    # print(text)  # print out in case email log isn't working
    logging.error("Unhandled exception: %s", text)


class BaseExp(object):
    """Base class for an experiment.

    Keyword arguments:
    name -- name of this experiment
    desc -- long description of this experiment
    debug -- (bool) flag for debugging (default=False)
    light_schedule  -- the light schedule for the experiment. either 'sun' or
        a tuple of (starttime,endtime) tuples in (hhmm,hhmm) form defining
        time intervals for the lights to be on
    experiment_path -- path to the experiment
    stim_path -- path to stimuli (default = <experiment_path>/stims)
    subject -- identifier of the subject
    panel -- instance of local Panel() object

    Methods:
    run() -- runs the experiment

    """

    def __init__(self,
                 name='',
                 description='',
                 debug=False,
                 filetime_fmt='%Y%m%d%H%M%S',
                 light_schedule='sun',
                 idle_poll_interval=60.0,
                 experiment_path='',
                 stim_path='',
                 subject='',
                 panel=None,
                 log_handlers=[],
                 *args, **kwargs):
        super(BaseExp, self).__init__()

        self.version = "2.0.0"

        self.name = name
        self.description = description
        self.debug = debug
        self.timestamp = dt.datetime.now().strftime(filetime_fmt)
        self.parameters = kwargs
        self.parameters['filetime_fmt'] = filetime_fmt
        self.parameters['light_schedule'] = light_schedule
        self.parameters['idle_poll_interval'] = idle_poll_interval

        self.parameters['experiment_path'] = experiment_path
        if stim_path == '':
            self.parameters['stim_path'] = os.path.join(experiment_path, 'stims')
        else:
            self.parameters['stim_path'] = stim_path
        self.parameters['subject'] = subject

        # configure logging
        self.parameters['log_handlers'] = log_handlers
        self.log_config()

        self.req_panel_attr = ['house_light',
                               'reset',
                               ]
        self.panel = panel
        self.log.debug('panel %s initialized' % self.parameters['panel_name'])

        atexit.register(self.pyoperant_close)

        if 'shape' not in self.parameters:
            # or self.parameters['shape'] not in ['block1', 'block2', 'block3', 'block4', 'block5']:
            self.parameters['shape'] = None

    def save(self):
        json_path = os.path.join(self.parameters['experiment_path'], 'settings_files')
        if not os.path.exists(json_path):
            os.mkdir(json_path)
        self.snapshot_f = os.path.join(json_path, self.timestamp + '.json')
        with open(self.snapshot_f, 'wb') as config_snap:
            json.dump(self.parameters, config_snap, sort_keys=True, indent=4)

    def log_config(self):

        self.log_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.log')
        self.error_file = os.path.join(self.parameters['experiment_path'], 'error.log')
        log_path = os.path.join(self.parameters['experiment_path'])
        if not os.path.exists(log_path):  # Add path if it doesn't exist
            os.makedirs(log_path)

        if self.debug:
            self.log_level = logging.DEBUG
        else:
            self.log_level = logging.INFO

        sys.excepthook = _log_except_hook  # send uncaught exceptions to log file

        logging.basicConfig(filename=self.log_file,
                            level=self.log_level,
                            format='"%(asctime)s","%(levelname)s","%(message)s"')
        self.log = logging.getLogger()
        errorHandler = logging.FileHandler(self.error_file, mode='w')  # mode 'w' means messages replace existing
        # contents of file
        errorHandler.setLevel(logging.ERROR)
        errorHandler.setFormatter(logging.Formatter('"%(asctime)s",\n%(message)s'))

        self.log.addHandler(errorHandler)

        if 'email' in self.parameters['log_handlers']:
            from pyoperant.local import SMTP_CONFIG
            from logging import handlers
            SMTP_CONFIG['toaddrs'] = [self.parameters['experimenter']['email'], ]

            email_handler = handlers.SMTPHandler(**SMTP_CONFIG)
            email_handler.setLevel(logging.WARNING)

            heading = '%s/Box %s\n' % (self.parameters['subject'], self.parameters['panel_name'])
            formatter = logging.Formatter(heading + '%(levelname)s at %(asctime)s:\n%(message)s')
            email_handler.setFormatter(formatter)

            self.log.addHandler(email_handler)

    def check_light_schedule(self):
        """returns true if the lights should be on"""
        return utils.check_time(self.parameters['light_schedule'])

    def check_session_schedule(self):
        """returns True if the subject should be running sessions"""
        if utils.check_day(self.parameters['session_days']):
            return utils.check_time(self.parameters['session_schedule'])
        return False

    def check_day_schedule(self):
        """returns True if the subject should be running sessions"""
        if utils.check_day(self.parameters['session_days']):
            return True
        else:
            return False

    def panel_reset(self):
        try:
            self.panel.reset()
        except components.ComponentError as err:
            self.log.error("component error: %s" % str(err))

    def run(self):

        for attr in self.req_panel_attr:
            assert hasattr(self.panel, attr)
        self.panel_reset()

        self.save()
        self.init_summary()

        self.log.info('%s: running %s with parameters in %s' % (self.name,
                                                                self.__class__.__name__,
                                                                self.snapshot_f,
                                                                )
                      )
        if self.parameters['shape']:
            self.shaper.run_shape()

        while True:  # is this while necessary?
            utils.run_state_machine(start_in='idle',
                                    error_state='idle',
                                    error_callback=self.log_error_callback,
                                    idle=self._run_idle,
                                    sleep=self._run_sleep,
                                    session=self._run_session)

    def _run_idle(self):
        if not self.check_light_schedule():  # If lights should be off
            return 'sleep'
        elif self.check_session_schedule():  # If session should be running
            return 'session'
        else:
            self.panel_reset()
            self.log.debug('idling...')
            utils.wait(self.parameters['idle_poll_interval'])
            return 'idle'

    # defining functions for sleep
    def sleep_pre(self):
        self.log.debug('lights off. going to sleep...')
        return 'main'

    def sleep_main(self):
        """ reset expal parameters for the next day """
        self.log.debug('sleeping...')
        self.panel.house_light.off()
        utils.wait(self.parameters['idle_poll_interval'])
        if not self.check_light_schedule():
            return 'main'
        else:
            return 'post'

    def sleep_post(self):
        self.log.debug('ending sleep')
        self.panel.house_light.on()
        self.init_summary()
        return None

    def _run_sleep(self):
        utils.run_state_machine(start_in='pre',
                                error_state='post',
                                error_callback=self.log_error_callback,
                                pre=self.sleep_pre,
                                main=self.sleep_main,
                                post=self.sleep_post)
        return 'idle'

    def pyoperant_close(self):
        try:
            self.log.debug('waiting for response')
            print "Closing pyoperant, turing off all components"
            self.panel.trialSens.off()
            self.panel.respSens.off()
        except:
            pass

    # session

    def session_pre(self):
        return 'main'

    def session_main(self):
        return 'post'

    def session_post(self):
        return None

    def _run_session(self):
        utils.run_state_machine(start_in='pre',
                                error_state='post',
                                error_callback=self.log_error_callback,
                                pre=self.session_pre,
                                main=self.session_main,
                                post=self.session_post)
        return 'idle'

    def init_summary(self):
        """ initializes an empty summary dictionary """
        self.summary = {'trials': 0,
                        'responses': 0,
                        'feeds': 0,
                        'correct_responses': 0,
                        'false_alarms': 0,
                        'misses': 0,
                        'correct_rejections': 0,
                        'last_trial_time': [],
                        'dprime': 0,
                        'sminus_trials': 0,
                        'splus_trials': 0
                        }

    def write_summary(self):
        """ takes in a summary dictionary and options and writes to the bird's summaryDAT"""
        summary_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.summaryDAT')
        with open(summary_file, 'wb') as f:
            f.write("Trials this session: %s\n" % self.summary['trials'])
            f.write("Rf'd responses: %i\n" % self.summary['feeds'])
            f.write("\n")
            f.write("\tS+\tS-\n")
            f.write("RespSw\t%i\t%i\n" % (self.summary['correct_responses'], self.summary['false_alarms']))
            f.write("TrlSw\t%i\t%i\n" % (self.summary['misses'], self.summary['correct_rejections']))
            f.write("d': %1.2f\n" % self.summary['dprime'])
            # f.write("Feeder ops today: %i\n" % self.summary['feeds'])
            f.write("\nLast trial @: %s" % self.summary['last_trial_time'])

    def write_summary_shaping(self):
        """ takes in a summary dictionary and options and writes to the bird's summaryDAT"""
        summary_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.summaryDAT')
        with open(summary_file, 'wb') as f:
            f.write("Shaping Summary\n\n")
            f.write("Feeds today: %s\n" % self.summary['feeds'])
            f.write("Pecks today: %i\n" % self.summary['responses'])
            # f.write("Feeder ops today: %i\n" % self.summary['feeds'])
            f.write("\nLast trial @: %s" % self.summary['last_trial_time'])

    def log_error_callback(self, err):
        if err.__class__ is InterfaceError or err.__class__ is ComponentError:
            self.log.critical(str(err))
