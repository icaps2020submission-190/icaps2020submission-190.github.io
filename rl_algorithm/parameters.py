from enum import Enum

import numpy as np

from .utils import mydefaultdict


class Parameter(object):


    def update(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        raise NotImplementedError


class Eligibility(Parameter):

    def __init__(self, lambda_, gamma):
        super().__init__()
        self.lambda_ = lambda_
        self.gamma = gamma

        self.traces = mydefaultdict(0.0)

    def get(self, state, action):
        return self.traces[(state, action)]

    def to_zero(self, state, action):
        self.pop(state, action)

    def to_one(self, state, action):
        self.reset_state_action(state, action)

    def reset_state_action(self, state, action):
        self.traces[(state, action)] = 1

    def pop(self, state, action):
        self.traces.pop((state, action))

    def update(self, state, action, *args, **kwargs):
        self.traces[(state, action)] = self.gamma * self.lambda_ * self.traces[(state, action)]
        if self.traces[(state, action)] < 1e-4:
            self.pop(state, action)

    def reset(self):
        self.traces = {}


class Constant(Parameter):
    def __init__(self, c):
        self.c = c

    def get(self, *args, **kwargs):
        return self.c


class DecayType(Enum):
    LINEAR = 'linear'
    MULTIPLICATIVE = 'multiplicative'


class AnnealedParameter(Parameter):
    def __init__(self, start=0.0, end=0.0, decay_steps=10000, decay_factor=0.99, decay_type: DecayType=DecayType.LINEAR):
        """decay_steps applies only if decay_type=LINEAR
        decay_factor applies only if decay_type=MULTIPLICATIVE"""
        assert start >= end and decay_factor < 1.0
        self.start = start
        self.end = end

        self.decay_type = decay_type
        self.decay_steps = decay_steps
        self.decay_factor = decay_factor

        self.cur_value = self.start
        self.linear_decay_step = (start - end)/decay_steps

    def decay_function(self, x):
        if x <= self.end:
            return self.end
        if self.decay_type == DecayType.LINEAR:
            return  \
                x - self.linear_decay_step
        elif self.decay_type == DecayType.MULTIPLICATIVE:
            return self.end if x <= self.end else x*self.decay_factor

    def get(self, *args, **kwargs):
        return self.cur_value

    def update(self, *args, **kwargs):
        self.cur_value = self.decay_function(self.cur_value)


class AlphaVisitDecay(Parameter):
    def __init__(self, action_space):
        self.action_space = action_space
        self.Visits = mydefaultdict(np.zeros(self.action_space.n))

    def get(self, x, a, *args, **kwargs):
        return 1.0/(self.Visits[x][a])

    def update(self, x, a, *args, **kwargs):
        self.incVisits(x, a)

    def setVisits(self, x, a, q):
        self.Visits[x][a] = q

    def getSumVisits(self, x):
        return np.sum(self.Visits[x,:])

    def incVisits(self, x, a):
        self.Visits[x][a] += 1

