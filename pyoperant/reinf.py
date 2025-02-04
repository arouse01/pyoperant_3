from numpy import random


class BaseSchedule(object):
    """Maintains logic for deciding whether to consequate trials.

    This base class provides the most basic reinforcent schedule: every
    response is consequated.

    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated. Always returns True.

    """

    def __init__(self):
        super(BaseSchedule, self).__init__()

    def consequate(self, trial):
        assert hasattr(trial, 'correct') and isinstance(trial.correct, bool)
        if trial.correct:
            return True
        else:
            return True


class ContinuousReinforcement(BaseSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This base class provides the most basic reinforcent schedule: every
    response is consequated.

    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated. Always returns True.

    """

    def __init__(self):
        super(ContinuousReinforcement, self).__init__()

    def consequate(self, trial):
        assert hasattr(trial, 'correct') and isinstance(trial.correct, bool)
        if trial.correct:
            return True
        else:
            return True


class FixedRatioSchedule(BaseSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This class implements a fixed ratio schedule, where a reward reinforcement
    is provided after every nth correct response, where 'n' is the 'ratio'.

    Incorrect trials are always reinforced.

    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated.

    """

    def __init__(self, ratio=1):
        super(FixedRatioSchedule, self).__init__()
        self.ratio = max(ratio, 1)
        self._update()

    def _update(self):
        self.cumulative_correct = 0
        self.threshold = self.ratio

    def consequate(self, trial):
        assert hasattr(trial, 'correct') and isinstance(trial.correct, bool)
        if trial.correct:
            self.cumulative_correct += 1
            if self.cumulative_correct >= self.threshold:
                self._update()
                return True
            else:
                return False
        elif not trial.correct:
            self.cumulative_correct = 0
            return True
        else:
            return False

    def __unicode__(self):
        return "FR%i" % self.ratio


class GoInterruptSchedule(BaseSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This class implements a conditional continuous schedule, where reinforcement
    is provided after certain correct and incorrect responses
    Added 6/27/18 by AR for zebra finch isochronicity discrimination experiment.

    Correct Response (Resp switch to S+) = True
    False Alarm (Resp switch to S-) = True
    Miss (NR or Trial switch to S+) = False
    Correct Reject (Trial switch to S-) = False
    Probe trials are always rewarded (but handled in behavior file instead of here)


    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated.

    """

    def __init__(self):
        super(GoInterruptSchedule, self).__init__()

    def consequate(self, trial):
        assert hasattr(trial, 'correct') and isinstance(trial.correct, bool)
        if trial.correct:
            if trial.response == 'sPlus':  # Hit
                return True
            else:
                return False  # Correct reject
        elif not trial.correct:
            if trial.response == 'sPlus':  # False alarm
                return True
            else:
                return False  # Miss
        else:
            return False


class GoInterruptPercentSchedule(BaseSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This class implements a conditional percent reinforcement schedule, where reinforcement
    is provided randomly after certain correct and incorrect responses
    Added 7/9/18 by AR for zebra finch isochronicity discrimination experiment.

    Correct Response (Resp switch to S+) = True by probability
    False Alarm (Resp switch to S-) = True always
    Miss (NR or Trial switch to S+) = False
    Correct Reject (Trial switch to S-) = False
    Probe trials are always rewarded (but handled in behavior file instead of here)


    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated.

    """

    def __init__(self, prob=1):
        super(GoInterruptPercentSchedule, self).__init__()
        self.prob = prob

    def consequate(self, trial):
        if trial.responseType == "correct_response":
            return random.random() < self.prob
        elif trial.responseType == "false_alarm":
            return True
        else:
            return False


class VariableRatioSchedule(FixedRatioSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This class implements a variable ratio schedule, where a reward
    reinforcement is provided after every a number of consecutive correct
    responses. On average, the number of consecutive responses necessary is the
    'ratio'. After a reinforcement is provided, the number of consecutive
    correct trials needed for the next reinforcement is selected by sampling
    randomly from the interval [1,2*ratio-1]. e.g. a ratio of '3' will require
    consecutive correct trials of 1, 2, 3, 4, & 5, randomly.

    Incorrect trials are always reinforced.

    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated.


    """

    def __init__(self, ratio=1):
        super(VariableRatioSchedule, self).__init__(ratio=ratio)

    def _update(self):
        """ update min correct by randomly sampling from interval [1:2*ratio)"""
        self.cumulative_correct = 0
        self.threshold = random.randint(1, 2 * self.ratio)

    def __unicode__(self):
        return "VR%i" % self.ratio


class PercentReinforcement(BaseSchedule):
    """Maintains logic for deciding whether to consequate trials.

    This class implements a probabalistic reinforcement, where a reward reinforcement
    is provided x percent of the time.

    Incorrect trials are always reinforced.

    Methods:
    consequate(trial) -- returns a boolean value based on whether the trial
        should be consequated.

    """

    def __init__(self, prob=1):
        super(PercentReinforcement, self).__init__()
        self.prob = prob

    def consequate(self, trial):
        assert hasattr(trial, 'correct') and isinstance(trial.correct, bool)
        if trial.correct:
            return random.random() < self.prob
        else:
            return True

    def __unicode__(self):
        return "PR%i" % self.prob
