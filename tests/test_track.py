import numpy as np
import pytest

from f1_realtrack_tiremodel import RealF1Track, create_silverstone, create_monaco, create_spa


def test_add_and_get_segment():
    t = RealF1Track("test", 1000, 60, "A", 2020)
    t.add_segment("s1", 100, radius=50, segment_type='corner')
    t.add_segment("s2", 200, radius=np.inf, segment_type='straight')
    assert t.total_length == 300

    seg1 = t.get_segment_at_distance(50)
    assert seg1['name'] == 's1'

    seg2 = t.get_segment_at_distance(150)
    assert seg2['name'] == 's2'

    seg_last = t.get_segment_at_distance(1000)
    assert seg_last['name'] == 's2'


def test_create_tracks_lengths():
    s = create_silverstone()
    m = create_monaco()
    sp = create_spa()

    assert s.total_length > 0
    assert m.total_length > 0
    assert sp.total_length > 0

    # sanity: total_length equals sum of segment lengths
    assert abs(s.total_length - sum(seg['length'] for seg in s.segments)) < 1e-6
