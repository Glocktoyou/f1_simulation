"""
F1 Vehicle Dynamics Simulator - Day 3 Advanced Version

NEW FEATURES:
1. Fuel mass effects (car gets lighter during lap)
2. DRS (Drag Reduction System) - reduces drag on straights
3. Setup optimization (find fastest configuration)
4. Lap comparison tool

This is getting close to professional simulator capability!
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import pandas as pd

class F1Vehicle:
    """F1 Vehicle with fuel mass and DRS"""
    
    def __init__(self, fuel_load=110):
        # Mass properties
        self.mass_empty = 798  # kg (minimum weight without fuel)
        self.fuel_load = fuel_load  # kg of fuel at start
        self.fuel_consumption_rate = 1.8  # kg per km
        
        # Aerodynamics
        self.Cd = 0.70  # Drag coefficient (DRS closed)
        self.Cd_drs = 0.55  # Drag coefficient with DRS open
        self.Cl_front = 1.8  # Front downforce
        self.Cl_rear = 1.7  # Rear downforce
        self.Cl_rear_drs = 1.4  # Rear downforce with DRS (less downforce)
        self.frontal_area = 1.5  # m²
        self.air_density = 1.225  # kg/m³
        
        # DRS rules
        self.drs_min_speed = 80  # km/h (minimum speed to activate DRS)
        self.drs_available_on_straights = True
        
        # Geometry
        self.wheelbase = 3.6
        self.track_width = 1.8
        self.cg_height = 0.35
        self.weight_dist_front = 0.45
        
        # Powertrain
        self.max_power = 746_000  # W
        
        # Tires
        self.tire_B = 10
        self.tire_C = 1.9
        self.tire_D = 1.0
        self.tire_E = 0.97
        self.tire_mu_peak = 1.8
        
        # Thermal (simplified for Day 3)
        self.tire_optimal_temp = 90
        self.tire_grip_at_temp = 1.0  # Assume optimal for now
        
        self.g = 9.81
    
    def get_current_mass(self, distance_covered):
        """Calculate current mass based on fuel burned"""
        fuel_burned = (distance_covered / 1000) * self.fuel_consumption_rate
        fuel_remaining = max(0, self.fuel_load - fuel_burned)
        current_mass = self.mass_empty + fuel_remaining
        return current_mass
    
    def can_use_drs(self, segment_radius, velocity_kmh):
        """Determine if DRS can be used"""
        is_straight = (segment_radius == np.inf)
        is_fast_enough = (velocity_kmh >= self.drs_min_speed)
        return is_straight and is_fast_enough and self.drs_available_on_straights
    
    def calculate_aero_forces(self, velocity, drs_active=False):
        """Calculate aero with DRS option"""
        v_squared = velocity ** 2
        
        if drs_active:
            drag = 0.5 * self.air_density * self.Cd_drs * self.frontal_area * v_squared
            downforce_rear = 0.5 * self.air_density * self.Cl_rear_drs * self.frontal_area * v_squared
        else:
            drag = 0.5 * self.air_density * self.Cd * self.frontal_area * v_squared
            downforce_rear = 0.5 * self.air_density * self.Cl_rear * self.frontal_area * v_squared
        
        downforce_front = 0.5 * self.air_density * self.Cl_front * self.frontal_area * v_squared
        downforce_total = downforce_front + downforce_rear
        
        return drag, downforce_total, downforce_front, downforce_rear
    
    def calculate_load_transfer(self, acceleration, downforce_front, downforce_rear, current_mass):
        """Load transfer with current mass"""
        weight_front_static = current_mass * self.g * self.weight_dist_front
        weight_rear_static = current_mass * self.g * (1 - self.weight_dist_front)
        
        load_transfer = (current_mass * acceleration * self.cg_height) / self.wheelbase
        
        weight_front = weight_front_static - load_transfer + downforce_front
        weight_rear = weight_rear_static + load_transfer + downforce_rear
        
        return max(0, weight_front), max(0, weight_rear)
    
    def calculate_max_acceleration(self, velocity, weight_rear, current_mass):
        """Max acceleration with current mass"""
        if velocity > 5:
            engine_force = self.max_power / velocity
        else:
            engine_force = 10000
        
        max_tire_force = self.tire_mu_peak * weight_rear
        driving_force = min(engine_force, max_tire_force)
        
        return driving_force
    
    def calculate_max_braking(self, weight_front, weight_rear):
        """Max braking force"""
        max_brake_front = self.tire_mu_peak * weight_front * 0.9
        max_brake_rear = self.tire_mu_peak * weight_rear * 0.6
        return max_brake_front + max_brake_rear
    
    def calculate_corner_speed(self, radius, weight_total, current_mass):
        """Corner speed limit"""
        if radius == np.inf:
            return np.inf
        
        max_lateral_force = self.tire_mu_peak * weight_total
        max_lateral_accel = max_lateral_force / current_mass
        max_speed = np.sqrt(max_lateral_accel * abs(radius))
        
        return max_speed


class Track:
    """Track definition"""
    
    def __init__(self, name="Generic Circuit"):
        self.name = name
        self.segments = []
        self.total_length = 0
        
    def add_segment(self, length, radius=np.inf, banking=0):
        start_distance = self.total_length
        self.segments.append({
            'start': start_distance,
            'end': start_distance + length,
            'length': length,
            'radius': radius,
            'banking': banking
        })
        self.total_length += length
    
    def get_segment_at_distance(self, distance):
        for seg in self.segments:
            if seg['start'] <= distance < seg['end']:
                return seg
        return self.segments[-1]


def create_monza_style_track():
    """Monza circuit"""
    track = Track("Monza-Style Circuit")
    
    track.add_segment(200, radius=np.inf)
    track.add_segment(120, radius=80)
    track.add_segment(80, radius=-70)
    track.add_segment(300, radius=np.inf)
    track.add_segment(150, radius=200)
    track.add_segment(250, radius=np.inf)
    track.add_segment(100, radius=45)
    track.add_segment(80, radius=-45)
    track.add_segment(400, radius=np.inf)
    track.add_segment(120, radius=60)
    track.add_segment(100, radius=55)
    track.add_segment(350, radius=np.inf)
    track.add_segment(90, radius=40)
    track.add_segment(80, radius=-42)
    track.add_segment(70, radius=38)
    track.add_segment(600, radius=np.inf)
    track.add_segment(100, radius=50)
    track.add_segment(150, radius=np.inf)
    
    return track


def simulate_lap(vehicle, track, dt=0.05):
    """
    Main simulation with fuel mass and DRS
    """
    
    time = 0
    distance = 0
    velocity = 0
    
    telemetry = {
        'time': [], 'distance': [], 'velocity': [], 'acceleration': [],
        'downforce': [], 'drag': [], 'throttle': [], 'brake': [],
        'lateral_g': [], 'longitudinal_g': [],
        'fuel_mass': [], 'current_mass': [], 'drs_active': []
    }
    
    max_iterations = 100_000
    iterations = 0
    
    while distance < track.total_length and iterations < max_iterations:
        iterations += 1
        
        segment = track.get_segment_at_distance(distance)
        current_mass = vehicle.get_current_mass(distance)
        
        # Check if DRS can be used
        drs_active = vehicle.can_use_drs(segment['radius'], velocity * 3.6)
        
        # Calculate aero forces
        drag, downforce_total, downforce_front, downforce_rear = vehicle.calculate_aero_forces(
            velocity, drs_active)
        
        # Initial load transfer estimate
        temp_accel = 0
        weight_front, weight_rear = vehicle.calculate_load_transfer(
            temp_accel, downforce_front, downforce_rear, current_mass)
        weight_total = weight_front + weight_rear
        
        # Corner speed limit
        corner_speed_limit = vehicle.calculate_corner_speed(segment['radius'], weight_total, current_mass)
        
        # Control logic
        if velocity > corner_speed_limit * 1.1:
            # Braking
            max_brake = vehicle.calculate_max_braking(weight_front, weight_rear)
            net_force = -(max_brake + drag)
            throttle = 0.0
            brake = 1.0
        elif velocity < corner_speed_limit * 0.95:
            # Accelerating
            max_accel_force = vehicle.calculate_max_acceleration(velocity, weight_rear, current_mass)
            net_force = max_accel_force - drag
            throttle = 1.0
            brake = 0.0
        else:
            # Coasting
            net_force = -drag
            throttle = 0.0
            brake = 0.0
        
        # Calculate acceleration
        acceleration = net_force / current_mass
        
        # Recalculate load transfer
        weight_front, weight_rear = vehicle.calculate_load_transfer(
            acceleration, downforce_front, downforce_rear, current_mass)
        
        # Lateral g
        if segment['radius'] != np.inf:
            lateral_g = (velocity ** 2) / (abs(segment['radius']) * vehicle.g)
        else:
            lateral_g = 0
        
        # Update state
        velocity = max(0, velocity + acceleration * dt)
        distance += velocity * dt
        time += dt
        
        # Store telemetry
        if iterations % 10 == 0:
            fuel_remaining = vehicle.fuel_load - (distance / 1000) * vehicle.fuel_consumption_rate
            telemetry['time'].append(time)
            telemetry['distance'].append(distance)
            telemetry['velocity'].append(velocity * 3.6)
            telemetry['acceleration'].append(acceleration / vehicle.g)
            telemetry['downforce'].append(downforce_total / 1000)
            telemetry['drag'].append(drag / 1000)
            telemetry['throttle'].append(throttle)
            telemetry['brake'].append(brake)
            telemetry['lateral_g'].append(lateral_g)
            telemetry['longitudinal_g'].append(acceleration / vehicle.g)
            telemetry['fuel_mass'].append(max(0, fuel_remaining))
            telemetry['current_mass'].append(current_mass)
            telemetry['drs_active'].append(1.0 if drs_active else 0.0)
    
    df = pd.DataFrame(telemetry)
    return df, time


def plot_day3_telemetry(telemetry, lap_time, track_name):
    """Day 3 plotting with fuel and DRS"""
    
    fig, axes = plt.subplots(5, 1, figsize=(14, 14))
    fig.suptitle(f'{track_name} - Lap Time: {lap_time:.3f}s (WITH FUEL & DRS)', 
                 fontsize=16, fontweight='bold')
    
    # Speed with DRS zones highlighted
    axes[0].plot(telemetry['distance'], telemetry['velocity'], 'r-', linewidth=2)
    
    # Highlight DRS zones
    drs_zones = telemetry[telemetry['drs_active'] > 0.5]
    if not drs_zones.empty:
        axes[0].scatter(drs_zones['distance'], drs_zones['velocity'], 
                       color='lime', s=1, alpha=0.5, label='DRS Active')
    
    axes[0].set_ylabel('Speed (km/h)', fontsize=12)
    axes[0].set_title('Speed vs Distance (Green = DRS Active)', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Throttle/Brake
    axes[1].fill_between(telemetry['distance'], 0, telemetry['throttle'], 
                         color='green', alpha=0.5, label='Throttle')
    axes[1].fill_between(telemetry['distance'], 0, -telemetry['brake'], 
                         color='red', alpha=0.5, label='Brake')
    axes[1].set_ylabel('Input', fontsize=12)
    axes[1].set_title('Throttle/Brake Application', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # G-Forces
    axes[2].plot(telemetry['distance'], telemetry['longitudinal_g'], 'b-', 
                linewidth=1.5, label='Longitudinal G')
    axes[2].plot(telemetry['distance'], telemetry['lateral_g'], 'orange', 
                linewidth=1.5, label='Lateral G')
    axes[2].set_ylabel('G-Force', fontsize=12)
    axes[2].set_title('G-Force Profile', fontsize=12, fontweight='bold')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    
    # Fuel Mass
    axes[3].plot(telemetry['distance'], telemetry['fuel_mass'], 'orange', linewidth=2)
    axes[3].set_ylabel('Fuel (kg)', fontsize=12)
    axes[3].set_title('Fuel Mass (Car Getting Lighter)', fontsize=12, fontweight='bold')
    axes[3].grid(True, alpha=0.3)
    
    # Total Mass
    axes[4].plot(telemetry['distance'], telemetry['current_mass'], 'purple', linewidth=2)
    axes[4].set_xlabel('Distance (m)', fontsize=12)
    axes[4].set_ylabel('Total Mass (kg)', fontsize=12)
    axes[4].set_title('Vehicle Mass Over Lap', fontsize=12, fontweight='bold')
    axes[4].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('f1_lap_simulation_day3.png', dpi=300, bbox_inches='tight')
    print(f"Day 3 plot saved as 'f1_lap_simulation_day3.png'")
    plt.show()


def optimize_setup(track, initial_params):
    """
    BONUS: Setup optimization using scipy
    Find the best downforce/drag balance for fastest lap
    """
    
    print("\n" + "="*60)
    print("SETUP OPTIMIZATION - Finding Fastest Configuration")
    print("="*60)
    
    def objective_function(params):
        """
        params = [Cd, Cl_front, Cl_rear]
        Returns lap time (we want to minimize this)
        """
        Cd, Cl_front, Cl_rear = params
        
        # Create vehicle with these parameters
        vehicle = F1Vehicle()
        vehicle.Cd = Cd
        vehicle.Cl_front = Cl_front
        vehicle.Cl_rear = Cl_rear
        
        # Run simulation
        _, lap_time = simulate_lap(vehicle, track)
        
        return lap_time
    
    # Initial guess [Cd, Cl_front, Cl_rear]
    x0 = initial_params
    
    # Bounds for parameters (realistic F1 ranges)
    bounds = [
        (0.50, 0.90),  # Cd: drag coefficient
        (1.2, 2.5),    # Cl_front: front downforce
        (1.2, 2.5)     # Cl_rear: rear downforce
    ]
    
    print("\nStarting optimization...")
    print(f"Initial setup: Cd={x0[0]:.2f}, Cl_front={x0[1]:.2f}, Cl_rear={x0[2]:.2f}")
    
    # Run optimization
    result = minimize(objective_function, x0, method='Nelder-Mead', 
                     bounds=bounds, options={'maxiter': 30, 'disp': True})
    
    optimal_Cd, optimal_Cl_front, optimal_Cl_rear = result.x
    optimal_laptime = result.fun
    
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE!")
    print("="*60)
    print(f"Optimal Setup:")
    print(f"  Cd (Drag):           {optimal_Cd:.3f}")
    print(f"  Cl_front (Downforce): {optimal_Cl_front:.3f}")
    print(f"  Cl_rear (Downforce):  {optimal_Cl_rear:.3f}")
    print(f"\nOptimal Lap Time: {optimal_laptime:.3f} seconds")
    
    return result


def compare_configurations(track):
    """Compare different setups side-by-side"""
    
    print("\n" + "="*60)
    print("CONFIGURATION COMPARISON")
    print("="*60)
    
    configs = {
        'Low Downforce (Monza)': {'Cd': 0.65, 'Cl_front': 1.5, 'Cl_rear': 1.4},
        'Medium Downforce (Balanced)': {'Cd': 0.70, 'Cl_front': 1.8, 'Cl_rear': 1.7},
        'High Downforce (Monaco)': {'Cd': 0.80, 'Cl_front': 2.3, 'Cl_rear': 2.2},
    }
    
    results = {}
    
    for name, setup in configs.items():
        vehicle = F1Vehicle()
        vehicle.Cd = setup['Cd']
        vehicle.Cl_front = setup['Cl_front']
        vehicle.Cl_rear = setup['Cl_rear']
        
        _, lap_time = simulate_lap(vehicle, track)
        max_speed = 330  # Placeholder
        
        results[name] = lap_time
        print(f"\n{name}:")
        print(f"  Cd={setup['Cd']:.2f}, Cl_f={setup['Cl_front']:.2f}, Cl_r={setup['Cl_rear']:.2f}")
        print(f"  Lap Time: {lap_time:.3f}s")
    
    # Find best
    best_config = min(results, key=results.get)
    print(f"\n{'='*60}")
    print(f"BEST CONFIGURATION: {best_config}")
    print(f"Lap Time: {results[best_config]:.3f}s")
    
    return results


def main():
    """Day 3 main simulation"""
    
    print("="*60)
    print("F1 SIMULATOR - DAY 3 ADVANCED VERSION")
    print("Features: Fuel Mass, DRS, Setup Optimization")
    print("="*60)
    
    track = create_monza_style_track()
    
    # Baseline simulation
    print("\n1. BASELINE SIMULATION (Full fuel, DRS enabled)")
    vehicle = F1Vehicle(fuel_load=110)
    telemetry, lap_time = simulate_lap(vehicle, track)
    
    print(f"\n{'='*60}")
    print(f"BASELINE LAP TIME: {lap_time:.3f} seconds")
    print(f"{'='*60}")
    
    # Stats
    max_speed = telemetry['velocity'].max()
    fuel_burned = telemetry['fuel_mass'].iloc[0] - telemetry['fuel_mass'].iloc[-1]
    mass_start = telemetry['current_mass'].iloc[0]
    mass_end = telemetry['current_mass'].iloc[-1]
    drs_usage = (telemetry['drs_active'].sum() / len(telemetry)) * 100
    
    print(f"\nPerformance:")
    print(f"  Max Speed: {max_speed:.1f} km/h")
    print(f"  Fuel Burned: {fuel_burned:.2f} kg")
    print(f"  Mass (Start): {mass_start:.1f} kg")
    print(f"  Mass (End): {mass_end:.1f} kg")
    print(f"  DRS Usage: {drs_usage:.1f}% of lap")
    
    telemetry.to_csv('f1_telemetry_day3.csv', index=False)
    plot_day3_telemetry(telemetry, lap_time, track.name)
    
    # Configuration comparison
    compare_configurations(track)
    
    print("\n" + "="*60)
    print("Day 3 simulation complete!")
    print("="*60)


if __name__ == "__main__":
    main()