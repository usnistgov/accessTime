#!/usr/bin/env python

import random


def expected_psud(p_a, p_r, interval, message_length):
    """
    Evaluate expected probability of successful delivery (PSuD).

    Parameters
    ----------
    p_a : float
        Probability transitioning into a transmitting state.
    p_r : float
        Probability of remaining in a transmitting state.
    interval : float
        How often state transitions are evaluated.
    message_length : float
        Length of message in seconds.

    Returns
    -------
    float:
        Probability that the message was successfully delivered.

    Examples
    --------
    Evaluate the PSuD when P_a = P_r = 0.5, with an interval of 1 for a three
    second long message.

    >>> mcvqoe.simulation.expected_psud(0.5,0.5,1,3)
    """
    exp = (message_length / interval) - 1
    psud = p_a / (1 + p_a - p_r) * (p_r ** exp)
    return psud


class PBI:
    """
    Probabilityiser for simulating probablistic channel drops.

    This class allows simple simulations of a channel that has two states:
    transmitting and not transmitting. Using the probability of returning to
    the transmitting state given it is not transmitting, P_a, and the
    probability of remaining in the transmitting state given it is
    transmitting, P_r, a faulty channel can be simulated.

    Parameters
    ----------
    P_a1 : float, optional
        Probability of initializing the transmission. The default is 1.
    P_a2 : float, optional
        Probability of returning ot a transmitting state once the transmitting
        state has been reached and it has returned to a non-transmitting
        state. The default is None. In this case P_a2 is set to be equal to
        P_a1.
    P_r : float, optional
        Probability of remaining in a transmitting state. The default is 1.
    interval : float, optional
        How often the channel state is reevaluated, in seconds. The default is
        1.

    Attributes
    ----------
    P_a1 : float, optional
        Probability of initializing the transmission. The default is 1.
    P_a2 : float, optional
        Probability of returning ot a transmitting state once the transmitting
        state has been reached and it has returned to a non-transmitting
        state. The default is None. In this case P_a2 is set to be equal to
        P_a1.
    P_r : float, optional
        Probability of remaining in a transmitting state. The default is 1.
    interval : float, optional
        How often the channel state is reevaluated, in seconds. The default is
        1.
    state : int
        Current state of PBI, either INVALID, G0, G1, or H (0,1,2,3
        respectively).
    state_history : list
        List of transmitting states that the PBI has been in at each interval
        cycle. Values of 0 represent non-transmitting states, values of 1
        represent transmitting states.
    STATE_INVALID : int
        Value 0 to represent invalid state reached
    STATE_G0 : int
        Value 1 to represent in initial state where transmission has not
        started.
    STATE_G1 : int
        Value 2 to represent in non-transmitting state where transmission has
        occured at least once.
    STATE_H : int
        Value 3 to represent in transmitting state.

    Returns
    -------
    None.

    Examples
    --------
    >>> pb = mcvqoe.simulation.PBI(P_a1 = 0.5, P_r = 0.5)
    """

    STATE_INVALID = 0
    STATE_G0 = 1
    STATE_G1 = 2
    STATE_H = 3

    def __init__(self, P_a1=1, P_a2=None, P_r=1, interval=1):
        # time in seconds between state machine evaluations
        self.interval = interval
        self.initial_state()
        self.P_a1 = P_a1
        if P_a2 is None:
            self.P_a2 = self.P_a1
        else:
            self.P_a2 = P_a2
        self.P_r = P_r
        self.state_history = []

    def initial_state(self):
        self.state = self.STATE_G0

    def process_audio(self, data, fs):
        # Numpy arrays pass by reference, and the result of scipy.io.wavfile.read is read-only
        data = data.copy()

        # set to initial state
        self.initial_state()

        # calculate the number of samples in each chunk
        chunk_len = int(round(fs * self.interval))

        start = range(0, len(data), chunk_len)
        stop = list(range(chunk_len, len(data), chunk_len))
        # add end of array to stop
        stop.append(len(data))

        for s, e in zip(start, stop):
            self.update_state()
            if self.state != self.STATE_H:
                data[s:e] = 0
                self.state_history.append(0)
            else:
                self.state_history.append(1)

        return data

    def update_state(self):
        # generate random number for state transition
        r = random.random()
        # select next state based on current state
        if self.state == self.STATE_G0:
            if r < self.P_a1:
                # transition into H state
                self.state = self.STATE_H
            else:
                # stay in G0 state
                pass
        elif self.state == self.STATE_G1:
            if r < self.P_a2:
                # transition into H state
                self.state = self.STATE_H
            else:
                # stay in G1 state
                pass
        elif self.state == self.STATE_H:
            if r < self.P_r:
                # stay in H state
                pass
            else:
                # transition into G1 state
                self.state = self.STATE_G1

    def expected_psud(self, t):
        """
        Determine expected PSuD of message of length t given settings

        Convenience function to use expected_psud function given current PBI
        settings.

        Parameters
        ----------
        t : float
            Length of message in seconds.

        Returns
        -------
        psud : float
              PSuD of message of length t given current settings

        """

        psud = expected_psud(p_a=self.P_a2, p_r=self.P_r, interval=self.interval, message_length=t)
        return psud
