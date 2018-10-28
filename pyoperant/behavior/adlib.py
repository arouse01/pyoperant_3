import random
import os
import datetime as dt
from pyoperant import panels
from pyoperant import utils


class Adlib(object):
    """
    Modified version of shape to facilitate ad-lib reward given on days not scheduled for testing.
    Only one block with infinite trials, but constant checking against schedule.
    """

    def __init__(self, panel, log, parameters, error_callback=None):
        self.init_summary()
        self.panel = panel
        assert isinstance(panel, panels.BasePanel)
        self.log = log
        assert log is not None
        self.parameters = parameters
        assert 'light_schedule' in self.parameters
        self.error_callback = error_callback
        self.recent_state = 0
        self.last_response = None

    def run_adlib(self):
        self.log.warning('Starting ad-lib water procedure')
        utils.run_state_machine(start_in='block1',
                                error_state='block1',
                                error_callback=self.error_callback,
                                block1=self.block1
                                )
        self.log.warning('Stopping ad-lib water procedure.')

    def _block_init(self, next_state):
        # Setup block and logging
        def temp():
            self.block_start = dt.datetime.now()
            self.log.info('Block start time: %s' % (self.block_start.isoformat(' ')))
            self.log.info("Blk #\tTrl #\tResp Key\tResp Time")
            self.responded_block = False
            self.response_counter = 0
            self.trial_counter = 0
            return next_state

        return temp

    def _check_block_log(self, next_state):
        # If function returns None, state machine ends (I think)
        # None returns when: -no response and elapsed time > timeout
        #                    -number of actual responses >= reps
        #                    -time is outside of light schedule
        def temp():
            self.write_summary_adlib()
            self.trial_counter = self.trial_counter + 1
            if not utils.check_time(self.parameters['light_schedule']):  # If lights should be off
                return None  # Break out if lights out
            elif self.check_session_schedule():  # If session should be running
                return None  # Break out of ad-lib cycle and return to base-level control to start session
            else:
                return next_state

        return temp

    def check_session_schedule(self):
        """returns True if the subject should be running sessions"""
        if utils.check_day(self.parameters['session_days']):
            return utils.check_time(self.parameters['session_schedule'])
        return False

    def _pre_reward_log(self, next_state):
        def temp():
            self.responded_block = True
            self.response_counter = self.response_counter + 1
            self.summary['responses'] = self.response_counter
            return next_state

        return temp

    def reward_log(self, value, next_state):
        def temp():
            self.log.info('%d\t%d\t%s\t%s' % (
                self.recent_state, self.response_counter, self.last_response, dt.datetime.now().isoformat(' ')))
            self.panel.reward(value=value)
            self.summary['feeds'] += 1
            self.summary['last_trial_time'] = dt.datetime.now()
            return next_state

        return temp

    def reward(self, value, next_state):
        def temp():
            self.log.info('%d\t%d\t%s\t%s' % (
                self.recent_state, self.response_counter, self.last_response, dt.datetime.now().isoformat(' ')))
            self.panel.reward(value=value)
            return next_state

        return temp

    def _polling_init(self, next_state):
        def temp():
            self.polling_start = dt.datetime.now()
            self.responded_poll = False
            self.last_response = None
            return next_state

        return temp

    def _poll(self, component, duration, next_state, reward_state=None, poll_state=None):
        if poll_state is None:  # If no specific poll function specified, run poll without turning component on/off (like if no light)
            poll_state = self._poll_main

        def temp():
            utils.run_state_machine(start_in='init',
                                    init=self._polling_init('main'),
                                    main=poll_state(component, duration))  # loops poll_state until response or timeout
            if self.responded_poll:
                return reward_state
            else:
                return next_state

        return temp

    def _poll_not(self, component, duration, next_state, reward_state=None):
        # Poll sensor and return value when sensor is *no longer* triggered
        return self._poll(component, duration, next_state, reward_state, poll_state=self._poll_end)

    def _light_poll(self, component, duration, next_state, reward_state=None):
        # Poll sensor and activate light when polling
        return self._poll(component, duration, next_state, reward_state, poll_state=self._light_main)

    # Polling subroutines
    def _poll_main(self, component, duration):
        def temp():
            elapsed_time = (dt.datetime.now() - self.polling_start).total_seconds()
            if elapsed_time <= duration:
                if component.status():
                    self.responded_poll = True
                    self.last_response = component.name
                    return None
                utils.wait(.015)
                return 'main'
            else:
                return None

        return temp

    def _light_main(self, component, duration=15):
        def temp():
            # elapsed_time = (dt.datetime.now() - self.polling_start).total_seconds()
            component.on()
            response = component.poll(timeout=duration)
            if response:
                component.off()
                self.responded_poll = True
                self.last_response = component.name
                return None
            else:
                component.off()
                return None

        return temp

    def _poll_end(self, component, *args):  # Check that component is back to default state
        def temp():
            if not component.status():
                return None
            utils.wait(.015)
            return 'main'

        return temp

    # Defining summary writing
    def init_summary(self):
        """ initializes an empty summary dictionary """
        self.summary = {'trials': 0,
                        'responses': 0,
                        'feeds': 0,
                        'correct_responses': 0,
                        'last_trial_time': [],
                        }

    def write_summary_adlib(self):
        """ takes in a summary dictionary and options and writes to the bird's summaryDAT"""
        summary_file = os.path.join(self.parameters['experiment_path'], self.parameters['subject'] + '.summaryDAT')
        with open(summary_file, 'wb') as f:
            f.write("Ad lib Summary\n\n")
            f.write("Feeds today: %s\n" % self.summary['feeds'])
            f.write("Pecks today: %i" % self.summary['responses'])
            # f.write("Feeder ops today: %i\n" % self.summary['feeds'])
            f.write("\nLast trial @: %s" % self.summary['last_trial_time'])


class ShaperFree(Adlib):
    """
    Special shaping paradigm for providing ad-lib water on non-experimental days (days not listed in the session_days parameter)
    Free water available from response port. Light on resp port is lit while port is accessible.
    """

    def __init__(self, panel, log, parameters, error_callback=None):
        super(ShaperFree, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._water_block()

    # Block logic
    def _water_block(self):
        """
        Block 1:  Water is only dispensed if resp port is accessed. Light on resp port is lit while port is accessible.
        """

        def temp():
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block_log('silent_resp'),
                                    silent_resp=self._light_poll(self.panel.respSens, 30, 'check', 'pre_reward'),
                                    pre_reward=self._pre_reward_log('reward'),
                                    reward=self.reward_log(0.15, 'trial_end'),  # Reward for .15 second
                                    trial_end=self._poll_not(self.panel.respSens, float('inf'), 'check'))
            if not utils.check_time(self.parameters['light_schedule']):  # If lights should be off
                return None  # Break out of ad-lib cycle and return to base-level control for 'sleep' control
            if self.check_session_schedule():  # If session should be starting/running
                return None  # Break out of ad-lib cycle and return to base-level control to start session

        return temp
