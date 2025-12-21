"""
F1 Vehicle Dynamics Simulator - ENHANCED VERSION (Day 2)
Added: Tire temperature, Load transfer, Brake temperature

New features:
- Tire temperature affects grip
- Load transfer in braking/acceleration  
- Brake temperature and fade
- More realistic vehicle behavior
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.interpolate import interp1d
import pandas as pd

class F1Vehicle:
    """F1 Vehicle with enhanced thermal and load transfer models"""
    
    def __init__(self):
        # Mass properties
        self.mass = 798  # kg (minimum weight including driver)
        self.wheelbase = 3.6  # m
        self.track_width = 1.8  # m
        self.cg_height = 0.35  # m (center of gravity height)
        self.weight_dist_front = 0.45  # 45% static front weight distribution
        
        # Aerodynamics
        self.Cd = 0.70  # Drag coefficient
        self.Cl_front = 1.8  # Front downforce coefficient
        self.Cl_rear = 1.7  # Rear downforce coefficient
        self.frontal_area = 1.5  # m²
        self.air_density = 1.225  # kg/m³
        
        # Powertrain
        self.max_power = 746_000  # W (1000 HP)
        self.max_rpm = 15_000
        
        # Tires (Pacejka parameters)
        self.tire_B = 10
        self.tire_C = 1.9
        self.tire_D = 1.0
        self.tire_E = 0.97
        self.tire_mu_peak = 1.8  # Peak friction at optimal temp
        
        # NEW: Tire thermal model
        self.tire_optimal_temp = 90  # °C (optimal operating temperature)
        self.tire_initial_temp = 40  # °C (cold tires at start)
        self.tire_max_temp = 130  # °C (danger zone)
        self.tire_heating_rate = 2.5  # °C per second of hard use
        self.tire_cooling_rate = 0.5  # °C per second
        
        # NEW: Brake thermal model
        self.brake_initial_temp = 200  # °C
        self.brake_optimal_temp = 400  # °C
        self.brake_max_temp = 800  # °C
        self.brake_heating_rate = 50  # °C per second of braking
        self.brake_cooling_rate = 8  # °C per second
        
        # Constants
        self.g = 9.81  # m/s²
        
    def get_tire_grip_multiplier(self, tire_temp):
        """
        Tire grip varies with temperature
        Peak grip at optimal temp, reduced when cold or hot
        """
        temp_diff = abs(tire_temp - self.tire_optimal_temp)
        
        if tire_temp < self.tire_optimal_temp:
            # Cold tires: linear degradation
            grip_multiplier = 0.70 + 0.30 * (tire_temp / self.tire_optimal_temp)
        else:
            # Hot tires: exponential degradation
            overheat = (tire_temp - self.tire_optimal_temp) / (self.tire_max_temp - self.tire_optimal_temp)
            grip_multiplier = 1.0 - 0.25 * overheat
        
        return max(0.65, min(1.0, grip_multiplier))  # Clamp between 65% and 100%
    
    def get_brake_efficiency(self, brake_temp):
        """
        Brake efficiency varies with temperature
        Too cold = not enough bite, too hot = fade
        """
        if brake_temp < self.brake_optimal_temp:
            # Cold brakes
            efficiency = 0.75 + 0.25 * (brake_temp / self.brake_optimal_temp)
        else:
            # Hot brakes - fade
            fade = (brake_temp - self.brake_optimal_temp) / (self.brake_max_temp - self.brake_optimal_temp)
            efficiency = 1.0 - 0.30 * fade
        
        return max(0.70, min(1.0, efficiency))
    
    def calculate_load_transfer(self, acceleration, downforce_front, downforce_rear):
        """
        Calculate weight distribution during acceleration/braking
        Weight shifts forward under braking, rearward under acceleration
        """
        # Static weight distribution
        weight_front_static = self.mass * self.g * self.weight_dist_front
        weight_rear_static = self.mass * self.g * (1 - self.weight_dist_front)
        
        # Load transfer due to longitudinal acceleration
        # ΔW = (m * a * h) / L
        load_transfer = (self.mass * acceleration * self.cg_height) / self.wheelbase
        
        # Add aerodynamic loads
        weight_front = weight_front_static - load_transfer + downforce_front
        weight_rear = weight_rear_static + load_transfer + downforce_rear
        
        return max(0, weight_front), max(0, weight_rear)
    
    def calculate_tire_force(self, slip, normal_force, tire_temp):
        """
        Enhanced Pacejka model with temperature effects
        """
        # Get grip multiplier based on temperature
        grip_mult = self.get_tire_grip_multiplier(tire_temp)
        
        B = self.tire_B
        C = self.tire_C
        D = self.tire_D * self.tire_mu_peak * grip_mult * normal_force
        E = self.tire_E
        
        force = D * np.sin(C * np.arctan(B * slip - E * (B * slip - np.arctan(B * slip))))
        return force
    
    def calculate_aero_forces(self, velocity):
        """Calculate aerodynamic drag and downforce"""
        v_squared = velocity ** 2
        
        drag = 0.5 * self.air_density * self.Cd * self.frontal_area * v_squared
        downforce_front = 0.5 * self.air_density * self.Cl_front * self.frontal_area * v_squared
        downforce_rear = 0.5 * self.air_density * self.Cl_rear * self.frontal_area * v_squared
        downforce_total = downforce_front + downforce_rear
        
        return drag, downforce_total, downforce_front, downforce_rear
    
    def calculate_max_acceleration(self, velocity, weight_rear, tire_temp):
        """Calculate maximum possible acceleration considering load transfer"""
        # Engine force (power limited)
        if velocity > 5:
            engine_force = self.max_power / velocity
        else:
            engine_force = 10000  # High torque at low speed
        
        # Tire limit on rear axle (RWD F1 car)
        grip_mult = self.get_tire_grip_multiplier(tire_temp)
        max_tire_force = self.tire_mu_peak * grip_mult * weight_rear
        
        # Actual force is minimum
        driving_force = min(engine_force, max_tire_force)
        
        return driving_force
    
    def calculate_max_braking(self, weight_front, weight_rear, brake_temp, tire_temp_front, tire_temp_rear):
        """Calculate maximum braking force with temperature effects"""
        # Brake efficiency
        brake_eff = self.get_brake_efficiency(brake_temp)
        
        # Tire grip on both axles
        grip_mult_front = self.get_tire_grip_multiplier(tire_temp_front)
        grip_mult_rear = self.get_tire_grip_multiplier(tire_temp_rear)
        
        max_brake_front = self.tire_mu_peak * grip_mult_front * weight_front * brake_eff
        max_brake_rear = self.tire_mu_peak * grip_mult_rear * weight_rear * brake_eff * 0.7  # Less rear braking
        
        return max_brake_front + max_brake_rear
    
    def calculate_corner_speed(self, radius, weight_total, tire_temp):
        """Calculate maximum cornering speed"""
        if radius == np.inf:
            return np.inf
        
        grip_mult = self.get_tire_grip_multiplier(tire_temp)
        max_lateral_force = self.tire_mu_peak * grip_mult * weight_total
        max_lateral_accel = max_lateral_force / self.mass
        max_speed = np.sqrt(max_lateral_accel * abs(radius))
        
        return max_speed


class Track:
    """Track definition"""
    
    def __init__(self, name="Generic Circuit"):
        self.name = name
        self.segments = []
        self.total_length = 0
        
    def add_segment(self, length, radius=np.inf, banking=0, elevation_change=0):
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
        for seg in self.segments:
            if seg['start'] <= distance < seg['end']:
                return seg
        return self.segments[-1]


def create_monza_style_track():
    """Monza-style circuit"""
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


def simulate_lap_enhanced(vehicle, track, dt=0.05):
    """
    Enhanced simulation with thermal models
    """
    
    # Initialize state
    time = 0
    distance = 0
    velocity = 0
    
    # Thermal states
    tire_temp_front = 110
    tire_temp_rear = 110
    brake_temp = vehicle.brake_initial_temp
    
    # Storage
    telemetry = {
        'time': [], 'distance': [], 'velocity': [], 'acceleration': [],
        'downforce': [], 'drag': [], 'throttle': [], 'brake': [],
        'lateral_g': [], 'longitudinal_g': [],
        'tire_temp_front': [], 'tire_temp_rear': [], 'brake_temp': [],
        'tire_grip_mult': [], 'brake_efficiency': []
    }
    
    max_iterations = 100_000
    iterations = 0
    
    while distance < track.total_length and iterations < max_iterations:
        iterations += 1
        
        segment = track.get_segment_at_distance(distance)
        drag, downforce_total, downforce_front, downforce_rear = vehicle.calculate_aero_forces(velocity)
        
        # Assume zero acceleration initially for load transfer calculation
        temp_accel = 0
        weight_front, weight_rear = vehicle.calculate_load_transfer(temp_accel, downforce_front, downforce_rear)
        weight_total = weight_front + weight_rear
        
        # Calculate corner speed limit with current tire temp
        corner_speed_limit = vehicle.calculate_corner_speed(segment['radius'], weight_total, tire_temp_front)
        
        # Determine control inputs
        if velocity > corner_speed_limit * 1.1:
            # Braking
            max_brake = vehicle.calculate_max_braking(weight_front, weight_rear, brake_temp, 
                                                       tire_temp_front, tire_temp_rear)
            net_force = -(max_brake + drag)
            throttle = 0.0
            brake = 1.0
            
            # Heat brakes and tires
            brake_temp += vehicle.brake_heating_rate * dt
            tire_temp_front = vehicle.tire_initial_temp * dt * 0.8
            tire_temp_rear = vehicle.tire_initial_temp * dt * 0.5
            
        elif velocity < corner_speed_limit * 0.95:
            # Accelerating
            max_accel_force = vehicle.calculate_max_acceleration(velocity, weight_rear, tire_temp_rear)
            net_force = max_accel_force - drag
            throttle = 1.0
            brake = 0.0
            
            # Heat rear tires from wheelspin/power
            tire_temp_rear += vehicle.tire_heating_rate * dt * 0.6
            tire_temp_front += vehicle.tire_heating_rate * dt * 0.2
            
            # Cool brakes
            brake_temp -= vehicle.brake_cooling_rate * dt
            
        else:
            # Coasting
            net_force = -drag
            throttle = 0.0
            brake = 0.0
            
            # Cool everything
            tire_temp_front -= vehicle.tire_cooling_rate * dt
            tire_temp_rear -= vehicle.tire_cooling_rate * dt
            brake_temp -= vehicle.brake_cooling_rate * dt
        
        # Clamp temperatures
        tire_temp_front = np.clip(tire_temp_front, 30, vehicle.tire_max_temp)
        tire_temp_rear = np.clip(tire_temp_rear, 30, vehicle.tire_max_temp)
        brake_temp = np.clip(brake_temp, 150, vehicle.brake_max_temp)
        
        # Calculate acceleration
        acceleration = net_force / vehicle.mass
        
        # Recalculate load transfer with actual acceleration
        weight_front, weight_rear = vehicle.calculate_load_transfer(acceleration, downforce_front, downforce_rear)
        
        # Lateral g-force
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
            telemetry['tire_temp_front'].append(tire_temp_front)
            telemetry['tire_temp_rear'].append(tire_temp_rear)
            telemetry['brake_temp'].append(brake_temp)
            telemetry['tire_grip_mult'].append(vehicle.get_tire_grip_multiplier(tire_temp_front))
            telemetry['brake_efficiency'].append(vehicle.get_brake_efficiency(brake_temp))
    
    df = pd.DataFrame(telemetry)
    return df, time


def plot_enhanced_telemetry(telemetry, lap_time, track_name):
    """Enhanced plotting with thermal data"""
    
    fig, axes = plt.subplots(5, 1, figsize=(14, 14))
    fig.suptitle(f'{track_name} - Lap Time: {lap_time:.3f}s (WITH THERMAL EFFECTS)', 
                 fontsize=16, fontweight='bold')
    
    # Speed
    axes[0].plot(telemetry['distance'], telemetry['velocity'], 'r-', linewidth=2)
    axes[0].set_ylabel('Speed (km/h)', fontsize=12)
    axes[0].set_title('Speed vs Distance', fontsize=12, fontweight='bold')
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
    
    # NEW: Tire Temperature
    axes[3].plot(telemetry['distance'], telemetry['tire_temp_front'], 'b-', 
                linewidth=2, label='Front Tires')
    axes[3].plot(telemetry['distance'], telemetry['tire_temp_rear'], 'r-', 
                linewidth=2, label='Rear Tires')
    axes[3].axhline(y=90, color='green', linestyle='--', linewidth=1, label='Optimal (90°C)')
    axes[3].set_ylabel('Temperature (°C)', fontsize=12)
    axes[3].set_title('Tire Temperature', fontsize=12, fontweight='bold')
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)
    
    # NEW: Brake Temperature & Grip
    ax4b = axes[4].twinx()
    axes[4].plot(telemetry['distance'], telemetry['brake_temp'], 'red', 
                linewidth=2, label='Brake Temp')
    ax4b.plot(telemetry['distance'], telemetry['tire_grip_mult'], 'blue', 
             linewidth=2, label='Tire Grip %')
    axes[4].set_xlabel('Distance (m)', fontsize=12)
    axes[4].set_ylabel('Brake Temp (°C)', fontsize=12, color='red')
    ax4b.set_ylabel('Tire Grip Multiplier', fontsize=12, color='blue')
    axes[4].set_title('Brake Temperature & Tire Grip', fontsize=12, fontweight='bold')
    axes[4].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('f1_lap_simulation_enhanced.png', dpi=300, bbox_inches='tight')
    print(f"Enhanced plot saved as 'f1_lap_simulation_enhanced.png'")
    plt.show()


def main():
    """Main simulation"""
    
    print("="*60)
    print("F1 ENHANCED Simulator - Day 2 Version")
    print("With Tire Temperature, Load Transfer, Brake Fade")
    print("="*60)
    
    vehicle = F1Vehicle()
    track = create_monza_style_track()
    
    print(f"\nTrack: {track.name}")
    print(f"Length: {track.total_length:.0f} meters")
    
    print("\nThermal Model:")
    print(f"  Tire Optimal Temp: {vehicle.tire_optimal_temp}°C")
    print(f"  Tire Starting Temp: {vehicle.tire_initial_temp}°C (COLD START)")
    print(f"  Brake Optimal Temp: {vehicle.brake_optimal_temp}°C")
    
    print("\nRunning enhanced simulation...")
    telemetry, lap_time = simulate_lap_enhanced(vehicle, track)
    
    print(f"\n{'='*60}")
    print(f"LAP TIME (with thermal effects): {lap_time:.3f} seconds")
    print(f"{'='*60}")
    
    # Statistics
    max_speed = telemetry['velocity'].max()
    final_tire_temp_front = telemetry['tire_temp_front'].iloc[-1]
    final_tire_temp_rear = telemetry['tire_temp_rear'].iloc[-1]
    max_brake_temp = telemetry['brake_temp'].max()
    min_grip = telemetry['tire_grip_mult'].min()
    
    print(f"\nPerformance:")
    print(f"  Maximum Speed: {max_speed:.1f} km/h")
    print(f"  Final Tire Temp (Front): {final_tire_temp_front:.1f}°C")
    print(f"  Final Tire Temp (Rear): {final_tire_temp_rear:.1f}°C")
    print(f"  Max Brake Temp: {max_brake_temp:.1f}°C")
    print(f"  Minimum Grip Factor: {min_grip:.2%}")
    
    telemetry.to_csv('f1_telemetry_enhanced.csv', index=False)
    print(f"\nEnhanced telemetry saved to 'f1_telemetry_enhanced.csv'")
    
    plot_enhanced_telemetry(telemetry, lap_time, track.name)
    
    print("\nSimulation complete!")


if __name__ == "__main__":
    main()