"""Low-level tests of the almanac search routines."""

import numpy as np

from skyfield.api import load
from skyfield.constants import tau
from skyfield.searchlib import find_discrete, _find_maxima as find_maxima

bump = 1e-5
epsilon = 1e-10

def make_t():
    ts = load.timescale(builtin=True)
    t0 = ts.tt_jd(0)
    t1 = ts.tt_jd(1)
    return t0, t1

def make_stairstep_f(steps):
    """Return a function that increases by one at each of several `steps`."""
    def f(t):
        # For each time, sum how many of the values in `steps` it surpasses.
        return np.greater_equal.outer(t.tt, steps).sum(axis=1)
    f.rough_period = 1.0
    return f

def is_close(value, expected):
    return (abs(value - expected) < epsilon).all()

def test_find_discrete_near_left_edge():
    t0, t1 = make_t()
    f = make_stairstep_f([bump, 0.5])
    t, y = find_discrete(t0, t1, f, epsilon)
    assert is_close(t.tt, (bump, 0.5))
    assert list(y) == [1, 2]

def test_find_discrete_near_right_edge():
    t0, t1 = make_t()
    f = make_stairstep_f([0.5, 1.0 - bump])
    t, y = find_discrete(t0, t1, f, epsilon)
    assert is_close(t.tt, (0.5, 1.0 - bump))
    assert list(y) == [1, 2]

def test_find_discrete_with_a_barely_detectable_jag_right_at_zero():
    t0, t1 = make_t()
    f = make_stairstep_f([0.5, 0.5 + 3.1 * epsilon])
    t, y = find_discrete(t0, t1, f, epsilon)
    assert is_close(t.tt, (0.5, 0.5 + 3.1 * epsilon))
    assert list(y) == [1, 2]

def test_find_discrete_with_a_sub_epsilon_jag_right_at_zero():
    t0, t1 = make_t()
    f = make_stairstep_f([0.5, 0.5 + 0.99 * epsilon])

    # We hard-code num=12, just in case the default ever changes to
    # another value that might not trigger the symptom.
    t, y = find_discrete(t0, t1, f, epsilon, 12)

    # Note that we always return the last of several close solutions, so
    # that `y` correctly reflects the new state that persists after the
    # flurry of changes is complete.
    assert is_close(t.tt, (0.5 + 0.99 * epsilon,))
    assert list(y) == [2]

def make_mountain_range_f(peaks):
    """Return a function with local maxima at each of a series of `peaks`."""
    def f(t):
        # For each time, sum how many of the values in `steps` it surpasses.
        return -abs(np.subtract.outer(t.tt, peaks)).min(axis=1)
    f.rough_period = 1.0
    return f

def test_finding_maxima_near_edges():
    t0, t1 = make_t()
    f = make_mountain_range_f([bump, 1.0 - bump])
    t, y = find_maxima(t0, t1, f, epsilon, 12)
    assert is_close(t.tt, (bump, 1.0 - bump))
    assert is_close(y, 0.0)

def test_not_finding_maxima_slightly_beyond_range():
    t0, t1 = make_t()
    f = make_mountain_range_f([-bump, 1.0 + bump])
    t, y = find_maxima(t0, t1, f, epsilon, 12)
    assert len(t.tt) == 0
    assert len(y) == 0