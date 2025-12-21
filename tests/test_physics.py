import math
import pytest
from f1_simulation import F1Vehicle, Track


def test_aero_forces_reasonable():
    v = 50.0  # m/s (~180 km/h)
    veh = F1Vehicle()
    drag, down_total, df_front, df_rear = veh.calculate_aero_forces(v)
    assert drag > 0
    assert down_total >= df_front
    assert down_total >= df_rear


def test_corner_speed_decreases_with_smaller_radius():
    veh = F1Vehicle()
    down = 0.0
    r_large = 200.0
    r_small = 30.0
    v_large = veh.calculate_corner_speed(r_large, down)
    v_small = veh.calculate_corner_speed(r_small, down)
    assert v_small < v_large


def test_tire_force_scale_with_normal():
    veh = F1Vehicle()
    # small slip angles
    f1 = veh.calculate_tire_force(0.01, 3000)
    f2 = veh.calculate_tire_force(0.02, 3000)
    assert abs(f2) >= abs(f1)
