import pytest

from f1_realtrack_tiremodel import validate_against_real_f1


def test_validate_against_real_f1_zero_diff(capsys):
    class DummyTrack:
        def __init__(self):
            self.name = "Dummy"
            self.record_lap_time = 100.0
            self.record_holder = "X"
            self.year = 2020

    t = DummyTrack()
    result = validate_against_real_f1(100.0, t)
    assert result['difference'] == pytest.approx(0.0)
    assert abs(result['error_percent']) < 1e-9
