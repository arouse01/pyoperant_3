#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
import copy
import datetime as dt
from pyoperant.behavior import base, shape, adlib
from pyoperant.errors import EndSession, EndBlock, InterfaceError, ArduinoException
from pyoperant import utils, reinf, queues, analysis

# from collections import OrderedDict  # If we want to export json in some sort of ordered way

try:
    import simplejson as json
except ImportError:
    import json


class GoNoGoInterruptExp(base.BaseExp):
    """A two alternative choice experiment

    Parameters
    ----------


    Attributes
    ----------
    req_panel_attr : list
        list of the panel attributes that are required for this behavior
    fields_to_save : list
        list of the fields of the Trial object that will be saved
    trials : list
        all of the trials that have run
    shaper : Shaper
        the protocol for shaping 
    parameters : dict 
        all additional parameters for the experiment
    data_csv : string 
        path to csv file to save data
    reinf_sched : object
        does logic on reinforcement



    """

    def __init__(self, *args, **kwargs):
        super(GoNoGoInterruptExp, self).__init__(*args, **kwargs)

        if self.parameters['shape']:
            self.shaper = shape.ShaperGoNogoInterrupt(self.panel, self.log, self.parameters, self.log_error_callback)

        if 'free_day_off' not in self.parameters:
            # or self.parameters['shape'] not in ['block1', 'block2', 'block3', 'block4', 'block5']:
            self.parameters['free_day_off'] = False

        # self.shaper = shape.ShaperGoNogoInterrupt(self.panel, self.log, self.parameters, self.log_error_callback)

        # # Get stimuli from separate file (for centrally-modifiable stimuli list that only needs to be
        # updated once, rather than for each subject). If there is no stim_list parameter, then use any stims that
        # are already defined in the json file
        if 'stim_list' in self.parameters:
            stim_file = self.parameters['stim_list']
            if os.path.isfile(stim_file):
                with open(stim_file, 'rb') as stim_list:
                    stimuli = json.load(stim_list)
                    self.parameters['stims'] = stimuli['stims']

        # # assign stim files full names
        for name, filename in self.parameters['stims'].items():
            filename_full = os.path.join(self.parameters['stim_path'], filename)
            self.parameters['stims'][name] = filename_full

        self.req_panel_attr += ['speaker',
                                'trialSens',
                                'respSens',
                                'reward',
                                'punish',
                                ]

        # configure csv file for data
        self.fields_to_save = ['session',
                               'index',
                               'type_',
                               'stimulus',
                               'class_',
                               'response',
                               'correct',
                               'rt',
                               'reward',
                               'punish',
                               'time',
                               'subject',
                               'block'
                               ]

        if 'add_fields_to_save' in self.parameters.keys():
            self.fields_to_save += self.parameters['add_fields_to_save']

        self.trials = []
        self.session_id = 0
        self.trial_q = None
        self.session_q = None

        data_dir = os.path.join(self.parameters['experiment_path'], 'trialdata')

        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        self.data_csv = os.path.join(data_dir, self.parameters['subject'] + '_trialdata_' + self.timestamp + '.csv')
        self.make_data_csv()

        if 'block_design' not in self.parameters:
            self.parameters['block_design'] = {
                'blocks': {
                    'default': {
                        'queue': 'random',
                        'conditions': [{'class': k} for k in self.parameters['classes'].keys()]
                    }
                },
                'order': ['default']
            }

        if 'session_schedule' not in self.parameters:
            self.parameters['session_schedule'] = self.parameters['light_schedule']

        if 'free_day_off' not in self.parameters:
            self.parameters['free_day_off'] = False
        elif self.parameters['free_day_off']:
            self.shaperAdLib = adlib.ShaperFree(self.panel, self.log, self.parameters, self.log_error_callback)

        if 'no_response_correction_trials' not in self.parameters:
            self.parameters['no_response_correction_trials'] = False

        if 'subject_type' not in self.parameters:
            self.parameters['subject_type'] = 'bird'

        # # Get blocks from separate file (for centrally-modifiable block definitions)
        if 'block_path' in self.parameters['block_design']:
            block_path = self.parameters['block_design']['block_path']
            if os.path.isfile(block_path):
                with open(block_path, 'rb') as stim_list:
                    blocks = json.load(stim_list)
                    self.parameters['block_design']['blocks'] = blocks['blocks']

    def reconnect_panel(self):
        # If hardware connection is interrupted, like serial communication fails,
        """:return: None
        """
        # Disconnected devices, at least on Linux, show the
        # behavior that they are always ready to read immediately
        # but reading returns nothing.
        device_name = self.panel.interfaces['arduino'].device_name
        # device = self.panel.interfaces['arduino'].device
        self.log.info('Serial device %s not responding, reconnecting' % device_name)
        self.panel.interfaces['arduino'].device.close()
        try:
            self.panel.interfaces['arduino'].device.open()
        except (InterfaceError, ArduinoException):
            self.log.info('First attempt failed, retrying')
            try:
                utils.wait(0.5)
                self.panel.interfaces['arduino'].device.open()
            except (InterfaceError, ArduinoException):
                raise InterfaceError('Could not open serial device %s' % device_name)

        # self.log.debug("Waiting for device to open")
        # device.readline()
        # device.flushInput()
        # self.log.info("Successfully reopened device %s" % device_name)

        # Reinitiate the inputs and outputs
        # for reInput in self.panel.inputs:
        #     reInput.config()
        # for reOutput in self.panel.outputs:
        #     reOutput.config()
        # Reconnect sound
        # self.reconnect_audio()
        # audioDevice = self.panel.speaker.interface
        # audioDevice.close()
        # try:
        #     audioDevice.open()
        # except:
        #     raise InterfaceError('could not find pyaudio device %s' % self.device_name)
        #
        # self.log.info("Successfully reconnected sound for device %s" % device_name)
        #
        # self.panel.speaker = hwio.AudioOutput(interface=self.interfaces['pyaudio'])

    def try_panel_function(self, function, *args, **kwargs):
        # Function for automatically trying Teensy-related function and reconnecting if Teensy isn't responding
        try:
            return function(*args, **kwargs)
        except (ArduinoException, InterfaceError):
            # self.log.info('Teensy function failed, trying to reconnect')
            self.reconnect_panel()
            return function(*args, **kwargs)

    def reconnect_audio(self):
        # If hardware connection is interrupted, like serial communication fails,
        """:return: None
        """
        device_name = self.panel.interfaces['arduino'].device_name
        audioDevice = self.panel.speaker.interface
        audioDevice.close()
        try:
            audioDevice.open()
        except:
            raise InterfaceError('could not find pyaudio device %s' % device_name)

        self.log.info("Successfully reconnected sound for device %s" % device_name)

    def make_data_csv(self):
        """ Create the csv file to save trial data

        This creates a new csv file at experiment.data_csv and writes a header row 
        with the fields in experiment.fields_to_save
        """

        with open(self.data_csv, 'wb') as data_fh:
            trialWriter = csv.writer(data_fh)
            trialWriter.writerow(self.fields_to_save)

    def save(self):
        json_path = os.path.join(self.parameters['experiment_path'], 'settings_files')
        if not os.path.exists(json_path):
            os.mkdir(json_path)
        self.snapshot_f = os.path.join(json_path, self.parameters['subject'] + '_settings_' + self.timestamp + '.json')
        with open(self.snapshot_f, 'wb') as config_snap:
            json.dump(self.parameters, config_snap, sort_keys=True, indent=4)

    def run(self):  # Overwrite base method to include ad lib water when sessions not running

        for attr in self.req_panel_attr:
            assert hasattr(self.panel, attr)
        self.panel_reset()
        self.save()
        if self.session_q is None:  # Skip summary overwriting if resuming session
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
                                    session=self._run_session,
                                    dayoff=self._run_dayoff)

    def _run_idle(self):
        if not self.check_light_schedule():
            # If lights should be off
            return 'sleep'
        elif self.check_session_schedule():
            # If session should be running
            return 'session'
        elif self.parameters['free_day_off']:
            # By this point, established that lights should be on and session shouldn't be running. Therefore if day
            # off parameter is active, start adlib procedure
            return 'dayoff'
        else:
            self.panel_reset()
            self.log.debug('idling...')
            utils.wait(self.parameters['idle_poll_interval'])
            return 'idle'

    def _run_dayoff(self):
        self.shaperAdLib.run_adlib()
        return 'idle'

    def init_summary(self):
        """ initializes an empty summary dictionary """
        self.summary = {'phase': '',
                        'trials': 0,
                        'responses': 0,
                        'feeds': 0,
                        'correct_responses': 0,
                        'false_alarms': 0,
                        'misses': 0,
                        'correct_rejections': 0,
                        'last_trial_time': [],
                        'dprime': 0,
                        'dprime_NR': 0,
                        'bias': 0,
                        'bias_description': '',
                        'bias_NR': 0,
                        'bias_description_NR': '',
                        'sminus_trials': 0,
                        'splus_trials': 0,
                        'sminus_nr': 0,
                        'splus_nr': 0,
                        'probe_trials': 0,
                        'probe_plus': 0,
                        'probe_minus': 0,
                        'probe_hit': 0,
                        'probe_miss': 0,
                        'probe_miss_nr': 0,
                        'probe_FA': 0,
                        'probe_CR': 0,
                        'probe_CR_nr': 0
                        }
        summary_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.summaryDAT')
        with open(summary_file, 'wb') as f:
            f.write("Welcome to pyoperant v%s." % self.version)

    def write_summary(self):
        """ takes in a summary dictionary and options and writes to the bird's summaryDAT"""
        summary_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.summaryDAT')
        with open(summary_file, 'w') as f:
            json.dump(self.summary, f, ensure_ascii=False)

    ## session flow
    def session_pre(self):
        """ Runs before the session starts

        For each stimulus class, if there is a component associated with it, that
        component is mapped onto `experiment.class_assoc[class]`. For example, 
        if the `left` port is registered with the 'L' class, you can access the response 
        port through `experiment.class_assoc['L']`.

        """
        # assert len(self.parameters['classes']) == 2, 'does not currently support > 2 classes'

        self.class_assoc = {}
        for class_, class_params in self.parameters['classes'].items():
            try:
                self.class_assoc[class_] = getattr(self.panel, class_params['component'])
            except KeyError:
                pass

        return 'main'

    def session_main(self):
        """ Runs the sessions

        Inside of `session_main`, we loop through sessions and through the trials within
        them. This relies heavily on the 'block_design' parameter, which controls trial
        conditions and the selection of queues to generate trial conditions.

        """

        def run_trial_queue():
            for tr_cond in self.trial_q:
                try:
                    self.new_trial(tr_cond)
                    self.run_trial()
                    while self.do_correction:
                        self.new_trial(tr_cond)
                        self.run_trial()
                except EndBlock:
                    self.trial_q = None
                    break
            self.trial_q = None

        if self.session_q is None:
            # Check if criteria met for moving to next phase/block
            if 'auto_advance' in self.parameters['block_design'] and self.parameters['block_design']['auto_advance']:
                if len(self.parameters['block_design']['order']) > 1:  # Only check if there's more than one block in
                    # list (so the pyoperant doesn't quit because the last block was removed)
                    nextBlock = next(iter(self.parameters['block_design']['order']))
                    if 'criteria' in self.parameters['block_design']['blocks'][nextBlock]:  # Only check
                        # criteria if actually specified
                        self.log.debug("Checking performance criteria for {}".format(nextBlock))
                        if self.check_performance(nextBlock):
                            self.condition = self.parameters['block_design']['order'].pop(0)  # Remove block from order
                            # with open(self.parameters['config_file'], 'wb') as config_snap:
                            #     json.load(config)
                            with open(self.parameters['config_file'], 'wb') as config_snap:
                                json.dump(self.parameters, config_snap, sort_keys=True, indent=4)
                                self.log.info('Stage {} complete!'.format(self.condition))
                            self.save()

            self.log.info('Next sessions: %s' % self.parameters['block_design']['order'])
            self.session_q = queues.block_queue(self.parameters['block_design']['order'])

        if self.trial_q is None:
            for sn_cond in self.session_q:
                # region Skip blocks where criteria has been met
                # Still in progress, need to decide whether to have the whole block list preserved and have
                # pyoperant cycle through list each time (and skip completed blocks) or remove each block from the
                # list as it's completed
                # block_complete = False  # initialize to false, only gets set to true if criteria have been met
                #
                # if 'auto_advance' in self.parameters['block_design']:  # only if settings file specifies
                #     if self.parameters['block_design']['auto_advance']:  # only if settings file specifies
                #         if len(self.parameters['block_design']['order']) > 1:
                #             # Only check if there's more than one block in list (so the pyoperant doesn't quit because
                #             # the last block was removed)
                #             if 'criteria' in self.parameters['block_design']['blocks'][self.condition]:
                #                 # Only check criteria if actually specified
                #                 if self.check_performance():
                #                     block_complete = True
                # # endregion
                # if block_complete:
                #     pass  # skip completed blocks
                # else:
                self.condition = sn_cond
                self.trials = []
                self.do_correction = False
                self.session_id += 1
                self.log.info('starting session %s: %s' % (self.session_id, sn_cond))
                self.summary['phase'] = self.condition
                # grab the block details
                blk = copy.deepcopy(self.parameters['block_design']['blocks'][sn_cond])

                # load the block details into the trial queue
                blk.pop(
                    'description')  # remove the "description" entry from the dictionary so queues doesn't complain
                if 'criteria' in blk:
                    blk.pop('criteria')
                q_type = blk.pop('queue')

                # Define reinforcement parameters
                if 'reinforcement' not in blk.keys():
                    self.reinf_sched = reinf.ContinuousReinforcement()
                    self.secondary_reinf_bool = False  # Assume no secondary reinforcement should be used
                    self.punish_bool = True  # Assume punishment should be used
                    self.passiveReward = False  # Assume no passive reward on S+ trials
                else:
                    reinforcement = blk.pop('reinforcement')

                    # Get reinforcement schedule
                    if reinforcement['schedule'] == 'variable_ratio':
                        self.reinf_sched = reinf.VariableRatioSchedule(ratio=reinforcement['ratio'])
                    elif reinforcement['schedule'] == 'fixed_ratio':
                        self.reinf_sched = reinf.FixedRatioSchedule(ratio=reinforcement['ratio'])
                    elif reinforcement['schedule'] == 'percent_reinf':
                        self.reinf_sched = reinf.PercentReinforcement(prob=reinforcement['prob'])
                    elif reinforcement['schedule'] == 'go_interrupt':
                        self.reinf_sched = reinf.GoInterruptPercentSchedule(prob=reinforcement['prob'])
                    else:
                        self.reinf_sched = reinf.ContinuousReinforcement()

                    # Other reinforcement parameters
                    if 'secondary' not in reinforcement:
                        self.secondary_reinf_bool = False  # Assume no secondary reinforcement should be used
                    else:
                        self.secondary_reinf_bool = reinforcement.pop('secondary')

                    if 'punish' not in reinforcement:
                        self.punish_bool = True  # Assume punishment should be used
                    else:
                        self.punish_bool = reinforcement.pop('punish')  # var determines whether punishment is used

                    if 'passive' not in reinforcement:
                        self.passiveReward = False  # Assume no passive reward on S+ trials
                    else:
                        self.passiveReward = reinforcement.pop('passive')

                if q_type == 'random':
                    self.trial_q = queues.random_queue(**blk)
                elif q_type == 'block':
                    self.trial_q = queues.block_queue(**blk)
                elif q_type == 'mixedDblStaircase':
                    dbl_staircases = [queues.DoubleStaircaseReinforced(stims) for stims in blk['stim_lists']]
                    self.trial_q = queues.MixedAdaptiveQueue.load(
                        os.path.join(self.parameters['experiment_path'], 'persistentQ.pkl'), dbl_staircases)

                try:
                    run_trial_queue()
                except EndSession:
                    return 'post'

            self.session_q = None
            if self.parameters['subject_type'] == 'human':
                # Blink reward system to signal end of sessions for human subjects
                self.panel.reward(value=.5)
                utils.wait(0.5)
                self.panel.reward(value=.5)
                utils.wait(0.5)
                self.panel.reward(value=.5)
                utils.wait(0.5)
                self.panel.reward(value=.5)
                utils.wait(0.5)
                self.panel.reward(value=.5)
                # utils.wait(0.5)
        else:
            self.condition = self.parameters['block_design']['order'][0]
            self.summary['phase'] = self.condition
            self.log.info('continuing last session')
            # Check if criteria met for moving to next phase/block
            # if 'auto_advance' in self.parameters['block_design'] and self.parameters['block_design']['auto_advance']:
            #     if len(self.parameters['block_design']['order']) > 1:  # Only check if there's more than one block in
            #         # list (so the session won't end because the last block was removed)
            #         if 'criteria' in self.parameters['block_design']['blocks'][self.condition]:  # Only check if
            #             # criteria are specified in json file, otherwise just continue with session
            #             if self.check_performance():
            #                 self.parameters['block_design']['order'].pop(0)  # Remove block from order
            #                 with open(self.parameters['config_file'], 'wb') as config_snap:
            #                     json.dump(self.parameters, config_snap, sort_keys=True, indent=4)
            #                     self.log.info('Stage %s complete!' % self.condition)
            #                     raise EndSession
            try:
                run_trial_queue()
            except EndSession:
                return 'post'

        return 'post'

    def session_post(self):
        """ Closes out the sessions

        """
        self.log.info('ending session')
        return None

    ## trial flow
    def new_trial(self, conditions=None):
        """Creates a new trial and appends it to the trial list

        If `self.do_correction` is `True`, then the conditions are ignored and a new
        trial is created which copies the conditions of the last trial.

        Parameters
        ----------
        conditions : dict
            The conditions dict must have a 'class' key, which specifys the trial
            class. The entire dict is passed to `exp.get_stimuli()` as keyword
            arguments and saved to the trial annotations.

        """
        if len(self.trials) > 0:
            index = self.trials[-1].index + 1
        else:
            index = 0

        if self.do_correction:
            # for correction trials, we want to use the last trial as a template
            trial = utils.Trial(type_='correction',
                                index=index,
                                class_=self.trials[-1].class_)
            for ev in self.trials[-1].events:
                if ev.label is 'wav':
                    trial.events.append(copy.copy(ev))
                    trial.stimulus_event = trial.events[-1]
                    trial.stimulus = trial.stimulus_event.name
                elif ev.label is 'motif':
                    trial.events.append(copy.copy(ev))
            self.log.debug("correction trial: class is %s" % trial.class_)
        else:
            # otherwise, we'll create a new trial
            trial = utils.Trial(index=index)
            trial.class_ = conditions['class']
            trial_stim, trial_motifs = self.get_stimuli(**conditions)
            trial.events.append(trial_stim)
            trial.stimulus_event = trial.events[-1]
            trial.stimulus = trial.stimulus_event.name
            # for mot in trial_motifs:
            #     trial.events.append(mot)

        trial.session = self.session_id
        trial.annotate(**conditions)

        trial.subject = self.parameters['subject']
        trial.block = self.parameters['block_design']['order'][trial.session - 1]

        self.trials.append(trial)
        self.this_trial = self.trials[-1]
        self.this_trial_index = self.trials.index(self.this_trial)
        self.log.debug("trial %i: %s, %s" % (self.this_trial.index, self.this_trial.type_, self.this_trial.class_))

        return True

    def get_stimuli(self, **conditions):
        """ Get the trial's stimuli from the conditions

        Returns
        -------
        stim, epochs : Event, list 


        """
        # TODO: default stimulus selection
        stim_name = conditions['stim_name']
        stim_file = self.parameters['stims'][stim_name]
        self.log.debug(stim_file)

        stim = utils.auditory_stim_from_wav(stim_file)
        epochs = []
        return stim, epochs

    def analyze_trial(self):
        # Calculate both including and excluding NR trials
        # excluding NR trials
        stats = analysis.Analysis([[self.summary['correct_responses'],
                                    self.summary['misses']],
                                   [self.summary['false_alarms'],
                                    self.summary['correct_rejections']]])
        self.summary['dprime'] = stats.dprime()
        self.summary['bias'] = stats.bias()
        if self.summary['bias'] > 1.001:
            self.summary['bias_description'] = '(Conservative)'
        elif self.summary['bias'] < 0.999:
            self.summary['bias_description'] = '(Liberal)'
        else:
            self.summary['bias_description'] = ''

        # Including NR trials
        stats = analysis.Analysis([[self.summary['correct_responses'],
                                    self.summary['misses'] + self.summary['splus_nr']],
                                   [self.summary['false_alarms'],
                                    self.summary['correct_rejections'] + self.summary['sminus_nr']]])
        self.summary['dprime_NR'] = stats.dprime()
        if self.summary['trials'] < 10:  # bias will be unnecessarily large, so don't calculate
            self.summary['bias_NR'] = 'n/a'
            self.summary['bias_description_NR'] = '(low n)'
        else:
            self.summary['bias_NR'] = stats.bias()
            if self.summary['bias_NR'] > 1.001:
                self.summary['bias_description_NR'] = '(Conservative)'
            elif self.summary['bias_NR'] < 0.999:
                self.summary['bias_description_NR'] = '(Liberal)'
            else:
                self.summary['bias_description_NR'] = ''

    def save_trial(self, trial):
        """write trial results to CSV"""

        trial_dict = {}
        for field in self.fields_to_save:
            try:
                trial_dict[field] = getattr(trial, field)
            except AttributeError:
                trial_dict[field] = trial.annotations[field]

        with open(self.data_csv, 'ab') as data_fh:
            trialWriter = csv.DictWriter(data_fh, fieldnames=self.fields_to_save, extrasaction='ignore')
            trialWriter.writerow(trial_dict)

    def run_trial(self):
        self.trial_pre()

        self.stimulus_pre()
        self.stimulus_main()
        self.stimulus_post()

        self.response_pre()
        self.response_main()
        self.response_post()

        self.consequence_pre()
        self.consequence_main()
        self.consequence_post()

        self.trial_post()

    def trial_pre(self):
        # this is where we initialize a trial
        # make sure lights are on at the beginning of each trial, prep for trial
        self.log.debug('running trial')
        self.log.debug("number of open file descriptors: %d" % (utils.get_num_open_fds()))

        self.this_trial = self.trials[-1]
        min_wait = self.parameters['response_delay']  # delay before response allowed defined in json file
        max_wait = self.this_trial.stimulus_event.duration + self.parameters[
            'response_win']  # wait up to response_win s after stimulus ends
        self.this_trial.annotate(min_wait=min_wait)
        self.this_trial.annotate(max_wait=max_wait)
        self.log.debug('created new trial')
        self.log.debug('min/max wait: %s/%s' % (min_wait, max_wait))

    def trial_post(self):
        # things to do at the end of a trial
        self.this_trial.duration = (dt.datetime.now() - self.this_trial.time).total_seconds()
        self.analyze_trial()
        self.save_trial(self.this_trial)
        self.write_summary()

        utils.wait(self.parameters['intertrial_min'])

        # # determine if next trial should be a correction trial
        # self.do_correction = True
        # if len(self.trials) > 0:
        #     if self.parameters['correction_trials']:
        #         if self.this_trial.correct == True:
        #             self.do_correction = False
        #         elif self.this_trial.response == 'none':
        #             if self.this_trial.type_ == 'normal':
        #                 self.do_correction = self.parameters['no_response_correction_trials']
        #     else:
        #         self.do_correction = False
        # else:
        #     self.do_correction = False

        if not self.check_session_schedule():
            raise EndSession

    def check_performance(self, block_name):
        criteria = self.parameters['block_design']['blocks'][block_name]['criteria']
        perform = analysis.Performance(self.parameters['experiment_path'])
        five_days_ago = dt.datetime.now() - dt.timedelta(days=5)
        perform.filter_data(startdate=five_days_ago, block=block_name)
        perform.summarize('filtered')
        analyzed_data = perform.analyze(perform.summaryData)
        perform_result = perform.check_criteria(analyzed_data, criteria)
        # print perform_result
        return perform_result

    def stimulus_pre(self):
        # wait for bird to peck
        self.log.debug("presenting stimulus %s" % self.this_trial.stimulus)
        self.log.debug("from file %s" % self.this_trial.stimulus_event.file_origin)
        self.try_panel_function(self.panel.speaker.queue, self.this_trial.stimulus_event.file_origin)
        # self.panel.speaker.queue(self.this_trial.stimulus_event.file_origin)
        self.log.debug('waiting for peck...')
        self.try_panel_function(self.panel.trialSens.on)
        # try:
        #     self.panel.trialSens.on()
        # except (ArduinoException, InterfaceError):
        #     self.reconnect_panel()
        #     self.panel.trialSens.on()
        trial_time = None
        while trial_time is None:
            if not self.check_session_schedule():
                self.try_panel_function(self.panel.speaker.stop)
                self.try_panel_function(self.panel.trialSens.off)
                # try:
                #     self.panel.trialSens.off()
                # except (ArduinoException, InterfaceError):
                #     self.reconnect_panel()
                #     self.panel.trialSens.off()
                self.update_adaptive_queue(presented=False)
                raise EndSession
            else:
                trial_time = self.try_panel_function(self.panel.trialSens.poll, timeout=15.0)

        self.this_trial.time = trial_time

        self.try_panel_function(self.panel.trialSens.off)
        # try:
        #     self.panel.trialSens.off()
        # except (ArduinoException, InterfaceError):
        #     self.reconnect_panel()
        #     self.panel.trialSens.off()
        self.this_trial.events.append(utils.Event(name='trialSens',
                                                  label='peck',
                                                  event_time=0.0,
                                                  )
                                      )

        # record trial initiation
        self.summary['trials'] += 1
        if self.this_trial.class_[0:5] == "probe":
            self.summary['probe_trials'] += 1
        self.summary['last_trial_time'] = self.this_trial.time.ctime()
        self.log.info("trial started at %s" % self.this_trial.time.ctime())

    def stimulus_main(self):
        stim_start = dt.datetime.now()
        self.this_trial.stimulus_event.time = (stim_start - self.this_trial.time).total_seconds()
        self.try_panel_function(self.panel.speaker.play)  # already queued in stimulus_pre()

    def stimulus_post(self):
        self.log.debug('waiting %s secs...' % self.this_trial.annotations['min_wait'])
        utils.wait(self.this_trial.annotations['min_wait'])

    # response flow
    def response_pre(self):
        for class_, port in self.class_assoc.items():
            self.try_panel_function(port.on)
            # port.on()
        self.log.debug('waiting for response')

    def response_main(self):
        response_start = dt.datetime.now()
        while True:
            elapsed_time = (dt.datetime.now() - self.this_trial.time).total_seconds()
            response_time = elapsed_time - self.this_trial.stimulus_event.time
            if response_time > self.this_trial.annotations['max_wait']:
                self.try_panel_function(self.panel.speaker.stop)
                # self.panel.speaker.stop()
                self.this_trial.response = 'none'
                self.log.info('no response')
                return
            for class_, port in self.class_assoc.items():
                try:  # Check that Teensy is still connected, and reconnect if necessary
                    trial_response = port.status()
                except (ArduinoException, InterfaceError):  # Trial interrupted by Teensy disconnect, discard trial
                    self.reconnect_panel()
                    self.this_trial.rt = (dt.datetime.now() - response_start).total_seconds()
                    self.try_panel_function(self.panel.speaker.stop)
                    self.this_trial.response = 'ERR'

                    response_event = utils.Event(name=self.parameters['classes'][class_]['component'],
                                                 label='error',
                                                 event_time=elapsed_time,
                                                 )
                    self.this_trial.events.append(response_event)
                    self.log.info('response: %s' % self.this_trial.response)
                    return
                else:
                    if trial_response:
                        self.this_trial.rt = (dt.datetime.now() - response_start).total_seconds()
                        self.try_panel_function(self.panel.speaker.stop)
                        # self.panel.speaker.stop()
                        self.this_trial.response = class_
                        self.summary['responses'] += 1
                        response_event = utils.Event(name=self.parameters['classes'][class_]['component'],
                                                     label='peck',
                                                     event_time=elapsed_time,
                                                     )
                        self.this_trial.events.append(response_event)
                        self.log.info('response: %s' % self.this_trial.response)
                        return
            utils.wait(.010)

    def response_post(self):
        for class_, port in self.class_assoc.items():
            self.try_panel_function(port.off)
            # port.off()

    ## consequence flow
    def consequence_pre(self):
        # Calculate response type, add to total of response types
        if self.this_trial.response == "ERR":
            pass
        elif self.this_trial.class_ == "probePlus":
            self.summary['probe_plus'] += 1

            if self.this_trial.response == "sPlus":
                self.this_trial.correct = True  # Mark correct response to probe as correct
                self.summary['probe_hit'] += 1
                self.this_trial.responseType = "correct_response"
            else:
                self.summary['probe_miss'] += 1
                self.this_trial.responseType = "miss"
                if self.this_trial.response != "sMinus":  # No response
                    self.summary['probe_miss_nr'] += 1

        elif self.this_trial.class_ == "sPlus":
            self.summary['splus_trials'] += 1

            if self.this_trial.response == "sPlus":
                self.this_trial.correct = True  # Mark correct response to probe as correct
                self.summary['correct_responses'] += 1
                self.this_trial.responseType = "correct_response"
            else:
                self.summary['misses'] += 1
                self.this_trial.responseType = "miss"
                if self.this_trial.response != "sMinus":  # No response
                    self.summary['splus_nr'] += 1

        elif self.this_trial.class_ == "probeMinus":
            self.summary['probe_minus'] += 1
            if self.this_trial.response == "sPlus":
                self.summary['probe_FA'] += 1
                self.this_trial.responseType = "false_alarm"
            else:
                self.this_trial.correct = True  # Mark correct response to probe as correct
                self.summary['probe_CR'] += 1
                self.this_trial.responseType = "correct_reject"
                if self.this_trial.response != "sMinus":  # No response
                    # No response
                    self.summary['probe_CR_nr'] += 1

        elif self.this_trial.class_ == "sMinus":
            self.summary['sminus_trials'] += 1
            if self.this_trial.response == "sPlus":
                self.summary['false_alarms'] += 1
                self.this_trial.responseType = "false_alarm"
            else:
                self.this_trial.correct = True  # Mark correct response to probe as correct
                self.summary['correct_rejections'] += 1
                self.this_trial.responseType = "correct_reject"
                if self.this_trial.response != "sMinus":  # No response
                    # No response
                    self.summary['sminus_nr'] += 1

    def consequence_main(self):
        if self.this_trial.response == "ERR":
            pass  # if trial is error, skip consequating and move onto next trial
        # treat probe trials regardless of response
        if self.this_trial.class_[0:5] == "probe":
            # self.reward_pre()
            # self.reward_main()  # provide a reward
            # self.reward_post()
            pass

        else:  # Handling non-probe trials
            # correct response trial
            if self.this_trial.response == 'none':
                # no response
                if self.passiveReward and self.this_trial.class_ == "sPlus":
                    # provide passive reward, even if bird didn't make response
                    self.reward_pre()
                    self.reward_main()  # provide a reward
                    self.reward_post()
                else:
                    pass

            elif self.this_trial.correct:
                if self.secondary_reinf_bool:
                    secondary_reinf_event = self.secondary_reinforcement()
                    self.this_trial.events.append(secondary_reinf_event)

                if self.this_trial.type_ == 'correction':
                    self._run_correction_reward()
                # elif self.this_trial.class_ == 'sMinus':  # correct reject (trial is S- and bird hits trial switch)
                #     pass  # nothing, end trial and move to next
                #     # NOTE: not necessary, since reward/punish_value in json can be set to 0
                elif self.reinf_sched.consequate(trial=self.this_trial):
                    self.reward_pre()
                    self.reward_main()  # provide a reward
                    self.reward_post()

            # incorrect trial
            else:
                self.this_trial.correct = False  # This might be redundant - 12/14/18 AR
                if self.reinf_sched.consequate(trial=self.this_trial):
                    self.punish_pre()
                    self.punish_main()
                    self.punish_post()

    def consequence_post(self):
        self.update_adaptive_queue()

    def update_adaptive_queue(self, presented=True):
        if self.this_trial.type_ == 'normal' and isinstance(self.trial_q, queues.AdaptiveBase):
            if presented:
                self.trial_q.update(self.this_trial.correct, self.this_trial.response == 'none')
            else:
                self.trial_q.update(False, True)

    def secondary_reinforcement(self, value=1.0):
        return self.panel.trialSens.flash(dur=value)

    ## reward flow
    def reward_pre(self):
        pass

    def reward_main(self):
        self.summary['feeds'] += 1
        try:
            value = self.parameters['classes'][self.this_trial.class_]['reward_value']
            self.try_panel_function(self.panel.reward, value=value)
            # try:  # Check that Teensy is still connected, and reconnect if necessary
            #     reward_event = self.panel.reward(value=value)
            # except (ArduinoException, InterfaceError):
            #     self.reconnect_panel()
            #     reward_event = self.panel.reward(value=value)
            self.this_trial.reward = True

        # but catch the reward errors

        ## note: this is quite specific to the Gentner Lab. consider
        ## ways to abstract this
        # except components.HopperAlreadyUpError as err:
        #     self.this_trial.reward = True
        #     self.summary['hopper_already_up'] += 1
        #     self.log.warning("hopper already up on panel %s" % str(err))
        #     utils.wait(self.parameters['classes'][self.this_trial.class_]['reward_value'])
        #     # self.panel.reset()
        #
        # except components.HopperWontComeUpError as err:
        #     self.this_trial.reward = 'error'
        #     self.summary['hopper_failures'] += 1
        #     self.log.error("hopper didn't come up on panel %s" % str(err))
        #     utils.wait(self.parameters['classes'][self.this_trial.class_]['reward_value'])
        #     self.panel.reset()

        # except components.ResponseDuringFeedError as err:
        #     trial['reward'] = 'Error'
        #     self.summary['responses_during_reward'] += 1
        #     self.log.error("response during reward on panel %s" % str(err))
        #     utils.wait(self.reward_dur[trial['class']])
        #     self.panel.reset()

        # except components.HopperWontDropError as err:
        #     self.this_trial.reward = 'error'
        #     self.summary['hopper_wont_go_down'] += 1
        #     self.log.warning("hopper didn't go down on panel %s" % str(err))
        #     # self.panel.reset()

        finally:
            self.try_panel_function(self.panel.house_light.on)
            # try:
            #     self.panel.house_light.on()
            # except (ArduinoException, InterfaceError):
            #     self.reconnect_panel()
            #     self.panel.house_light.on()

    def reward_post(self):
        pass

    def _run_correction_reward(self):
        pass

    ## punishment flow
    def punish_pre(self):
        pass

    def punish_main(self):
        value = self.parameters['classes'][self.this_trial.class_]['punish_value']
        if self.punish_bool:
            self.try_panel_function(self.panel.punish, value=value)
            # try:  # Check that Teensy is still connected, and reconnect if necessary
            #     punish_event = self.panel.punish(value=value)
            # except (InterfaceError, ArduinoException):
            #     self.reconnect_panel()
            #     punish_event = self.panel.punish(value=value)
        self.this_trial.punish = True

    def punish_post(self):
        pass
