"""
F1 Vehicle Dynamics Lap Time Simulator
Author: [Your Name]
Date: December 2025

This simulator models F1 vehicle dynamics using:
- Pacejka tire model for lateral and longitudinal forces
- Aerodynamic downforce and drag
- Load transfer effects
- Point-mass vehicle model with 6-DOF potential

Physics Model:
- Longitudinal dynamics: F_x = m*a_x
- Lateral dynamics: F_y = m*v²/r (cornering)
- Aerodynamics: F_d = 0.5*ρ*C_d*A*v², F_l = 0.5*ρ*C_l*A*v²
- Tire forces: Pacejka Magic Formula
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.interpolate import interp1d
import pandas as pd

class F1Vehicle:
    """F1 Vehicle parameters based on 2024 regulations"""
    
    def __init__(self):
        # Mass properties
        self.mass = 798  # kg (minimum weight including driver)
        self.wheelbase = 3.6  # m
        self.track_width = 1.8  # m
        self.cg_height = 0.35  # m (center of gravity height)
        self.weight_dist_front = 0.45  # 45% front weight distribution
        
        # Aerodynamics
        self.Cd = 0.70  # Drag coefficient
        self.Cl_front = 1.8  # Front downforce coefficient
        self.Cl_rear = 1.7  # Rear downforce coefficient
        self.frontal_area = 1.5  # m²
        self.air_density = 1.225  # kg/m³
        
        # Powertrain
        self.max_power = 746_000  # W (1000 HP)
        self.max_rpm = 15_000
        self.gear_ratios = [2.8, 2.2, 1.8, 1.5, 1.3, 1.15, 1.0, 0.9]
        self.final_drive = 3.5
        
        # Tires (Pacejka parameters - simplified)
        self.tire_B = 10  # Stiffness factor
        self.tire_C = 1.9  # Shape factor
        self.tire_D = 1.0  # Peak factor
        self.tire_E = 0.97  # Curvature factor
        self.tire_mu_peak = 1.8  # Peak friction coefficient
        
        # Constants
        self.g = 9.81  # m/s²
        
    def calculate_tire_force(self, slip, normal_force):
        """
        Pacejka Magic Formula for tire force
        F = D * sin(C * atan(B*slip - E*(B*slip - atan(B*slip))))
        """
        B = self.tire_B
        C = self.tire_C
        D = self.tire_D * self.tire_mu_peak * normal_force
        E = self.tire_E
        
        force = D * np.sin(C * np.arctan(B * slip - E * (B * slip - np.arctan(B * slip))))
        return force
    
    def calculate_aero_forces(self, velocity, drs=False):
        """Calculate aerodynamic drag and downforce
        
        Args:
            velocity: Speed in m/s
            drs: Boolean indicating if DRS (Drag Reduction System) is active
        
        Returns:
            Tuple of (drag, downforce_total, downforce_front, downforce_rear)
        """
        v_squared = velocity ** 2
        
        # DRS reduces drag coefficient and rear downforce
        cd_active = self.Cd * 0.7 if drs else self.Cd
        cl_rear_active = self.Cl_rear * 0.5 if drs else self.Cl_rear
        
        drag = 0.5 * self.air_density * cd_active * self.frontal_area * v_squared
        downforce_front = 0.5 * self.air_density * self.Cl_front * self.frontal_area * v_squared
        downforce_rear = 0.5 * self.air_density * cl_rear_active * self.frontal_area * v_squared
        downforce_total = downforce_front + downforce_rear
        
        return drag, downforce_total, downforce_front, downforce_rear
    
    def calculate_max_acceleration(self, velocity, downforce_total):
        """Calculate maximum possible acceleration at given velocity"""
        # Normal forces on tires
        weight = self.mass * self.g
        normal_force_total = weight + downforce_total
        
        # Maximum tire force (simplified - assumes all tires contribute)
        max_tire_force = self.tire_mu_peak * normal_force_total
        
        # Engine force (power limited at high speed)
        if velocity > 5:
            engine_force = self.max_power / velocity
        else:
            engine_force = max_tire_force
        
        # Actual driving force is minimum of tire limit and engine force
        driving_force = min(engine_force, max_tire_force * 0.7)  # 70% for traction margin
        
        return driving_force
    
    def calculate_max_braking(self, velocity, downforce_total):
        """Calculate maximum braking force"""
        weight = self.mass * self.g
        normal_force_total = weight + downforce_total
        
        # Maximum braking force (assume 80% of grip for braking)
        max_brake_force = self.tire_mu_peak * normal_force_total * 0.8
        
        return max_brake_force
    
    def calculate_corner_speed(self, radius, downforce_total, mass=None):
        """Calculate maximum cornering speed for given radius
        
        Args:
            radius: Corner radius in meters
            downforce_total: Total downforce in N
            mass: Optional vehicle mass (defaults to self.mass)
        
        Returns:
            Maximum speed in m/s
        """
        if radius == np.inf:
            return np.inf
        
        if mass is None:
            mass = self.mass
            
        weight = mass * self.g
        normal_force = weight + downforce_total
        max_lateral_force = self.tire_mu_peak * normal_force
        
        # v = sqrt(a_y * r) where a_y = F_y / m
        max_lateral_accel = max_lateral_force / mass
        max_speed = np.sqrt(max_lateral_accel * abs(radius))
        
        return max_speed
    
    def get_current_mass(self, distance_km):
        """Get vehicle mass at a given track distance (accounts for fuel consumption)
        
        Args:
            distance_km: Distance traveled in kilometers
        
        Returns:
            Current vehicle mass in kg
        """
        # Simplified fuel consumption: ~1.5 kg/km
        fuel_consumed = distance_km * 1.5
        current_mass = max(798, self.mass - fuel_consumed)  # Minimum 798 kg
        return current_mass
    
    def can_use_drs(self, segment_type, speed_kmh):
        """Determine if DRS can be used at current location
        
        Args:
            segment_type: Type of track segment ('straight', 'fast_corner', etc.)
            speed_kmh: Current speed in km/h
        
        Returns:
            Boolean indicating if DRS is available
        """
        # DRS only on straights and at reasonable speed
        drs_eligible = segment_type in ['straight', 'fast_corner']
        speed_eligible = speed_kmh > 100  # Only above 100 km/h
        return drs_eligible and speed_eligible
    
    def get_axle_normal_loads(self, longitudinal_acc=0, lateral_acc=0):
        """Calculate normal loads on front and rear axles
        
        Args:
            longitudinal_acc: Longitudinal acceleration in m/s² (positive = forward)
            lateral_acc: Lateral acceleration in m/s²
        
        Returns:
            Tuple of (front_load, rear_load) in Newtons
        """
        weight = self.mass * self.g
        wheelbase = self.wheelbase
        cg_height = self.cg_height
        track_width = self.track_width
        
        # Weight distribution (45% front, 55% rear)
        weight_front = weight * self.weight_dist_front
        weight_rear = weight * (1 - self.weight_dist_front)
        
        # Longitudinal load transfer (due to acceleration/braking)
        # Positive accel pushes load backward (to rear)
        long_transfer = (longitudinal_acc * self.mass * cg_height) / wheelbase
        
        # Lateral load transfer (due to cornering)
        lat_transfer = (lateral_acc * self.mass * cg_height) / track_width
        
        # Total loads - transfer pushes weight to rear during acceleration
        front_load = weight_front - long_transfer
        rear_load = weight_rear + long_transfer
        
        # Ensure non-negative loads
        front_load = max(1, front_load)
        rear_load = max(1, rear_load)
        
        return front_load, rear_load
    
    def _tire_mu_vs_normal(self, normal_force):
        """Tire friction coefficient as function of normal load
        
        Args:
            normal_force: Normal force on a single tire in N
        
        Returns:
            Friction coefficient (mu)
        """
        # Simplified relationship: mu increases with load then plateaus
        base_mu = self.tire_mu_peak
        
        # Reduce mu at very low loads
        if normal_force < 2000:
            mu = base_mu * (normal_force / 2000) * 0.9
        # Slight increase with load
        elif normal_force < 5000:
            mu = base_mu
        # Diminishing effect at high loads
        else:
            mu = base_mu * (1 - 0.05 * np.log10(normal_force / 5000))
        
        return max(0.8, min(base_mu, mu))
    
    def calculate_combined_tire_force(self, slip_ratio, slip_angle, normal_force):
        """Calculate combined longitudinal and lateral tire force
        
        Args:
            slip_ratio: Longitudinal slip (0-1)
            slip_angle: Lateral slip angle in radians
            normal_force: Normal load in N
        
        Returns:
            Tuple of (longitudinal_force, lateral_force) in N
        """
        # Longitudinal force from slip
        fx = self.calculate_tire_force(slip_ratio, normal_force)
        
        # Lateral force from slip angle
        fy = self.calculate_tire_force(np.tan(slip_angle), normal_force)
        
        # Friction circle constraint
        mu = self._tire_mu_vs_normal(normal_force)
        max_force = mu * normal_force
        combined = np.sqrt(fx**2 + fy**2)
        
        if combined > max_force:
            scale = max_force / (combined + 1e-6)
            fx *= scale
            fy *= scale
        
        return fx, fy


class Track:
    """Track definition with segments"""
    
    def __init__(self, name="Generic Circuit"):
        self.name = name
        self.segments = []
        self.total_length = 0
        
    def add_segment(self, length, radius=np.inf, banking=0, elevation_change=0):
        """
        Add a track segment
        length: meters
        radius: meters (positive = right turn, negative = left turn, inf = straight)
        banking: degrees
        elevation_change: meters
        """
        start_distance = self.total_length
        self.segments.append({
            'start': start_distance,
            'end': start_distance + length,
            'length': length,
            'radius': radius,
            'banking': banking,
            'elevation': elevation_change
        })
        self.total_length += length
    
    def get_segment_at_distance(self, distance):
        """Get track segment properties at given distance"""
        for seg in self.segments:
            if seg['start'] <= distance < seg['end']:
                return seg
        return self.segments[-1]  # Return last segment if beyond track


def create_monza_style_track():
    """Create a Monza-inspired track layout"""
    track = Track("Monza-Style Circuit")
    
    # Sector 1
    track.add_segment(200, radius=np.inf)  # Start straight
    track.add_segment(120, radius=80)      # Turn 1 (Variante del Rettifilo)
    track.add_segment(80, radius=-70)      # Turn 2
    track.add_segment(300, radius=np.inf)  # Straight to Curva Grande
    track.add_segment(150, radius=200)     # Turn 3 (Curva Grande)
    
    # Sector 2
    track.add_segment(250, radius=np.inf)  # Straight
    track.add_segment(100, radius=45)      # Turn 4 (Variante della Roggia)
    track.add_segment(80, radius=-45)      # Turn 5
    track.add_segment(400, radius=np.inf)  # Long straight (Curva di Lesmo)
    track.add_segment(120, radius=60)      # Turn 6 (Lesmo 1)
    track.add_segment(100, radius=55)      # Turn 7 (Lesmo 2)
    
    # Sector 3
    track.add_segment(350, radius=np.inf)  # Straight to Ascari
    track.add_segment(90, radius=40)       # Turn 8 (Ascari)
    track.add_segment(80, radius=-42)      # Turn 9
    track.add_segment(70, radius=38)       # Turn 10
    track.add_segment(600, radius=np.inf)  # Main straight (Rettifilo Tribune)
    track.add_segment(100, radius=50)      # Parabolica
    track.add_segment(150, radius=np.inf)  # Finish straight
    
    return track


def simulate_lap(vehicle, track, dt=0.05):
    """
    Simulate a complete lap using point-mass model
    
    Returns:
    - telemetry: DataFrame with time, distance, speed, forces, etc.
    - lap_time: total lap time in seconds
    """
    
    # Initialize state
    time = 0
    distance = 0
    velocity = 0  # m/s
    
    # Storage for telemetry
    telemetry = {
        'time': [],
        'distance': [],
        'velocity': [],
        'acceleration': [],
        'downforce': [],
        'drag': [],
        'throttle': [],
        'brake': [],
        'lateral_g': [],
        'longitudinal_g': []
    }
    
    max_iterations = 100_000  # Safety limit
    iterations = 0
    
    while distance < track.total_length and iterations < max_iterations:
        iterations += 1
        
        # Get current track segment
        segment = track.get_segment_at_distance(distance)
        
        # Calculate aerodynamic forces
        drag, downforce_total, _, _ = vehicle.calculate_aero_forces(velocity)
        
        # Calculate corner speed limit
        corner_speed_limit = vehicle.calculate_corner_speed(segment['radius'], downforce_total)
        
        # Determine if we need to brake, coast, or accelerate
        if velocity > corner_speed_limit * 1.1:
            # Braking required
            max_brake = vehicle.calculate_max_braking(velocity, downforce_total)
            net_force = -(max_brake + drag)
            throttle = 0.0
            brake = 1.0
        elif velocity < corner_speed_limit * 0.95:
            # Can accelerate
            max_accel_force = vehicle.calculate_max_acceleration(velocity, downforce_total)
            net_force = max_accel_force - drag
            throttle = 1.0
            brake = 0.0
        else:
            # Coasting through corner
            net_force = -drag
            throttle = 0.0
            brake = 0.0
        
        # Calculate acceleration
        acceleration = net_force / vehicle.mass
        
        # Calculate lateral g-force in corner
        if segment['radius'] != np.inf:
            lateral_g = (velocity ** 2) / (abs(segment['radius']) * vehicle.g)
        else:
            lateral_g = 0
        
        # Update state
        velocity = max(0, velocity + acceleration * dt)
        distance += velocity * dt
        time += dt
        
        # Store telemetry (sample every 10 steps to reduce data)
        if iterations % 10 == 0:
            telemetry['time'].append(time)
            telemetry['distance'].append(distance)
            telemetry['velocity'].append(velocity * 3.6)  # Convert to km/h
            telemetry['acceleration'].append(acceleration / vehicle.g)
            telemetry['downforce'].append(downforce_total / 1000)  # kN
            telemetry['drag'].append(drag / 1000)  # kN
            telemetry['throttle'].append(throttle)
            telemetry['brake'].append(brake)
            telemetry['lateral_g'].append(lateral_g)
            telemetry['longitudinal_g'].append(acceleration / vehicle.g)
    
    # Convert to DataFrame
    df = pd.DataFrame(telemetry)
    
    return df, time


def plot_telemetry(telemetry, lap_time, track_name):
    """Create comprehensive telemetry plots"""
    
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))
    fig.suptitle(f'{track_name} - Lap Time: {lap_time:.3f}s', fontsize=16, fontweight='bold')
    
    # Speed trace
    axes[0].plot(telemetry['distance'], telemetry['velocity'], 'r-', linewidth=2)
    axes[0].set_ylabel('Speed (km/h)', fontsize=12)
    axes[0].set_title('Speed vs Distance', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim([0, telemetry['distance'].max()])
    
    # Throttle and Brake
    axes[1].fill_between(telemetry['distance'], 0, telemetry['throttle'], 
                         color='green', alpha=0.5, label='Throttle')
    axes[1].fill_between(telemetry['distance'], 0, -telemetry['brake'], 
                         color='red', alpha=0.5, label='Brake')
    axes[1].set_ylabel('Input', fontsize=12)
    axes[1].set_title('Throttle/Brake Application', fontsize=12, fontweight='bold')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim([0, telemetry['distance'].max()])
    axes[1].set_ylim([-1.1, 1.1])
    
    # G-Forces
    axes[2].plot(telemetry['distance'], telemetry['longitudinal_g'], 'b-', 
                linewidth=1.5, label='Longitudinal G')
    axes[2].plot(telemetry['distance'], telemetry['lateral_g'], 'orange', 
                linewidth=1.5, label='Lateral G')
    axes[2].set_ylabel('G-Force', fontsize=12)
    axes[2].set_title('G-Force Profile', fontsize=12, fontweight='bold')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    axes[2].set_xlim([0, telemetry['distance'].max()])
    
    # Downforce
    axes[3].plot(telemetry['distance'], telemetry['downforce'], 'purple', linewidth=2)
    axes[3].set_xlabel('Distance (m)', fontsize=12)
    axes[3].set_ylabel('Downforce (kN)', fontsize=12)
    axes[3].set_title('Aerodynamic Downforce', fontsize=12, fontweight='bold')
    axes[3].grid(True, alpha=0.3)
    axes[3].set_xlim([0, telemetry['distance'].max()])
    
    plt.tight_layout()
    plt.savefig('f1_lap_simulation.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved as 'f1_lap_simulation.png'")
    plt.show()


def main():
    """Main simulation runner"""
    
    print("="*60)
    print("F1 Vehicle Dynamics Lap Time Simulator")
    print("="*60)
    
    # Create vehicle and track
    vehicle = F1Vehicle()
    track = create_monza_style_track()
    
    print(f"\nTrack: {track.name}")
    print(f"Length: {track.total_length:.0f} meters")
    print(f"Number of segments: {len(track.segments)}")
    
    print("\nVehicle Configuration:")
    print(f"  Mass: {vehicle.mass} kg")
    print(f"  Power: {vehicle.max_power/745.7:.0f} HP")
    print(f"  Drag Coefficient: {vehicle.Cd}")
    print(f"  Downforce Coefficient (Total): {vehicle.Cl_front + vehicle.Cl_rear}")
    print(f"  Tire Peak μ: {vehicle.tire_mu_peak}")
    
    print("\nRunning simulation...")
    telemetry, lap_time = simulate_lap(vehicle, track)
    
    print(f"\n{'='*60}")
    print(f"PREDICTED LAP TIME: {lap_time:.3f} seconds")
    print(f"{'='*60}")
    
    # Calculate statistics
    max_speed = telemetry['velocity'].max()
    max_g_long = telemetry['longitudinal_g'].min()  # Most negative = hardest braking
    max_g_lat = telemetry['lateral_g'].max()
    avg_speed = telemetry['velocity'].mean()
    
    print(f"\nPerformance Statistics:")
    print(f"  Maximum Speed: {max_speed:.1f} km/h")
    print(f"  Average Speed: {avg_speed:.1f} km/h")
    print(f"  Max Braking G: {abs(max_g_long):.2f}g")
    print(f"  Max Lateral G: {max_g_lat:.2f}g")
    
    # Save telemetry
    telemetry.to_csv('f1_telemetry.csv', index=False)
    print(f"\nTelemetry saved to 'f1_telemetry.csv'")
    
    # Create plots
    plot_telemetry(telemetry, lap_time, track.name)
    
    print("\nSimulation complete!")


if __name__ == "__main__":
    main()