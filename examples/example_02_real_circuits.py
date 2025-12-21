
"""
Example 2: Real Circuit Analysis

This example shows how to:
1. Simulate multiple real F1 circuits
2. Compare accuracy against real lap records
3. Analyze circuit characteristics
"""

# Ensure src is in sys.path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pandas as pd
from f1_simulation import F1Vehicle
from f1_realtrack_tiremodel import (
    create_silverstone, create_monaco, create_spa,
    simulate_real_track, validate_against_real_f1
)


def main():
    print("="*70)
    print("F1 VEHICLE DYNAMICS SIMULATOR - EXAMPLE 2: REAL CIRCUITS")
    print("="*70)
    
    # Create vehicle
    vehicle = F1Vehicle()
    print(f"\nVehicle: {vehicle.mass}kg, {vehicle.max_power/745.7:.0f}HP")
    
    # Define circuits
    circuits = {
        'Silverstone': create_silverstone(),
        'Monaco': create_monaco(),
        'Spa': create_spa()
    }
    
    results = {}
    
    # Simulate each circuit
    for circuit_name, track in circuits.items():
        print(f"\n{'='*70}")
        print(f"Simulating {circuit_name}...")
        print(f"{'='*70}")
        
        print(f"  Length: {track.length/1000:.2f} km")
        print(f"  F1 Record: {track.record_lap_time:.3f}s ({track.record_holder})")
        
        # Run simulation
        telemetry, lap_time = simulate_real_track(vehicle, track)
        
        # Validate
        validation = validate_against_real_f1(lap_time, track)
        results[circuit_name] = {
            'sim_time': lap_time,
            'real_time': track.record_lap_time,
            'error_pct': validation['error_percent']
        }
        
        # Print stats
        print(f"\n  Simulation Results:")
        print(f"    Predicted lap time: {lap_time:.3f}s")
        print(f"    Difference: {lap_time - track.record_lap_time:+.3f}s ({validation['error_percent']:+.2f}%)")
        print(f"    Max speed: {telemetry['velocity'].max():.1f} km/h")
        print(f"    Max G: {(telemetry['lateral_acc'] / 9.81).max():.2f}g")
        
        # Save telemetry
        filename = f"telemetry_{circuit_name.lower()}.csv"
        telemetry.to_csv(filename, index=False)
        print(f"    Telemetry saved: {filename}")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY - ACCURACY ACROSS CIRCUITS")
    print(f"{'='*70}")
    
    df_results = pd.DataFrame(results).T
    print("\n" + df_results.to_string())
    
    avg_error = abs(df_results['error_pct']).mean()
    print(f"\nAverage absolute error: {avg_error:.2f}%")
    
    if avg_error < 5:
        print("✓ Excellent accuracy!")
    elif avg_error < 10:
        print("✓ Good accuracy")
    else:
        print("⚠ Room for improvement")


if __name__ == "__main__":
    main()
