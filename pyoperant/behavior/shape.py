import random
import datetime as dt
from pyoperant import panels
from pyoperant import utils


class Shaper(object):
    """
    Run a shaping routine in the operant chamber that will teach an
    to peck the center key to hear a stimulus, then peck one of the side keys for reward.
    training sequence:
    Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
              that the animal is in the apparatus. Center key flashes for 5 sec, prior
              to the hopper access. If the center key is pressed while flashing, then
              the hopper comes up and then the session jumps to block 2 immediately.
    Block 2:  The center key flashes until pecked.  When pecked the hopper comes up for
              4 sec. Run 100 trials.
    Block 3:  The center key flashes until pecked, then either the right or left (p = .5)
              key flashes until pecked, then the hopper comes up for 3 sec. Run 100 trials.
    Block 4:  Wait for peck to non-flashing center key, then right or left key flashes
              until pecked, then food for 2.5 sec.   Run 100 trials."""

    def __init__(self, panel, log, parameters, error_callback=None):
        self.panel = panel
        assert isinstance(panel, panels.BasePanel)
        self.log = log
        assert log is not None
        self.parameters = parameters
        assert 'light_schedule' in self.parameters
        self.error_callback = error_callback
        self.recent_state = 0
        self.last_response = None
        self.block1 = self._null_block(1)
        self.block2 = self._null_block(2)
        self.block3 = self._null_block(3)
        self.block4 = self._null_block(4)
        self.block5 = self._null_block(5)

    def run_shape(self, start_in='block1'):
        self.log.warning('Starting shaping procedure')
        utils.run_state_machine(start_in='block1',
                                error_state='block1',
                                error_callback=self.error_callback,
                                block1=self.block1,
                                block2=self.block2,
                                block3=self.block3,
                                block4=self.block4,
                                block5=self.block5,
                                sleep_block=self._run_sleep)
        self.log.warning('Shaping procedure complete.  Remember to disable shaping in your config file')

    def _null_block(self, block_num):
        def temp():
            return self.block_name(block_num + 1)

        return temp

    def _hopper_block(self, block_num):
        """
        Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
        that the animal is in the apparatus. Center key flashes for 5 sec, prior
        to the hopper access. If the center key is pressed while flashing, then
        the hopper comes up and then the session jumps to block 2 immediately"""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('wait'),
                                    wait=self._wait_block(10, 40, 'check'),
                                    check=self._check_block('flash_mid', 1, float('inf')),
                                    flash_mid=self._flash_poll(self.panel.center, 5, 'reward', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(5, 'check2'),
                                    check2=self._check_block('wait', 1, float('inf')))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _center_peck_block(self, block_num, reps=100, revert_timeout=10800):
        """Block 2:  The center key flashes until pecked.  When pecked the hopper comes up for
        4 sec. Run 100 trials.
        reverts to revert_state if no response before timeout (60*60*3=10800)"""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._flash_poll(self.panel.center, 10, 'check', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(4, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp

    def _block_init(self, next_state):
        # Setup block and logging
        def temp():
            self.block_start = dt.datetime.now()
            self.log.info('Block start time: %s' % (self.block_start.isoformat(' ')))
            self.log.info("Blk #\tTrl #\tResp Key\tResp Time")
            self.responded_block = False
            self.response_counter = 0
            return next_state

        return temp

    def _check_block(self, next_state, reps, revert_timeout):
        # If function returns None, state machine ends (I think)
        # None returns when: no response and elapsed time > timeout
        #                    number of actual responses >= reps
        #                    time is outside of light schedule
        def temp():
            if not self.responded_block:
                elapsed_time = (dt.datetime.now() - self.block_start).total_seconds()
                if elapsed_time > revert_timeout:
                    self.log.warning("No response in block %d, reverting to block %d.  Time: %s" % (
                        self.recent_state, self.recent_state - 1, dt.datetime.now().isoformat(' ')))
                    return None
            else:
                if self.response_counter >= reps:
                    return None
            if not utils.check_time(self.parameters['light_schedule']):
                return None
            return next_state

        return temp

    def _pre_reward(self, next_state):
        def temp():
            self.responded_block = True
            self.response_counter = self.response_counter + 1
            return next_state

        return temp

    def _wait_block(self, t_min, t_max, next_state):
        # Wait between t_min and t_max seconds
        def temp():
            if t_min == t_max:
                t = t_max
            else:
                t = random.randrange(t_min, t_max)
            utils.wait(t)
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

    def _poll_dual(self, component1, component2, duration, trial_state, timeout_state=None, resp_state=None,
                   poll_state=None):
        if poll_state is None:  # If no specific poll function specified, run poll without turning component on/off (like if no light)
            poll_state = self._poll_main

        def temp():
            utils.run_state_machine(start_in='init',
                                    init=self._polling_init('main'),
                                    main=poll_state(component1, component2,
                                                    duration))  # loops poll_state until response or timeout
            if self.responded_poll == 1:
                return resp_state
            elif self.responded_poll == 2:
                return trial_state
            else:
                return timeout_state

        return temp

    def _flash_poll(self, component, duration, next_state, reward_state=None):
        return self._poll(component, duration, next_state, reward_state, poll_state=self._flashing_main)

    def _random_poll(self, component, t_min, t_max, next_state, reward_state=None):
        if t_min == t_max:
            t = t_max
        else:
            t = random.randrange(t_min, t_max)
        return self._poll(component, t, next_state, reward_state)

    def _light_poll(self, component, duration, next_state, reward_state=None):
        return self._poll(component, duration, next_state, reward_state, poll_state=self._light_main)

    def _light_poll_dual(self, component1, component2, duration, trial_state, timeout_state, resp_state=None):
        return self._poll_dual(component1, component2, duration, trial_state, timeout_state, resp_state,
                               poll_state=self._light_dual)

    def _punish_main(self, component, duration, next_state):
        def temp():
            component.off()
            utils.wait(duration)
            component.on()
            return next_state

        return temp

    def _polling_init(self, next_state):
        def temp():
            self.polling_start = dt.datetime.now()
            self.responded_poll = False
            self.last_response = None
            return next_state

        return temp

    # TODO: remake to not hog CPU
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

    def _flashing_main(self, component, duration, period=1):
        def temp():
            elapsed_time = (dt.datetime.now() - self.polling_start).total_seconds()
            if elapsed_time <= duration:
                if ((elapsed_time % period) - (period / 2.0)) < 0:
                    component.on()
                else:
                    component.off()
                if component.status():
                    component.off()
                    self.responded_poll = True
                    self.last_response = component.name
                    return None
                utils.wait(.015)
                return 'main'
            else:
                component.off()
                return None

        return temp

    def _light_main(self, component, duration):
        def temp():
            elapsed_time = (dt.datetime.now() - self.polling_start).total_seconds()
            if elapsed_time <= duration:
                component.on()
                if component.status():
                    component.off()
                    self.responded_poll = True
                    self.last_response = component.name
                    return None
                utils.wait(.015)
                return 'main'
            else:
                component.off()
                return None

        return temp

    def _light_dual(self, component1, component2, duration):
        def temp():
            elapsed_time = (dt.datetime.now() - self.polling_start).total_seconds()
            if elapsed_time <= duration:
                component1.on()
                component2.on()
                if component1.status():
                    component1.off()
                    self.responded_poll = 1
                    self.last_response = component1.name
                    return None
                if component2.status():
                    component2.off()
                    self.responded_poll = 2
                    self.last_response = component2.name
                    return None
                utils.wait(.015)
                return 'main'
            else:
                component1.off()
                component2.off()
                return None

        return temp

    # TODO: catch errors here
    def reward(self, value, next_state):
        def temp():
            self.log.info('%d\t%d\t%s\t%s' % (
                self.recent_state, self.response_counter, self.last_response, dt.datetime.now().isoformat(' ')))
            self.panel.reward(value=value)
            return next_state

        return temp

    def _rand_state(self, states):
        def temp():
            return random.choice(states)

        return temp

    # defining functions for sleep
    # TODO: there should really be a separate sleeper or some better solution
    def sleep_pre(self):
        self.log.debug('lights off. going to sleep...')
        return 'main'

    def sleep_main(self):
        """ reset expal parameters for the next day """
        self.log.debug('sleeping...')
        self.panel.house_light.off()
        utils.wait(self.parameters['idle_poll_interval'])
        if not utils.check_time(self.parameters['light_schedule']):
            return 'main'
        else:
            return 'post'

    def sleep_post(self):
        self.log.debug('ending sleep')
        self.panel.house_light.on()
        #        self.init_summary()
        return None

    def _run_sleep(self):
        utils.run_state_machine(start_in='pre',
                                error_state='post',
                                error_callback=self.error_callback,
                                pre=self.sleep_pre,
                                main=self.sleep_main,
                                post=self.sleep_post)
        return self.block_name(self.recent_state)

    def block_name(self, block_num):
        if 1 <= block_num <= 5:
            return "block%d" % block_num
        else:
            return None


class Shaper2AC(Shaper):
    """Run a shaping routine in the operant chamber that will teach an
    to peck the center key to hear a stimulus, then peck one of the side keys for reward.
    training sequence:
    Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
              that the animal is in the apparatus. Center key flashes for 5 sec, prior
              to the hopper access. If the center key is pressed while flashing, then
              the hopper comes up and then the session jumps to block 2 immediately.
    Block 2:  The center key flashes until pecked.  When pecked the hopper comes up for
              4 sec. Run 100 trials.
    Block 3:  The center key flashes until pecked, then either the right or left (p = .5)
              key flashes until pecked, then the hopper comes up for 3 sec. Run 100 trials.
    Block 4:  Wait for peck to non-flashing center key, then right or left key flashes
              until pecked, then food for 2.5 sec.   Run 100 trials."""

    def __init__(self, panel, log, parameters, error_callback=None):
        super(Shaper2AC, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._hopper_block(1)
        self.block2 = self._center_peck_block(2)
        self.block3 = self._response_2ac_block(3)
        self.block4 = self._response_2ac_no_flash_block(4)

    def _response_2ac_block(self, block_num, reps=100, revert_timeout=10800):

        """Block 3:  The center key flashes until pecked, then either the right or left (p = .5)
        key flashes until pecked, then the hopper comes up for 3 sec. Run 100 trials."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._flash_poll(self.panel.center, 10, 'check', 'coin_flip'),
                                    coin_flip=self._rand_state(('check_right', 'check_left')),
                                    check_right=self._check_block('poll_right', reps, revert_timeout),
                                    poll_right=self._flash_poll(self.panel.right, 10, 'check_right', 'pre_reward'),
                                    check_left=self._check_block('poll_left', reps, revert_timeout),
                                    poll_left=self._flash_poll(self.panel.left, 10, 'check_left', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(3, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp

    def _response_2ac_no_flash_block(self, block_num, reps=100, revert_timeout=10800):
        """Block 4:  Wait for peck to non-flashing center key, then right or left key flashes
        until pecked, then food for 2.5 sec.   Run 100 trials."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._poll(self.panel.center, 10, 'check', 'coin_flip'),
                                    coin_flip=self._rand_state(('check_right', 'check_left')),
                                    check_right=self._check_block('poll_right', reps, revert_timeout),
                                    poll_right=self._flash_poll(self.panel.right, 10, 'check_right', 'pre_reward'),
                                    check_left=self._check_block('poll_left', reps, revert_timeout),
                                    poll_left=self._flash_poll(self.panel.left, 10, 'check_left', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(2.5, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp


class ShaperGoNogo(Shaper):
    """accomodate go/nogo terminal procedure along with one or two hopper 2choice procedures
    Go/Nogo shaping works like this:
    Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
              that the animal is in the apparatus. Center key flashes for 5 sec, prior
              to the hopper access. If the center key is pressed while flashing, then
              the hopper comes up and then the session jumps to block 2 immediately.
    Block 2:  The center key flashes until pecked.  When pecked the hopper comes up for
              4 sec. Run 100 trials.
    Block 3:  Wait for a peck to non-flashing center key, when you get it, the hopper
              comes up for 2.5 sec. Run 100 trials.
    NOTE:     when you run the go/nog procedure in a 2 hopper apparatus, it uses only the
              right hand key and hopper.  If you do this often, you may want to add the
              facility for use of the left hand key and hopper."""

    def __init__(self, panel, log, parameters, error_callback=None):
        super(ShaperGoNogo, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._hopper_block(1)
        self.block2 = self._center_peck_block(2)
        self.block3 = self._center_peck_no_flash_block(3)

    def _center_peck_no_flash_block(self, block_num):
        raise NotImplementedError


class ShaperFemalePref(Shaper):
    """run a shaping routine for female pecking preferencein the operant chamber
    termial proc: peck one of the side keys for stimulus presentation followed by reward.
    Training sequence invoked as:
    Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
              that the animal is in the apparatus.
              Left and right keylights flash for 5 sec, prior
              to the hopper access. If either L or R key is pressed while flashing, then
              the hopper comes up and the session jumps to block 2 immediately.
    Block 2:  randomly choose either L or R key to flash until pecked.  When pecked the hopper
              comes up for 4 sec.
    Block 3:  Wait for peck to non-flashing L or R key (chosen at random). When pecked,
              give food for 2.5 sec."""

    def __init__(self, panel, log, parameters, error_callback=None):
        super(ShaperFemalePref, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._hopper_block(1)
        self.block2 = self._female_choice_block(2)
        self.block3 = self._female_choice_no_flash_block(3)

    def _female_choice_block(self, block_num):
        raise NotImplementedError

    def _female_choice_no_flash_block(self, block_num):
        raise NotImplementedError


class Shaper3AC(Shaper):
    """run a shaping routine for 3AC the operant chamber
    termial proc: peck center key for stimulus presentation then peck one of three keys L-C-R, or give no response.
    Training sequence invoked as:
    Block 1:  Hopper comes up on VI (stays up for 5 s) for the first day
              that the animal is in the apparatus. Center key flashes for 5 sec, prior
              to the hopper access. If the center key is pressed while flashing, then
              the hopper comes up and then the session jumps to block 2 immediately.
    Block 2:  The center key flashes until pecked.  When pecked the hopper comes up for
              4 sec. Run 100 trials.
    Block 3:  The center key flashes until pecked, then either the right, left, or center
              key flashes (p=0.333) until pecked, then the hopper comes up for 3 sec. Run 150 trials.
    Block 4:  Wait for peck to non-flashing center key, then right, center,or left key flashes
              until pecked, then food for 2.5 sec.   Run 150 trials."""

    def __init__(self, panel, log, parameters, error_callback=None):
        super(Shaper3AC, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._hopper_block(1)
        self.block2 = self._center_peck_block(2)
        self.block3 = self._response_3ac_block(3)
        self.block4 = self._response_3ac_no_flash_block(4)

    def _response_3ac_block(self, block_num, reps=100, revert_timeout=10800):
        """Block 3:  The center key flashes until pecked, then either the right, left, or center
        key flashes (p=0.333) until pecked, then the hopper comes up for 3 sec. Run 150 trials."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._flash_poll(self.panel.center, 10, 'check', 'coin_flip'),
                                    coin_flip=self._rand_state(('check_right', 'check_center', 'check_left')),
                                    check_right=self._check_block('poll_right', reps, revert_timeout),
                                    poll_right=self._flash_poll(self.panel.right, 10, 'check_right', 'pre_reward'),
                                    check_center=self._check_block('poll_center', reps, revert_timeout),
                                    poll_center=self._flash_poll(self.panel.center, 10, 'check_center', 'pre_reward'),
                                    check_left=self._check_block('poll_left', reps, revert_timeout),
                                    poll_left=self._flash_poll(self.panel.left, 10, 'check_left', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(3, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp

    def _response_3ac_no_flash_block(self, block_num, reps=150, revert_timeout=10800):
        """Block 4:  Wait for peck to non-flashing center key, then right, center,or left key flashes
        until pecked, then food for 2.5 sec.   Run 150 trials."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._poll(self.panel.center, 10, 'check', 'coin_flip'),
                                    coin_flip=self._rand_state(('check_right', 'check_center', 'check_left')),
                                    check_right=self._check_block('poll_right', reps, revert_timeout),
                                    poll_right=self._flash_poll(self.panel.right, 10, 'check_right', 'pre_reward'),
                                    check_center=self._check_block('poll_center', reps, revert_timeout),
                                    poll_center=self._flash_poll(self.panel.center, 10, 'check_center', 'pre_reward'),
                                    check_left=self._check_block('poll_left', reps, revert_timeout),
                                    poll_left=self._flash_poll(self.panel.left, 10, 'check_left', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(2.5, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp


class Shaper3ACMatching(Shaper3AC):
    def __init__(self, panel, log, parameters, get_stimuli, error_callback=None):
        super(Shaper3AC, self).__init__(panel, log, parameters, error_callback)
        assert hasattr(get_stimuli, '__call__')
        self.get_stimuli = get_stimuli
        self.block5 = self._response_3ac_matching_audio_block(5)

    def _response_3ac_matching_audio_block(self, block_num, reps=150, revert_timeout=10800):
        def temp():
            self.recent_state = block_num
            self.log.info('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='check',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_mid', reps, revert_timeout),
                                    poll_mid=self._poll(self.panel.center, 10, 'check', 'coin_flip'),
                                    coin_flip=self._rand_state(('check_right', 'check_center', 'check_left')),
                                    check_right=self._check_block('audio_right', reps, revert_timeout),
                                    audio_right=self._play_audio('poll_right', 'R'),
                                    poll_right=self._flash_poll(self.panel.right, 10, 'check_right', 'close_audio'),
                                    check_center=self._check_block('audio_center', reps, revert_timeout),
                                    audio_center=self._play_audio('poll_center', 'C'),
                                    poll_center=self._flash_poll(self.panel.center, 10, 'check_center', 'close_audio'),
                                    check_left=self._check_block('audio_left', reps, revert_timeout),
                                    audio_left=self._play_audio('poll_left', 'L'),
                                    poll_left=self._flash_poll(self.panel.left, 10, 'check_left', 'close_audio'),
                                    close_audio=self._close_audio('pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(2.5, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            if self.responded_block:
                return self.block_name(block_num + 1)
            else:
                return self.block_name(block_num - 1)

        return temp

    def _play_audio(self, next_state, trial_class):
        def temp():
            trial_stim, trial_motifs = self.get_stimuli(trial_class)
            self.log.debug("presenting stimulus %s" % trial_stim.name)
            self.panel.speaker.queue(trial_stim.file_origin)
            self.panel.speaker.play()
            return next_state

        return temp

    def _close_audio(self, next_state):
        def temp():
            self.panel.speaker.stop()
            return next_state

        return temp


class ShaperGoNogoInterrupt(Shaper):
    """accomodate go/nogo terminal procedure along with one or two hopper 2choice procedures
    Go/Nogo shaping works like this:
    Block 1:  Water opens (for 2 s) for the first day that the animal is in the apparatus at random intervals.
    Block 2:  Playbacks begin when w.
    Block 4:  Wait for a peck to non-flashing center key, when you get it, the hopper
              comes up for 2.5 sec. Run 100 trials.
    NOTE:     when you run the go/nog procedure in a 2 hopper apparatus, it uses only the
              right hand key and hopper.  If you do this often, you may want to add the
              facility for use of the left hand key and hopper."""

    def __init__(self, panel, log, parameters, error_callback=None):
        super(ShaperGoNogoInterrupt, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._water_trainer2(1)
        # self.block2 = self._water_block(2)
        # self.block3 = self._water_block_no_passive(3)
        # self.block4 = self._center_peck_no_passive(4)

    def _water_trainer(self, block_num, reps=500):
        """
        Block 1:  Water is frequently dispensed from the port to train the bird that water
        is available in that location.  No light used."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('wait', 100, float('inf')),
                                    # next_state, reps, revert_timeout
                                    wait=self._wait_block(10, 40, 'pre_reward'),  # wait between 10 and 40 seconds
                                    # silent_resp=self._random_poll(self.panel.respSens, 10, 40, 'reward', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(1, 'check'))  # Reward for 1 second
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_trainer2(self, block_num, reps=10000):
        """
        Block 1:  Water is frequently dispensed from the port to train the bird that water
        is available in that location. If resp port accessed, water also dispensed. No light used."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('silent_resp', reps, float('inf')),
                                    # next_state, reps, revert_timeout
                                    # wait=self._wait_block(10, 40, 'reward'),  # wait between 10 and 40 seconds
                                    silent_resp=self._random_poll(self.panel.respSens, 10, 40, 'reward', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(1, 'check'))  # Reward for 1 second
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block_flash(self, block_num):
        """
        Block 2:  Trial light flashes.
        Playback starts when switch is pressed. Both switches are inactive for first 200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback, or passively at end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('wait'),
                                    wait=self._wait_block(10, 40, 'check'),
                                    check=self._check_block('flash_mid', 1, float('inf')),
                                    flash_mid=self._flash_poll(self.panel.trialSens, 5, 'reward', 'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.2, 'check2'),
                                    check2=self._check_block('wait', 1, float('inf')))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block(self, block_num, reps=5000):
        """
        Block 3:  Trial light turns on. Playback starts when switch is pressed. Both switches are inactive for first
        200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback, or passively at end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_trial', reps, float('inf')),
                                    poll_trial=self._light_poll(self.panel.trialSens, 10, 'check',
                                                                'coin_flip'),  # poll for 10 on loop
                                    coin_flip=self._rand_state(('audio_sPlus', 'audio_sMinus')),
                                    audio_sPlus=self._play_audio('sPlus_pause_buffer', 'sPlus'),
                                    sPlus_pause_buffer=self._wait_block(.2, .2, 'sPlus_trial'),
                                    sPlus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 5,
                                                                      'trialResp_sPlus_stop', 'no_resp_sPlus_stop'
                                                                                              'respResp_sPlus_stop'),
                                    trialResp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sPlus_stop=self._close_audio('reward'),
                                    respResp_sPlus_stop=self._close_audio('pre_reward'),
                                    audio_sMinus=self._play_audio('sMinus_pause_buffer', 'sMinus'),
                                    sMinus_pause_buffer=self._wait_block(.2, .2, 'sMinus_trial'),
                                    sMinus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 5,
                                                                       'trialResp_sMinus_stop', 'no_resp_sMinus_stop'
                                                                                                'respResp_sMinus_stop'),
                                    trialResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.5, 'trial_end_wait'),
                                    trial_end_wait=self._wait_block(.2, .2, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block_no_passive(self, block_num, reps=200):
        """
        Block 4:  Trial light turns on. Playback starts when switch is pressed. Both switches are inactive for first
        200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback or up to 5 s after playback end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_trial', reps, float('inf')),
                                    poll_trial=self._light_poll(self.panel.trialSens, 10, 'check',
                                                                'coin_flip'),  # poll for 10 on loop
                                    coin_flip=self._rand_state(('audio_sPlus', 'audio_sMinus')),
                                    audio_sPlus=self._play_audio('sPlus_pause_buffer', 'sPlus'),
                                    sPlus_pause_buffer=self._wait_block(.2, .2, 'sPlus_trial'),
                                    sPlus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 10,
                                                                      'trialResp_sPlus_stop', 'no_resp_sPlus_stop'
                                                                                              'respResp_sPlus_stop'),
                                    trialResp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sPlus_stop=self._close_audio('pre_reward'),
                                    audio_sMinus=self._play_audio('sMinus_pause_buffer', 'sMinus'),
                                    sMinus_pause_buffer=self._wait_block(.2, .2, 'sMinus_trial'),
                                    sMinus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 10,
                                                                       'trialResp_sMinus_stop', 'no_resp_sMinus_stop'
                                                                                                'respResp_sMinus_stop'),
                                    trialResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.5, 'trial_end_wait'),
                                    trial_end_wait=self._wait_block(.1, .1, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block_punish(self, block_num, reps=500):
        """
        Block 4:  Trial light turns on. Playback starts when switch is pressed. Both switches are inactive for first
        200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback or up to 5 s after playback end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_trial', reps, float('inf')),
                                    poll_trial=self._light_poll(self.panel.trialSens, 10, 'check',
                                                                'coin_flip'),  # poll for 10 on loop
                                    coin_flip=self._rand_state(('audio_sPlus', 'audio_sMinus')),
                                    audio_sPlus=self._play_audio('sPlus_pause_buffer', 'sPlus'),
                                    sPlus_pause_buffer=self._wait_block(.2, .2, 'sPlus_trial'),
                                    sPlus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 10,
                                                                      'trialResp_sPlus_stop', 'no_resp_sPlus_stop'
                                                                                              'respResp_sPlus_stop'),
                                    trialResp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sPlus_stop=self._close_audio('pre_reward'),
                                    audio_sMinus=self._play_audio('sMinus_pause_buffer', 'sMinus'),
                                    sMinus_pause_buffer=self._wait_block(.2, .2, 'sMinus_trial'),
                                    sMinus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 10,
                                                                       'trialResp_sMinus_stop', 'no_resp_sMinus_stop'
                                                                                                'respResp_sMinus_stop'),
                                    trialResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sMinus_stop=self._close_audio('sMinus_punish'),
                                    sMinus_punish=self._punish_main(self.panel.house_light, 'trial_end_wait'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.5, 'trial_end_wait'),
                                    trial_end_wait=self._wait_block(.1, .1, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _play_audio(self, next_state, trial_class):
        def temp():
            trial_stim, trial_motifs = self.get_stimuli(trial_class)
            self.log.debug("presenting stimulus %s" % trial_stim.name)
            self.panel.speaker.queue(trial_stim.file_origin)
            self.panel.speaker.play()
            return next_state

        return temp

    def _close_audio(self, next_state):
        def temp():
            self.panel.speaker.stop()
            return next_state

        return temp


class ShaperGoInterruptOneStep(Shaper):
    """accomodate go/nogo terminal procedure along with one or two hopper 2choice procedures
    Single-step operant conditioning to use both the trial start and
    """

    def __init__(self, panel, log, parameters, error_callback=None):
        super(ShaperGoInterruptOneStep, self).__init__(panel, log, parameters, error_callback)
        self.block1 = self._water_block(1)

    def _water_trainer2(self, block_num):
        """
        Block 1:  Water is frequently dispensed from the port to train the bird that water
        is available in that location. If resp port accessed, water also dispensed. No light used."""

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('silent_resp', 100, float('inf')),
                                    # next_state, reps, revert_timeout
                                    # wait=self._wait_block(10, 40, 'reward'),  # wait between 10 and 40 seconds
                                    silent_resp=self._random_poll(self.panel.respSens, 10, 40, 'reward',
                                                                  'pre_reward'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(1, 'check'))  # Reward for 1 second
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block(self, block_num, reps=5000):
        """
        Block 3:  Trial light turns on. Playback starts when switch is pressed. Both switches are inactive for first
        200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback, or passively at end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_trial', reps, float('inf')),
                                    poll_trial=self._light_poll(self.panel.trialSens, 10, 'check',
                                                                'coin_flip'),  # poll for 10 on loop
                                    coin_flip=self._rand_state(('audio_sPlus', 'audio_sMinus')),
                                    audio_sPlus=self._play_audio('sPlus_pause_buffer', 'sPlus'),
                                    sPlus_pause_buffer=self._wait_block(.2, .2, 'sPlus_trial'),
                                    sPlus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 5,
                                                                      'trialResp_sPlus_stop', 'no_resp_sPlus_stop'
                                                                                              'respResp_sPlus_stop'),
                                    trialResp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sPlus_stop=self._close_audio('reward'),
                                    respResp_sPlus_stop=self._close_audio('pre_reward'),
                                    audio_sMinus=self._play_audio('sMinus_pause_buffer', 'sMinus'),
                                    sMinus_pause_buffer=self._wait_block(.2, .2, 'sMinus_trial'),
                                    sMinus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 5,
                                                                       'trialResp_sMinus_stop',
                                                                       'no_resp_sMinus_stop'
                                                                       'respResp_sMinus_stop'),
                                    trialResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.5, 'trial_end_wait'),
                                    trial_end_wait=self._wait_block(.2, .2, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp

    def _water_block_no_passive(self, block_num, reps=200):
        """
        Block 4:  Trial light turns on. Playback starts when switch is pressed. Both switches are inactive for first
        200ms of playback.
        On S+ trials: Water is delivered when reward port is accessed during playback or up to 5 s after playback end
        On both trial types: accessing trial port stops playback and another interaction starts new trial/playback
        """

        def temp():
            self.recent_state = block_num
            self.log.warning('Starting %s' % (self.block_name(block_num)))
            utils.run_state_machine(start_in='init',
                                    error_state='wait',
                                    error_callback=self.error_callback,
                                    init=self._block_init('check'),
                                    check=self._check_block('poll_trial', reps, float('inf')),
                                    poll_trial=self._light_poll(self.panel.trialSens, 10, 'check',
                                                                'coin_flip'),  # poll for 10 on loop
                                    coin_flip=self._rand_state(('audio_sPlus', 'audio_sMinus')),
                                    audio_sPlus=self._play_audio('sPlus_pause_buffer', 'sPlus'),
                                    sPlus_pause_buffer=self._wait_block(.2, .2, 'sPlus_trial'),
                                    sPlus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens, 10,
                                                                      'trialResp_sPlus_stop', 'no_resp_sPlus_stop'
                                                                                              'respResp_sPlus_stop'),
                                    trialResp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sPlus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sPlus_stop=self._close_audio('pre_reward'),
                                    audio_sMinus=self._play_audio('sMinus_pause_buffer', 'sMinus'),
                                    sMinus_pause_buffer=self._wait_block(.2, .2, 'sMinus_trial'),
                                    sMinus_trial=self._light_poll_dual(self.panel.trialSens, self.panel.respSens,
                                                                       10,
                                                                       'trialResp_sMinus_stop',
                                                                       'no_resp_sMinus_stop'
                                                                       'respResp_sMinus_stop'),
                                    trialResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    no_resp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    respResp_sMinus_stop=self._close_audio('trial_end_wait'),
                                    pre_reward=self._pre_reward('reward'),
                                    reward=self.reward(.5, 'trial_end_wait'),
                                    trial_end_wait=self._wait_block(.1, .1, 'check'))
            if not utils.check_time(self.parameters['light_schedule']):
                return 'sleep_block'
            return self.block_name(block_num + 1)

        return temp



    def _play_audio(self, next_state, trial_class):
        def temp():
            trial_stim, trial_motifs = self.get_stimuli(trial_class)
            self.log.debug("presenting stimulus %s" % trial_stim.name)
            self.panel.speaker.queue(trial_stim.file_origin)
            self.panel.speaker.play()
            return next_state

        return temp

    def _close_audio(self, next_state):
        def temp():
            self.panel.speaker.stop()
            return next_state

        return temp
