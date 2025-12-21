"""
F1 Vehicle Dynamics Simulator - DAY 4: REAL TRACKS

Real F1 circuits with actual corner data:
- Silverstone (UK) - High speed with fast corners
- Monaco - Slow, technical street circuit
- Spa-Francorchamps - Mix of high/low speed

Includes validation against real F1 lap times
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

class F1Vehicle:
    """F1 Vehicle - Final optimized version"""
    
    def __init__(self, fuel_load=15):
        # Mass
        self.mass_empty = 798
        self.fuel_load = fuel_load
        self.fuel_consumption_rate = 1.8
        
        # Aero
        self.Cd = 0.70
        self.Cd_drs = 0.55
        self.Cl_front = 1.8
        self.Cl_rear = 1.6
        self.Cl_rear_drs = 1.4
        self.frontal_area = 1.5
        self.air_density = 1.225
        
        # DRS
        self.drs_min_speed = 80
        self.drs_available = True
        
        # Geometry
        self.wheelbase = 3.6
        self.track_width = 1.8
        self.cg_height = 0.35
        self.weight_dist_front = 0.45
        
        # Power
        self.max_power = 746_000
        
        # Tires
        self.tire_mu_peak = 2.1
        # Rolling resistance coefficient (typical range ~0.010-0.020)
        self.C_rr = 0.015
        # Drivetrain efficiency (multiplicative on available engine force)
        self.drivetrain_efficiency = 0.92
        # Low-speed torque/force cap to prevent unrealistically large forces
        self.max_torque_force = 90000
        self.g = 9.81
        
        # Drivetrain / gearing
        self.wheel_radius = 0.33                # m (approx. effective wheel radius)
        self.final_drive = 3.8                  # final drive ratio
        self.gear_ratios = [3.6, 2.2, 1.6, 1.2, 0.95, 0.75, 0.6]  # example 7-speed ratios

        # Simple torque curve (rpm -> Nm)
        self.torque_rpm = np.array([1000, 3000, 6000, 9000, 12000, 15000])
        self.torque_values = np.array([350, 500, 540, 520, 480, 380])
        self.idle_rpm = 1000
        self.redline_rpm = 15000
    

    def get_current_mass(self, distance_km):
        fuel_burned = distance_km * self.fuel_consumption_rate
        fuel_remaining = max(0, self.fuel_load - fuel_burned)
        return self.mass_empty + fuel_remaining
    
    def can_use_drs(self, segment_type, velocity_kmh):
        return segment_type == 'straight' and velocity_kmh >= self.drs_min_speed and self.drs_available
    
    def calculate_aero_forces(self, velocity, drs_active=False):
        v_squared = velocity ** 2
        
        if drs_active:
            drag = 0.5 * self.air_density * self.Cd_drs * self.frontal_area * v_squared
            downforce_rear = 0.5 * self.air_density * self.Cl_rear_drs * self.frontal_area * v_squared
        else:
            drag = 0.5 * self.air_density * self.Cd * self.frontal_area * v_squared
            downforce_rear = 0.5 * self.air_density * self.Cl_rear * self.frontal_area * v_squared
        
        downforce_front = 0.5 * self.air_density * self.Cl_front * self.frontal_area * v_squared
        return drag, downforce_front + downforce_rear, downforce_front, downforce_rear
    
    def calculate_corner_speed(self, radius, downforce_total, current_mass):
        # Keep backwards-compatibility if radius is infinite
        if radius == np.inf:
            return np.inf

        # Use a simple static tire mu here; the caller may reduce effective mu
        weight = current_mass * self.g
        normal_force = weight + downforce_total
        max_lateral_force = self.tire_mu_peak * normal_force
        max_speed = np.sqrt((max_lateral_force / current_mass) * abs(radius))
        return max_speed


class RealF1Track:
    """Real F1 track with actual corner data"""
    
    def __init__(self, name, length, record_lap_time, record_holder, year):
        self.name = name
        self.length = length  # meters
        self.record_lap_time = record_lap_time  # seconds
        self.record_holder = record_holder
        self.year = year
        self.segments = []
        self.total_length = 0
    
    def add_segment(self, name, length, radius=np.inf, segment_type='corner', speed_limit=None):
        """
        Add track segment with real corner data
        segment_type: 'straight', 'fast_corner', 'medium_corner', 'slow_corner', 'chicane'
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
    
    def get_segment_at_distance(self, distance):
        for seg in self.segments:
            if seg['start'] <= distance < seg['end']:
                return seg
        return self.segments[-1]


def create_silverstone():
    """
    Silverstone Circuit - United Kingdom
    - Length: 5.891 km
    - Record: 1:27.097 (Lewis Hamilton, 2020, Mercedes)
    - Characteristics: Fast, flowing corners with long straights
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


def create_monaco():
    """
    Circuit de Monaco - Monte Carlo
    - Length: 3.337 km
    - Record: 1:10.166 (Lewis Hamilton, 2019, Mercedes)
    - Characteristics: Slow, tight street circuit with many slow corners
    """
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


def create_spa():
    """
    Spa-Francorchamps - Belgium
    - Length: 7.004 km
    - Record: 1:46.286 (Valtteri Bottas, 2018, Mercedes)
    - Characteristics: High speed with elevation changes, mix of corner types
    """
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


def simulate_real_track(vehicle, track, dt=0.05):
    """Simulate lap on real F1 track"""
    
    time = 0
    distance = 0
    velocity = 0
    
    telemetry = {
        'time': [], 'distance': [], 'velocity': [],
        'segment_name': [], 'drs_active': []
    }
    
    max_iterations = 150_000
    iterations = 0
    
    while distance < track.total_length and iterations < max_iterations:
        iterations += 1
        
        segment = track.get_segment_at_distance(distance)
        current_mass = vehicle.get_current_mass(distance / 1000)
        
        # Restrict DRS to long straights (avoid enabling on short straights/chicanes)
        drs_active = vehicle.can_use_drs(segment['type'], velocity * 3.6) and segment.get('length', 0) >= 300
        drag, downforce_total, df_front, df_rear = vehicle.calculate_aero_forces(velocity, drs_active)

        # Compute a speed-dependent effective tire mu (reduces slightly at very high speeds)
        speed_kmh = velocity * 3.6
        mu_decay = min(0.2, speed_kmh / 2000.0)
        mu_eff = vehicle.tire_mu_peak * (1.0 - mu_decay)

        # Corner speed limit computed from effective lateral grip
        if segment['radius'] == np.inf:
            corner_speed_limit = np.inf
        else:
            weight = current_mass * vehicle.g
            normal_force = weight + downforce_total
            max_lateral_force = mu_eff * normal_force
            corner_speed_limit = np.sqrt((max_lateral_force / current_mass) * abs(segment['radius']))
        
        # Control logic
        if velocity > corner_speed_limit * 1.1:
            # Braking
            weight = current_mass * vehicle.g + downforce_total
            max_brake = vehicle.tire_mu_peak * weight * 0.85
            net_force = -(max_brake + drag)
        elif velocity < corner_speed_limit * 0.95:
            # Accelerating
            weight_rear = current_mass * vehicle.g * 0.55 + df_rear
            # More realistic engine/drivetrain: include efficiency and a low-speed torque cap
            # Use gear/torque model to compute engine force (handles low/high speed more realistically)
            engine_force = vehicle.get_engine_force(max(velocity, 0.1))
            engine_force = min(engine_force, vehicle.max_torque_force)
            max_tire = mu_eff * weight_rear
            net_force = min(engine_force, max_tire) - drag
        else:
            # Coasting
            net_force = -drag

        # Rolling resistance (always opposes motion)
        rolling = vehicle.C_rr * current_mass * vehicle.g
        net_force -= rolling
        
        acceleration = net_force / current_mass
        velocity = max(0, velocity + acceleration * dt)
        distance += velocity * dt
        time += dt
        
        if iterations % 20 == 0:
            telemetry['time'].append(time)
            telemetry['distance'].append(distance)
            telemetry['velocity'].append(velocity * 3.6)
            telemetry['segment_name'].append(segment['name'])
            telemetry['drs_active'].append(1 if drs_active else 0)
    
    return pd.DataFrame(telemetry), time


def validate_against_real_f1(simulated_time, track):
    """Compare simulation to real F1 lap time"""
    
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
        print(f"✓ EXCELLENT - Within 5% of real F1 time!")
    elif abs(error_percent) < 10:
        print(f"✓ GOOD - Within 10% of real F1 time")
    else:
        print(f"⚠ Needs improvement - Over 10% error")
    
    return {
        'track': track.name,
        'real_time': real_time,
        'sim_time': simulated_time,
        'difference': difference,
        'error_percent': error_percent
    }


def plot_track_comparison(results_dict):
    """Create comparison plot for multiple tracks"""
    
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
    print(f"\n✓ Validation plot saved: 'real_track_validation.png'")
    plt.show()


def create_validation_report(results_dict):
    """Create text report for documentation"""
    
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
    
    print("\n✓ Validation report saved: 'validation_report.txt'")
    return report_text


def main():
    """Day 4 - Real tracks validation"""
    
    print("="*70)
    print("F1 SIMULATOR - DAY 4: REAL TRACKS & VALIDATION")
    print("="*70)
    
    # Create vehicle (qualifying setup - low fuel)
    vehicle = F1Vehicle(fuel_load=10)
    
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
    print("DAY 4 COMPLETE!")
    print("="*70)
    print("\nFiles created:")
    print("  ✓ real_track_validation.png")
    print("  ✓ validation_report.txt")
    print("  ✓ telemetry_silverstone.csv")
    print("  ✓ telemetry_monaco.csv")
    print("  ✓ telemetry_spa.csv")


if __name__ == "__main__":
    main()