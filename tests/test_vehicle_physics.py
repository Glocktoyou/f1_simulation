import numpy as np
import pytest

from f1_simulation import F1Vehicle


def test_axle_loads_sum():
    veh = F1Vehicle()
    f, r = veh.get_axle_normal_loads(0.0, 0.0)
    total = f + r
    assert total == pytest.approx(veh.mass * veh.g, rel=1e-6)


def test_axle_loads_longitudinal_transfer():
    veh = F1Vehicle()
    f0, r0 = veh.get_axle_normal_loads(0.0, 0.0)
    f1, r1 = veh.get_axle_normal_loads(5.0, 0.0)  # positive longitudinal accel -> rear load increases
    assert r1 > r0
    assert f1 < f0


def test_combined_tire_force_limits():
    veh = F1Vehicle()
    normal = 4000.0  # N
    fx, fy = veh.calculate_combined_tire_force(0.2, 0.3, normal)
    combined = np.hypot(fx, fy)
    # Allow a small numerical tolerance when comparing to peak friction*normal
    assert combined <= (veh.tire_mu_peak * normal) + 1e-6


def test_aero_drs_effect():
    veh = F1Vehicle()
    v = 50.0
    drag0, total0, df0, dr0 = veh.calculate_aero_forces(v, drs=False)
    drag1, total1, df1, dr1 = veh.calculate_aero_forces(v, drs=True)
    assert drag1 < drag0
    assert dr1 < dr0
    assert total1 <= total0 + 1e-9


def test_max_acceleration_positive():
    veh = F1Vehicle()
    a = veh.calculate_max_acceleration(10.0, 0.0)
    assert a >= 0
