
"""
Example 1: Basic Lap Simulation

This example shows how to:
1. Create a vehicle and track
2. Run a lap simulation
3. Analyze telemetry data
"""

# Ensure src is in sys.path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from f1_simulation import F1Vehicle, create_monza_style_track, simulate_lap, plot_telemetry


def main():
    print("="*70)
    print("F1 VEHICLE DYNAMICS SIMULATOR - EXAMPLE 1: BASIC LAP")
    print("="*70)
    
    # Step 1: Create vehicle
    print("\nCreating F1 vehicle...")
    vehicle = F1Vehicle()
    print(f"  Vehicle mass: {vehicle.mass} kg")
    print(f"  Max power: {vehicle.max_power/1000:.0f} kW ({vehicle.max_power/745.7:.0f} HP)")
    print(f"  Tire peak μ: {vehicle.tire_mu_peak}")
    
    # Step 2: Create track
    print("\nCreating Monza-style track...")
    track = create_monza_style_track()
    print(f"  Track name: {track.name}")
    print(f"  Track length: {track.total_length:.0f} m")
    print(f"  Number of segments: {len(track.segments)}")
    
    # Step 3: Run simulation
    print("\nRunning lap simulation...")
    telemetry, lap_time = simulate_lap(vehicle, track, dt=0.05)
    
    # Step 4: Analyze results
    print(f"\n{'='*70}")
    print(f"LAP TIME: {lap_time:.3f} seconds")
    print(f"{'='*70}")
    
    print("\nPerformance Metrics:")
    print(f"  Max speed:         {telemetry['velocity'].max():.1f} km/h")
    print(f"  Avg speed:         {telemetry['velocity'].mean():.1f} km/h")
    print(f"  Max acceleration:  {telemetry['acceleration'].max():.2f}g")
    print(f"  Max braking:       {abs(telemetry['acceleration'].min()):.2f}g")
    print(f"  Max lateral G:     {telemetry['lateral_g'].max():.2f}g")
    
    # Step 5: Generate visualizations
    print("\nGenerating telemetry plots...")
    plot_telemetry(telemetry, lap_time, track.name)
    
    print("\nDone! Check 'f1_lap_simulation.png' for visualization.")


if __name__ == "__main__":
    main()
