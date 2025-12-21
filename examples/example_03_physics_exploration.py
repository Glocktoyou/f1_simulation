
"""
Example 3: Vehicle Physics Exploration

This example shows how to:
1. Analyze aerodynamic forces
2. Calculate tire grip limits
3. Explore load transfer effects
"""

# Ensure src is in sys.path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import numpy as np
from f1_simulation import F1Vehicle


def main():
    print("="*70)
    print("F1 VEHICLE DYNAMICS SIMULATOR - EXAMPLE 3: PHYSICS EXPLORATION")
    print("="*70)
    
    vehicle = F1Vehicle()
    
    # 1. Aerodynamic forces vs speed
    print("\n1. AERODYNAMIC FORCES VS SPEED")
    print("-" * 70)
    print(f"{'Speed (km/h)':<15} {'Drag (kN)':<15} {'Downforce (kN)':<15} {'Total Grip':<15}")
    print("-" * 70)
    
    for speed_kmh in [100, 150, 200, 250, 300, 350]:
        speed_ms = speed_kmh / 3.6
        drag, df_total, df_front, df_rear = vehicle.calculate_aero_forces(speed_ms)
        weight = vehicle.mass * vehicle.g
        total_grip = (weight + df_total) * vehicle.tire_mu_peak / 1000
        print(f"{speed_kmh:<15} {drag/1000:<15.2f} {df_total/1000:<15.2f} {total_grip:<15.1f}")
    
    # 2. Cornering speed limits
    print("\n2. CORNERING SPEED LIMITS")
    print("-" * 70)
    print(f"{'Radius (m)':<15} {'Speed (no aero)':<20} {'Speed (300 km/h)':<20}")
    print("-" * 70)
    
    for radius in [50, 75, 100, 150, 200]:
        # No downforce
        v_static = vehicle.calculate_corner_speed(radius, 0)
        
        # With downforce at 300 km/h
        speed_300 = 300 / 3.6
        _, df_300, _, _ = vehicle.calculate_aero_forces(speed_300)
        v_dynamic = vehicle.calculate_corner_speed(radius, df_300)
        
        print(f"{radius:<15} {v_static*3.6 if v_static != np.inf else 'inf':<20.0f} {v_dynamic*3.6:<20.1f}")
    
    # 3. Load transfer effects
    print("\n3. LOAD TRANSFER DURING ACCELERATION")
    print("-" * 70)
    print(f"{'Accel (m/s²)':<15} {'Front Load (N)':<20} {'Rear Load (N)':<20} {'Load Transfer':<15}")
    print("-" * 70)
    
    for accel in [0, 5, 10, 15, 20]:
        f_load, r_load = vehicle.get_axle_normal_loads(accel, 0)
        transfer = (r_load - f_load) / 2
        print(f"{accel:<15} {f_load:<20.0f} {r_load:<20.0f} {transfer:<15.0f}")
    
    # 4. Tire friction vs normal load
    print("\n4. TIRE FRICTION COEFFICIENT vs LOAD")
    print("-" * 70)
    print(f"{'Normal Load (N)':<20} {'Friction μ':<20} {'Max Tire Force (N)':<20}")
    print("-" * 70)
    
    for load in [2000, 3000, 4000, 5000, 6000]:
        mu = vehicle._tire_mu_vs_normal(load)
        max_force = mu * load
        print(f"{load:<20} {mu:<20.3f} {max_force:<20.0f}")
    
    # 5. Powertrain performance
    print("\n5. POWERTRAIN PERFORMANCE")
    print("-" * 70)
    print(f"{'Speed (km/h)':<15} {'Power (kW)':<15} {'Max Force (kN)':<15} {'Max Accel (m/s²)':<15}")
    print("-" * 70)
    
    weight = vehicle.mass * vehicle.g
    
    for speed_kmh in [0, 100, 150, 200, 250]:
        speed_ms = speed_kmh / 3.6
        if speed_ms > 1:
            power = vehicle.max_power
            force = power / speed_ms / 1000
        else:
            force = vehicle.tire_mu_peak * weight / 1000
            power = 0
        
        max_accel = (force * 1000) / vehicle.mass
        print(f"{speed_kmh:<15} {power/1000:<15.0f} {force:<15.1f} {max_accel:<15.1f}")
    
    # 6. DRS effect
    print("\n6. DRS EFFECT (DRAG REDUCTION SYSTEM)")
    print("-" * 70)
    print(f"{'Speed (km/h)':<15} {'Drag Off (kN)':<20} {'Drag On (kN)':<20} {'Speed Gain (km/h)':<15}")
    print("-" * 70)
    
    for speed_kmh in [200, 250, 300, 350]:
        speed_ms = speed_kmh / 3.6
        drag_off, _, _, _ = vehicle.calculate_aero_forces(speed_ms, drs=False)
        drag_on, _, _, _ = vehicle.calculate_aero_forces(speed_ms, drs=True)
        
        # Estimate speed gain from drag reduction
        # At high speed, power limited: F = P/v, so if F_drag reduces, v increases
        power = vehicle.max_power
        v_off = power / drag_off
        v_on = power / drag_on
        speed_gain = (v_on - v_off) * 3.6
        
        print(f"{speed_kmh:<15} {drag_off/1000:<20.1f} {drag_on/1000:<20.1f} {speed_gain:<15.1f}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
