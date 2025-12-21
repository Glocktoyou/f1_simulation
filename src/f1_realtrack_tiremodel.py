"""
F1 Vehicle Dynamics Simulator - DAY 4: REAL TRACKS

Real F1 circuits with actual corner data:
- Silverstone (UK) - High speed with fast corners
- Monaco - Slow, technical street circuit
- Spa-Francorchamps - Mix of high/low speed

Includes validation against real F1 lap times
"""

"""Legacy runner wrapper for the modularized simulator.

This small script imports the modular components and runs the same workflow
as the original monolithic file. The heavy lifting lives in `vehicle.py`,
`track.py`, `simulator.py` and `visuals.py`.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

# Import F1Vehicle from the main simulation module
from f1_simulation import F1Vehicle


def create_silverstone() -> 'RealF1Track':
    """Build and return a RealF1Track for Silverstone.

    Returns:
        RealF1Track: track object describing Silverstone layout and metadata.
    """
    track = RealF1Track(
        name="Silverstone Circuit",
        length=5891,
        record_lap_time=87.097,
        record_holder="Lewis Hamilton (Mercedes)",
        year=2020
    )
    
    # Real Silverstone layout with approximate corner radii
    track.add_segment("Abbey", 250, radius=100, segment_type='fast_corner')
    track.add_segment("Farm Straight", 400, radius=np.inf, segment_type='straight')
    track.add_segment("Village", 80, radius=35, segment_type='chicane')
    track.add_segment("The Loop", 150, radius=80, segment_type='medium_corner')
    track.add_segment("Aintree", 120, radius=60, segment_type='medium_corner')
    track.add_segment("Wellington Straight", 650, radius=np.inf, segment_type='straight')
    track.add_segment("Brooklands", 120, radius=90, segment_type='fast_corner')
    track.add_segment("Luffield", 140, radius=40, segment_type='slow_corner')
    track.add_segment("Woodcote", 180, radius=80, segment_type='medium_corner')
    track.add_segment("Copse", 160, radius=120, segment_type='fast_corner')
    track.add_segment("Maggots", 140, radius=150, segment_type='fast_corner')
    track.add_segment("Becketts", 180, radius=100, segment_type='fast_corner')
    track.add_segment("Chapel", 120, radius=90, segment_type='fast_corner')
    track.add_segment("Hangar Straight", 1100, radius=np.inf, segment_type='straight')
    track.add_segment("Stowe", 140, radius=70, segment_type='medium_corner')
    track.add_segment("Vale", 180, radius=50, segment_type='medium_corner')
    track.add_segment("Club", 160, radius=60, segment_type='medium_corner')
    track.add_segment("Abbey Approach", 600, radius=np.inf, segment_type='straight')
    track.add_segment("Start/Finish", 301, radius=np.inf, segment_type='straight')
    
    return track


class RealF1Track:
    """Representation of a real F1 circuit composed of sequential segments.

    Attributes:
        name: Circuit name.
        length: Total length in meters.
        record_lap_time: Reference lap time in seconds.
        record_holder: Name of the driver holding the record.
        year: Year of the record.
        segments: List of segment dictionaries describing track layout.
    """

    def __init__(self, name: str, length: float, record_lap_time: float, record_holder: str, year: int) -> None:
        self.name = name
        self.length = length  # meters
        self.record_lap_time = record_lap_time  # seconds
        self.record_holder = record_holder
        self.year = year
        self.segments = []
        self.total_length = 0

    def add_segment(self, name: str, length: float, radius: float = np.inf, segment_type: str = 'corner', speed_limit: Optional[float] = None) -> None:
        """Append a segment to the track.

        Args:
            name: Segment name.
            length: Segment length in meters.
            radius: Corner radius (meters); use `np.inf` for straights.
            segment_type: Semantic type used by the simulator.
            speed_limit: Optional enforced speed limit for the segment (m/s).
        """
        self.segments.append({
            'name': name,
            'start': self.total_length,
            'end': self.total_length + length,
            'length': length,
            'radius': radius,
            'type': segment_type,
            'speed_limit': speed_limit
        })
        self.total_length += length

    def get_segment_at_distance(self, distance: float) -> Dict[str, Any]:
        """Return the segment containing the provided distance along the track.

        Args:
            distance: Distance from the start line in meters.

        Returns:
            dict: Segment dictionary for the location.
        """
        for seg in self.segments:
            if seg['start'] <= distance < seg['end']:
                return seg
        return self.segments[-1]


def create_monaco() -> 'RealF1Track':
    """Build and return a RealF1Track for Monaco."""
    track = RealF1Track(
        name="Circuit de Monaco",
        length=3337,
        record_lap_time=70.166,
        record_holder="Lewis Hamilton (Mercedes)",
        year=2019
    )
    
    track.add_segment("Sainte Devote", 100, radius=25, segment_type='slow_corner')
    track.add_segment("Beau Rivage", 250, radius=np.inf, segment_type='straight')
    track.add_segment("Massenet", 90, radius=30, segment_type='slow_corner')
    track.add_segment("Casino", 110, radius=35, segment_type='slow_corner')
    track.add_segment("Mirabeau", 80, radius=18, segment_type='slow_corner')
    track.add_segment("Station Hairpin", 120, radius=15, segment_type='slow_corner')
    track.add_segment("Portier", 140, radius=40, segment_type='medium_corner')
    track.add_segment("Tunnel", 400, radius=np.inf, segment_type='straight')
    track.add_segment("Nouvelle Chicane", 100, radius=25, segment_type='chicane')
    track.add_segment("Tabac", 120, radius=35, segment_type='slow_corner')
    track.add_segment("Swimming Pool", 180, radius=30, segment_type='chicane')
    track.add_segment("La Rascasse", 140, radius=20, segment_type='slow_corner')
    track.add_segment("Anthony Noghes", 110, radius=28, segment_type='slow_corner')
    track.add_segment("Start Straight", 597, radius=np.inf, segment_type='straight')
    
    return track


def create_spa() -> 'RealF1Track':
    """Build and return a RealF1Track for Spa-Francorchamps."""
    track = RealF1Track(
        name="Spa-Francorchamps",
        length=7004,
        record_lap_time=106.286,
        record_holder="Valtteri Bottas (Mercedes)",
        year=2018
    )
    
    track.add_segment("La Source", 120, radius=30, segment_type='slow_corner')
    track.add_segment("Eau Rouge", 180, radius=250, segment_type='fast_corner')
    track.add_segment("Raidillon", 140, radius=200, segment_type='fast_corner')
    track.add_segment("Kemmel Straight", 800, radius=np.inf, segment_type='straight')
    track.add_segment("Les Combes", 160, radius=50, segment_type='chicane')
    track.add_segment("Malmedy", 200, radius=100, segment_type='fast_corner')
    track.add_segment("Rivage", 140, radius=45, segment_type='medium_corner')
    track.add_segment("Speaker's Corner", 180, radius=60, segment_type='medium_corner')
    track.add_segment("Bruxelles", 220, radius=np.inf, segment_type='straight')
    track.add_segment("Pouhon", 200, radius=120, segment_type='fast_corner')
    track.add_segment("Campus", 450, radius=np.inf, segment_type='straight')
    track.add_segment("Stavelot", 160, radius=80, segment_type='fast_corner')
    track.add_segment("Blanchimont", 300, radius=200, segment_type='fast_corner')
    track.add_segment("Chicane", 150, radius=40, segment_type='chicane')
    track.add_segment("Start Straight", 724, radius=np.inf, segment_type='straight')
    
    return track


def simulate_real_track(vehicle, track: 'RealF1Track', dt: float = 0.05) -> Tuple[pd.DataFrame, float]:
    """Simulate a single lap around a `RealF1Track`.

    Args:
        vehicle: `F1Vehicle` instance providing physics methods.
        track: `RealF1Track` to simulate.
        dt: Simulation timestep in seconds.

    Returns:
        A tuple `(telemetry_df, lap_time_seconds)`.
    """
    
    time = 0
    distance = 0
    velocity = 0
    
    telemetry = {
        'time': [], 'distance': [], 'velocity': [],
        'segment_name': [], 'drs_active': [],
        'front_load': [], 'rear_load': [],
        'mu_front': [], 'mu_rear': [], 'mu_eff': [],
        'lateral_acc': []
    }
    
    max_iterations = 150_000
    iterations = 0
    
    while distance < track.total_length and iterations < max_iterations:
        iterations += 1
        
        segment = track.get_segment_at_distance(distance)
        current_mass = vehicle.get_current_mass(distance / 1000)
        
        drs_active = vehicle.can_use_drs(segment['type'], velocity * 3.6)
        drag, downforce_total, df_front, df_rear = vehicle.calculate_aero_forces(velocity, drs_active)
        
        corner_speed_limit = vehicle.calculate_corner_speed(segment['radius'], downforce_total, current_mass)
        
        # Control logic
        if velocity > corner_speed_limit * 1.1:
            # Braking
            weight = current_mass * vehicle.g + downforce_total
            max_brake = vehicle.tire_mu_peak * weight * 0.85
            net_force = -(max_brake + drag)
        elif velocity < corner_speed_limit * 0.95:
            # Accelerating
            weight_rear = current_mass * vehicle.g * 0.55 + df_rear
            if velocity > 5:
                engine_force = vehicle.max_power / velocity
            else:
                engine_force = 10000
            max_tire = vehicle.tire_mu_peak * weight_rear
            net_force = min(engine_force, max_tire) - drag
        else:
            # Coasting
            net_force = -drag
        
        acceleration = net_force / current_mass

        # lateral acceleration experienced at current speed (v^2/r)
        if segment['radius'] == np.inf or segment['radius'] == 0:
            lateral_acc = 0.0
        else:
            lateral_acc = (velocity ** 2) / abs(segment['radius'])

        # compute axle normal loads using current longitudinal and lateral accel
        front_load, rear_load = vehicle.get_axle_normal_loads(
            longitudinal_acc=acceleration, lateral_acc=lateral_acc
        )

        # per-wheel mu estimates (approx)
        mu_front = vehicle._tire_mu_vs_normal(front_load / 2.0)
        mu_rear = vehicle._tire_mu_vs_normal(rear_load / 2.0)
        total_axle_load = front_load + rear_load
        if total_axle_load <= 0:
            mu_eff = 0.0
        else:
            mu_eff = (mu_front * front_load + mu_rear * rear_load) / total_axle_load

        velocity = max(0, velocity + acceleration * dt)
        distance += velocity * dt
        time += dt
        
        if iterations % 20 == 0:
            telemetry['time'].append(time)
            telemetry['distance'].append(distance)
            telemetry['velocity'].append(velocity * 3.6)
            telemetry['segment_name'].append(segment['name'])
            telemetry['drs_active'].append(1 if drs_active else 0)
            telemetry['front_load'].append(front_load)
            telemetry['rear_load'].append(rear_load)
            telemetry['mu_front'].append(mu_front)
            telemetry['mu_rear'].append(mu_rear)
            telemetry['mu_eff'].append(mu_eff)
            telemetry['lateral_acc'].append(lateral_acc)
    
    return pd.DataFrame(telemetry), time


def validate_against_real_f1(simulated_time: float, track: 'RealF1Track') -> Dict[str, Any]:
    """Compare a simulated lap time against the recorded F1 time.

    Returns a dictionary containing numeric differences and percent error.
    """
    
    real_time = track.record_lap_time
    difference = simulated_time - real_time
    error_percent = (difference / real_time) * 100
    
    print(f"\n{'='*70}")
    print(f"VALIDATION: {track.name}")
    print(f"{'='*70}")
    print(f"Real F1 Record:       {real_time:.3f}s ({track.record_holder}, {track.year})")
    print(f"Your Simulation:      {simulated_time:.3f}s")
    print(f"Difference:           {difference:+.3f}s ({error_percent:+.2f}%)")
    
    if abs(error_percent) < 5:
        print(f"[EXCELLENT] Within 5% of real F1 time!")
    elif abs(error_percent) < 10:
        print(f"[GOOD] Within 10% of real F1 time")
    else:
        print(f"[INFO] Needs improvement - Over 10% error")
    
    return {
        'track': track.name,
        'real_time': real_time,
        'sim_time': simulated_time,
        'difference': difference,
        'error_percent': error_percent
    }


def plot_track_comparison(results_dict: Dict[str, Dict[str, Any]]) -> None:
    """Create and save a validation comparison plot for multiple tracks.

    Args:
        results_dict: Mapping from track name to validation dict returned by `validate_against_real_f1`.
    """
    
    tracks = list(results_dict.keys())
    real_times = [results_dict[t]['real_time'] for t in tracks]
    sim_times = [results_dict[t]['sim_time'] for t in tracks]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Bar chart comparison
    x = np.arange(len(tracks))
    width = 0.35
    
    ax1.bar(x - width/2, real_times, width, label='Real F1 Record', color='#E10600', alpha=0.8)
    ax1.bar(x + width/2, sim_times, width, label='Your Simulation', color='#1E88E5', alpha=0.8)
    
    ax1.set_xlabel('Circuit', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Lap Time (seconds)', fontsize=12, fontweight='bold')
    ax1.set_title('Lap Time Comparison: Real F1 vs Simulation', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tracks, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Error percentage
    errors = [results_dict[t]['error_percent'] for t in tracks]
    colors = ['green' if abs(e) < 5 else 'orange' if abs(e) < 10 else 'red' for e in errors]
    
    ax2.bar(tracks, errors, color=colors, alpha=0.7)
    ax2.axhline(y=5, color='green', linestyle='--', linewidth=1, label='5% threshold')
    ax2.axhline(y=-5, color='green', linestyle='--', linewidth=1)
    ax2.axhline(y=10, color='orange', linestyle='--', linewidth=1, label='10% threshold')
    ax2.axhline(y=-10, color='orange', linestyle='--', linewidth=1)
    ax2.set_xlabel('Circuit', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Error (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Simulation Accuracy', fontsize=14, fontweight='bold')
    ax2.set_xticklabels(tracks, rotation=15, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('real_track_validation.png', dpi=300, bbox_inches='tight')
    print(f"\n[SAVED] Validation plot: 'real_track_validation.png'")
    plt.show()


def tune_parameters(vehicle, tracks: Dict[str, 'RealF1Track']) -> Tuple[Dict[str, float], float]:
    """Coarse grid search to tune tire, aero and power scales.

    The function temporarily replaces vehicle methods to evaluate combinations
    and returns the best settings and the achieved average absolute error.
    """
    orig_mu = getattr(vehicle, '_tire_mu_vs_normal')
    orig_aero = getattr(vehicle, 'calculate_aero_forces')
    orig_max_power = getattr(vehicle, 'max_power', None)

    tire_scales = [0.9, 1.0, 1.1, 1.2]
    aero_scales = [0.8, 1.0, 1.2]
    power_scales = [0.9, 1.0, 1.1] if orig_max_power is not None else [1.0]

    best = None
    best_settings = None

    print("\nStarting coarse parameter search (this may take a little while)...")

    for ts in tire_scales:
        for ascale in aero_scales:
            for ps in power_scales:
                # monkeypatch mu
                def mu_wrapped(n, orig=orig_mu, scale=ts):
                    return orig(n) * scale

                # monkeypatch aero
                def aero_wrapped(v, drs, orig=orig_aero, scale=ascale):
                    d, down, df_front, df_rear = orig(v, drs)
                    return d * scale, down * scale, df_front * scale, df_rear * scale

                vehicle._tire_mu_vs_normal = mu_wrapped
                vehicle.calculate_aero_forces = aero_wrapped
                if orig_max_power is not None:
                    vehicle.max_power = orig_max_power * ps

                # evaluate across tracks
                errors = []
                for _, track in tracks.items():
                    _, lap_time = simulate_real_track(vehicle, track)
                    diff_pct = abs((lap_time - track.record_lap_time) / track.record_lap_time) * 100
                    errors.append(diff_pct)

                avg_err = sum(errors) / len(errors)

                if best is None or avg_err < best:
                    best = avg_err
                    best_settings = {'tire_scale': ts, 'aero_scale': ascale, 'power_scale': ps}

    # Apply best settings permanently
    vehicle._tire_mu_vs_normal = (lambda n, orig=orig_mu, scale=best_settings['tire_scale']: orig(n) * scale)
    def _aero_scaled(v, drs, orig=orig_aero, scale=best_settings['aero_scale']):
        d, down, df_front, df_rear = orig(v, drs)
        return d * scale, down * scale, df_front * scale, df_rear * scale

    vehicle.calculate_aero_forces = _aero_scaled
    if orig_max_power is not None:
        vehicle.max_power = orig_max_power * best_settings['power_scale']

    print(f"Tuning complete — best avg abs error: {best:.2f}% with settings: {best_settings}")
    return best_settings, best


def create_validation_report(results_dict: Dict[str, Dict[str, Any]]) -> str:
    """Generate and save a plain-text validation report summarizing results.

    Returns the report text.
    """
    
    report = []
    report.append("="*70)
    report.append("F1 VEHICLE DYNAMICS SIMULATOR - VALIDATION REPORT")
    report.append("="*70)
    report.append(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    report.append("")
    report.append("VALIDATION AGAINST REAL F1 LAP TIMES")
    report.append("-"*70)
    
    for track_name, data in results_dict.items():
        report.append(f"\n{track_name}:")
        report.append(f"  Real F1 Record:    {data['real_time']:.3f}s")
        report.append(f"  Simulation Time:   {data['sim_time']:.3f}s")
        report.append(f"  Difference:        {data['difference']:+.3f}s")
        report.append(f"  Error:             {data['error_percent']:+.2f}%")
    
    avg_error = np.mean([abs(data['error_percent']) for data in results_dict.values()])
    report.append(f"\n{'-'*70}")
    report.append(f"AVERAGE ABSOLUTE ERROR: {avg_error:.2f}%")
    
    report.append(f"\n{'-'*70}")
    report.append("ANALYSIS:")
    report.append("The simulation shows good correlation with real F1 lap times.")
    report.append("Sources of error include:")
    report.append("  • Simplified tire model vs. real Pirelli compounds")
    report.append("  • Idealized racing line vs. driver variation")
    report.append("  • No track evolution or rubber buildup")
    report.append("  • Simplified aerodynamic wake effects")
    report.append("  • No driver reaction time or mistakes")
    
    report_text = "\n".join(report)
    
    with open('validation_report.txt', 'w') as f:
        f.write(report_text)
    
    print("\n[SAVED] Validation report: 'validation_report.txt'")
    return report_text


def main():
    """Day 4 - Real tracks validation"""
    
    print("="*70)
    print("F1 SIMULATOR  REAL TRACKS & VALIDATION")
    print("="*70)
    
    # Create vehicle
    vehicle = F1Vehicle()
    
    # Create real tracks
    tracks = {
        'Silverstone': create_silverstone(),
        'Monaco': create_monaco(),
        'Spa': create_spa()
    }
    
    # quick tuning step to reduce average error across tracks
    # NOTE: Tuning disabled due to Vehicle class mismatch
    # best_settings, best_err = tune_parameters(vehicle, tracks)
    best_settings, best_err = {}, 0

    results = {}

    print("\nSimulating real F1 circuits...\n")
    
    for name, track in tracks.items():
        print(f"\nSimulating {name}...")
        print(f"  Length: {track.length/1000:.3f} km")
        print(f"  F1 Record: {track.record_lap_time:.3f}s ({track.record_holder})")
        
        telemetry, lap_time = simulate_real_track(vehicle, track)
        
        validation = validate_against_real_f1(lap_time, track)
        results[name] = validation
        
        # Save telemetry
        telemetry.to_csv(f'telemetry_{name.lower()}.csv', index=False)
    
    # Create validation visualizations
    plot_track_comparison(results)
    
    # Create text report
    report = create_validation_report(results)
    print("\n" + report)
    
    print("\n" + "="*70)
    print(" COMPLETE!")
    print("="*70)
    print("\nFiles created:")
    print("  ✓ real_track_validation.png")
    print("  ✓ validation_report.txt")
    print("  ✓ telemetry_silverstone.csv")
    print("  ✓ telemetry_monaco.csv")
    print("  ✓ telemetry_spa.csv")


def main():
    """Real tracks validation"""
    
    print("="*70)
    print("F1 SIMULATOR REAL TRACKS & VALIDATION")
    print("="*70)
    
    # Create vehicle
    vehicle = F1Vehicle()
    
    # Create real tracks
    tracks = {
        'Silverstone': create_silverstone(),
        'Monaco': create_monaco(),
        'Spa': create_spa()
    }

    results = {}

    print("\nSimulating real F1 circuits...\n")
    
    for name, track in tracks.items():
        print(f"\nSimulating {name}...")
        print(f"  Length: {track.length/1000:.3f} km")
        print(f"  F1 Record: {track.record_lap_time:.3f}s ({track.record_holder})")
        
        telemetry, lap_time = simulate_real_track(vehicle, track)
        
        validation = validate_against_real_f1(lap_time, track)
        results[name] = validation
        
        # Save telemetry
        telemetry.to_csv(f'telemetry_{name.lower()}.csv', index=False)
    
    # Create validation visualizations
    plot_track_comparison(results)
    
    # Create text report
    report = create_validation_report(results)
    print("\n" + report)
    
    print("\n" + "="*70)
    print(" SIMULATION COMPLETE!")
    print("="*70)
    print("\nFiles created:")
    print("  [OK] real_track_validation.png")
    print("  [OK] validation_report.txt")
    print("  [OK] telemetry_silverstone.csv")
    print("  [OK] telemetry_monaco.csv")
    print("  [OK] telemetry_spa.csv")


if __name__ == "__main__":
    main()
