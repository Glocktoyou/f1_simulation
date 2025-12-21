# API Reference

Complete API documentation for the F1 Vehicle Dynamics Simulator.

## Table of Contents

1. [F1Vehicle Class](#f1vehicle-class)
2. [Track Class](#track-class)
3. [Simulation Functions](#simulation-functions)
4. [Real Track Functions](#real-track-functions)
5. [Data Structures](#data-structures)

---

## F1Vehicle Class

Main vehicle class containing all physics calculations.

### Constructor

```python
vehicle = F1Vehicle()
```

Creates an F1 vehicle with 2024 regulation parameters.

### Attributes

#### Mass & Dimensions
```python
vehicle.mass                    # int: 798 kg (2024 minimum)
vehicle.wheelbase              # float: 3.6 m
vehicle.track_width            # float: 1.8 m
vehicle.cg_height              # float: 0.35 m (center of gravity)
vehicle.weight_dist_front      # float: 0.45 (45% front distribution)
```

#### Aerodynamics
```python
vehicle.Cd                      # float: 0.70 (drag coefficient)
vehicle.Cl_front                # float: 1.8 (front downforce coeff)
vehicle.Cl_rear                 # float: 1.7 (rear downforce coeff)
vehicle.frontal_area            # float: 1.5 m²
vehicle.air_density             # float: 1.225 kg/m³ (sea level)
```

#### Powertrain
```python
vehicle.max_power               # int: 746000 W (1000 HP)
vehicle.max_rpm                 # int: 15000
vehicle.gear_ratios             # list: [2.8, 2.2, 1.8, 1.5, 1.3, 1.15, 1.0, 0.9]
vehicle.final_drive             # float: 3.5
```

#### Tires
```python
vehicle.tire_B                  # float: 10 (stiffness factor)
vehicle.tire_C                  # float: 1.9 (shape factor)
vehicle.tire_D                  # float: 1.0 (peak factor)
vehicle.tire_E                  # float: 0.97 (curvature factor)
vehicle.tire_mu_peak            # float: 1.8 (peak friction coefficient)
```

#### Constants
```python
vehicle.g                       # float: 9.81 m/s² (gravity)
```

### Methods

#### calculate_aero_forces()

Calculate aerodynamic drag and downforce at given velocity.

```python
drag, downforce_total, downforce_front, downforce_rear = vehicle.calculate_aero_forces(
    velocity: float,
    drs: bool = False
) -> Tuple[float, float, float, float]
```

**Parameters:**
- `velocity` (float): Vehicle velocity in m/s
- `drs` (bool, optional): DRS active flag (default: False)

**Returns:**
- `drag` (float): Drag force in Newtons
- `downforce_total` (float): Total downforce in Newtons
- `downforce_front` (float): Front axle downforce in Newtons
- `downforce_rear` (float): Rear axle downforce in Newtons

**Example:**
```python
drag, df_total, df_front, df_rear = vehicle.calculate_aero_forces(50.0)
# drag ≈ 1200 N at 50 m/s

drag_drs, _, _, _ = vehicle.calculate_aero_forces(50.0, drs=True)
# drag ≈ 840 N (30% reduction)
```

**Physics:**
```
F_drag = 0.5 * ρ * C_d * A * v²
C_d_drs = 0.7 * C_d when DRS active
```

---

#### calculate_tire_force()

Calculate tire force using Pacejka Magic Formula.

```python
force = vehicle.calculate_tire_force(
    slip: float,
    normal_force: float
) -> float
```

**Parameters:**
- `slip` (float): Slip ratio (0 to 1) or slip angle (radians)
- `normal_force` (float): Normal load on tire in Newtons

**Returns:**
- `force` (float): Tire force in Newtons

**Example:**
```python
# At 20% longitudinal slip with 4000 N load
force = vehicle.calculate_tire_force(0.2, 4000)  # ≈ 6200 N

# At -5° slip angle with 4000 N load
force = vehicle.calculate_tire_force(-0.087, 4000)  # ≈ 6800 N
```

**Notes:**
- Maximum force: `vehicle.tire_mu_peak * normal_force`
- Force increases non-linearly with slip
- Peak occurs around 5-15% slip ratio

---

#### calculate_corner_speed()

Calculate maximum cornering speed for a given radius.

```python
max_speed = vehicle.calculate_corner_speed(
    radius: float,
    downforce_total: float,
    mass: float = None
) -> float
```

**Parameters:**
- `radius` (float): Corner radius in meters (inf for straights)
- `downforce_total` (float): Total downforce in Newtons
- `mass` (float, optional): Vehicle mass in kg (default: self.mass)

**Returns:**
- `max_speed` (float): Maximum cornering speed in m/s

**Example:**
```python
# 100m radius corner, 3000N downforce
v_max = vehicle.calculate_corner_speed(100, 3000)
print(f"Max speed: {v_max*3.6:.1f} km/h")  # ≈ 186 km/h
```

**Physics:**
```
v_max = √((μ * (g + F_d/m)) * R)
```

---

#### calculate_max_acceleration()

Calculate maximum driving force at given velocity.

```python
force = vehicle.calculate_max_acceleration(
    velocity: float,
    downforce_total: float
) -> float
```

**Parameters:**
- `velocity` (float): Current velocity in m/s
- `downforce_total` (float): Total downforce in Newtons

**Returns:**
- `force` (float): Maximum driving force in Newtons

**Example:**
```python
# At 50 m/s with 5000 N downforce
f_max = vehicle.calculate_max_acceleration(50, 5000)
a_max = f_max / vehicle.mass
print(f"Max accel: {a_max/9.81:.1f}g")
```

---

#### calculate_max_braking()

Calculate maximum braking force at given velocity.

```python
force = vehicle.calculate_max_braking(
    velocity: float,
    downforce_total: float
) -> float
```

**Parameters:**
- `velocity` (float): Current velocity in m/s
- `downforce_total` (float): Total downforce in Newtons

**Returns:**
- `force` (float): Maximum braking force in Newtons

**Example:**
```python
f_brake = vehicle.calculate_max_braking(100, 8000)
a_brake = f_brake / vehicle.mass
print(f"Max decel: {a_brake/9.81:.2f}g")  # ≈ 7.68g
```

---

#### get_axle_normal_loads()

Calculate front and rear axle normal loads with load transfer.

```python
front_load, rear_load = vehicle.get_axle_normal_loads(
    longitudinal_acc: float = 0,
    lateral_acc: float = 0
) -> Tuple[float, float]
```

**Parameters:**
- `longitudinal_acc` (float, optional): Longitudinal acceleration in m/s² (default: 0)
- `lateral_acc` (float, optional): Lateral acceleration in m/s² (default: 0)

**Returns:**
- `front_load` (float): Front axle normal load in Newtons
- `rear_load` (float): Rear axle normal load in Newtons

**Example:**
```python
# No acceleration
f0, r0 = vehicle.get_axle_normal_loads()
print(f"Static: Front={f0:.0f}N, Rear={r0:.0f}N")

# Under 5 m/s² forward acceleration
f1, r1 = vehicle.get_axle_normal_loads(5.0, 0)
print(f"Accel: Front={f1:.0f}N, Rear={r1:.0f}N")
# Rear load increases, front decreases
```

**Physics:**
```
N_front = m*g*0.45 - (a_long * m * h_cg) / L
N_rear = m*g*0.55 + (a_long * m * h_cg) / L
```

---

#### _tire_mu_vs_normal()

Calculate tire friction coefficient as function of normal load.

```python
mu = vehicle._tire_mu_vs_normal(normal_force: float) -> float
```

**Parameters:**
- `normal_force` (float): Normal load on single tire in Newtons

**Returns:**
- `mu` (float): Friction coefficient (0.8 to 1.8)

**Example:**
```python
# At low load: friction is lower
mu_light = vehicle._tire_mu_vs_normal(2000)  # ≈ 1.4

# At nominal load: maximum friction
mu_nominal = vehicle._tire_mu_vs_normal(4000)  # ≈ 1.8

# At very high load: slight degradation
mu_high = vehicle._tire_mu_vs_normal(6000)  # ≈ 1.77
```

**Notes:**
- Implements load sensitivity of real tires
- Minimum μ = 0.8 (underload condition)
- Maximum μ = 1.8 (peak friction)

---

#### calculate_combined_tire_force()

Calculate combined longitudinal and lateral tire forces with friction circle.

```python
fx, fy = vehicle.calculate_combined_tire_force(
    slip_ratio: float,
    slip_angle: float,
    normal_force: float
) -> Tuple[float, float]
```

**Parameters:**
- `slip_ratio` (float): Longitudinal slip (0 to 1)
- `slip_angle` (float): Lateral slip angle in radians
- `normal_force` (float): Tire normal load in Newtons

**Returns:**
- `fx` (float): Longitudinal force in Newtons
- `fy` (float): Lateral force in Newtons

**Example:**
```python
# 20% accel slip + 5° cornering slip
fx, fy = vehicle.calculate_combined_tire_force(0.2, 0.087, 4000)
combined = np.hypot(fx, fy)
max_available = 1.8 * 4000
print(f"Combined force: {combined:.0f} N (max: {max_available:.0f} N)")
# Always ≤ friction circle limit
```

**Physics:**
Enforces friction circle constraint: `√(Fx² + Fy²) ≤ μ * N`

---

#### get_current_mass()

Get vehicle mass accounting for fuel consumption.

```python
mass = vehicle.get_current_mass(distance_km: float) -> float
```

**Parameters:**
- `distance_km` (float): Distance traveled in kilometers

**Returns:**
- `mass` (float): Current vehicle mass in kilograms

**Example:**
```python
m0 = vehicle.get_current_mass(0)      # 798 kg
m10 = vehicle.get_current_mass(10)    # ≈ 783 kg (after 10 km)
m100 = vehicle.get_current_mass(100)  # ≈ 598 kg (fuel depleted)
```

**Notes:**
- Consumption rate: 1.5 kg/km
- Minimum mass: 798 kg (regulation dry weight)

---

#### can_use_drs()

Determine if DRS (Drag Reduction System) is available.

```python
available = vehicle.can_use_drs(
    segment_type: str,
    speed_kmh: float
) -> bool
```

**Parameters:**
- `segment_type` (str): Track segment type ('straight', 'fast_corner', etc.)
- `speed_kmh` (float): Current speed in km/h

**Returns:**
- `available` (bool): True if DRS can be used

**Example:**
```python
# On straight at 200 km/h
drs_on = vehicle.can_use_drs('straight', 200)  # True

# In tight corner
drs_on = vehicle.can_use_drs('slow_corner', 150)  # False

# Below 100 km/h threshold
drs_on = vehicle.can_use_drs('straight', 80)  # False
```

**Rules:**
- Segment must be 'straight' or 'fast_corner'
- Speed must be > 100 km/h

---

## Track Class

Defines a track with segments.

### Constructor

```python
track = Track(name: str = "Generic Circuit")
```

**Parameters:**
- `name` (str): Track name

**Example:**
```python
track = Track("Monza-Style Circuit")
```

### Attributes

```python
track.name              # str: Track name
track.segments          # list: Segment definitions
track.total_length      # float: Total track length in meters
```

### Methods

#### add_segment()

Add a track segment.

```python
track.add_segment(
    length: float,
    radius: float = np.inf,
    banking: float = 0,
    elevation_change: float = 0
)
```

**Parameters:**
- `length` (float): Segment length in meters
- `radius` (float, optional): Corner radius in meters (default: inf for straight)
- `banking` (float, optional): Bank angle in degrees (default: 0)
- `elevation_change` (float, optional): Elevation change in meters (default: 0)

**Example:**
```python
track = Track("Silverstone")
track.add_segment(250, radius=100)      # Abbey corner
track.add_segment(400, radius=np.inf)   # Farm Straight
track.add_segment(80, radius=35)        # Village chicane
```

---

#### get_segment_at_distance()

Get track segment at given distance.

```python
segment = track.get_segment_at_distance(distance: float) -> dict
```

**Parameters:**
- `distance` (float): Distance from start in meters

**Returns:**
- `segment` (dict): Segment dictionary with keys:
  - `start`: Segment start distance (m)
  - `end`: Segment end distance (m)
  - `length`: Segment length (m)
  - `radius`: Corner radius (m)
  - `banking`: Bank angle (degrees)
  - `elevation`: Elevation change (m)

**Example:**
```python
segment = track.get_segment_at_distance(500)
print(f"At 500m: {segment['length']}m segment, radius={segment['radius']}m")
```

---

## Simulation Functions

### simulate_lap()

Run a complete lap simulation.

```python
telemetry_df, lap_time = simulate_lap(
    vehicle: F1Vehicle,
    track: Track,
    dt: float = 0.05
) -> Tuple[pd.DataFrame, float]
```

**Parameters:**
- `vehicle` (F1Vehicle): Vehicle to simulate
- `track` (Track): Track to simulate
- `dt` (float, optional): Timestep in seconds (default: 0.05 for 20 Hz)

**Returns:**
- `telemetry_df` (pd.DataFrame): Telemetry data with columns:
  - `time`: Elapsed time (s)
  - `distance`: Distance traveled (m)
  - `velocity`: Speed (km/h)
  - `acceleration`: Longitudinal accel (g)
  - `downforce`: Total downforce (kN)
  - `drag`: Drag force (kN)
  - `throttle`: Throttle input (0-1)
  - `brake`: Brake input (0-1)
  - `lateral_g`: Lateral acceleration (g)
  - `longitudinal_g`: Longitudinal acceleration (g)
- `lap_time` (float): Total lap time in seconds

**Example:**
```python
vehicle = F1Vehicle()
track = create_monza_style_track()
telemetry, lap_time = simulate_lap(vehicle, track)

print(f"Lap time: {lap_time:.3f}s")
print(f"Max speed: {telemetry['velocity'].max():.1f} km/h")
print(f"Max G: {telemetry['lateral_g'].max():.2f}g")
```

---

### plot_telemetry()

Create comprehensive telemetry visualization.

```python
plot_telemetry(
    telemetry: pd.DataFrame,
    lap_time: float,
    track_name: str
)
```

**Parameters:**
- `telemetry` (pd.DataFrame): Telemetry data from simulate_lap()
- `lap_time` (float): Lap time for title
- `track_name` (str): Track name for title

**Generates:**
- Speed vs distance plot
- Throttle/brake application
- G-force profile
- Downforce trace

**Example:**
```python
plot_telemetry(telemetry, 53.7, "Monza-Style Circuit")
# Saves: f1_lap_simulation.png
```

---

## Real Track Functions

### create_silverstone(), create_monaco(), create_spa()

Create real F1 circuit definitions.

```python
track = create_silverstone() -> RealF1Track
track = create_monaco() -> RealF1Track
track = create_spa() -> RealF1Track
```

**Returns:**
- `track` (RealF1Track): Real circuit with authentic geometry

**Example:**
```python
silverstone = create_silverstone()
print(f"Length: {silverstone.length}m")
print(f"Record: {silverstone.record_lap_time}s")
```

---

### simulate_real_track()

Simulate a lap on a real circuit.

```python
telemetry_df, lap_time = simulate_real_track(
    vehicle: F1Vehicle,
    track: RealF1Track,
    dt: float = 0.05
) -> Tuple[pd.DataFrame, float]
```

(Similar to `simulate_lap()` but with real circuit data)

---

### validate_against_real_f1()

Validate simulation against real F1 record.

```python
validation_dict = validate_against_real_f1(
    simulated_time: float,
    track: RealF1Track
) -> dict
```

**Returns:**
- `validation_dict` with keys:
  - `track`: Circuit name
  - `real_time`: Real F1 record (s)
  - `sim_time`: Simulation time (s)
  - `difference`: Time difference (s)
  - `error_percent`: Error percentage (%)

**Example:**
```python
validation = validate_against_real_f1(71.25, monaco)
print(f"Error: {validation['error_percent']:.2f}%")  # +1.54%
```

---

## Data Structures

### Telemetry DataFrame

Output from `simulate_lap()`:

```python
telemetry.columns:
- time (float): Elapsed time in seconds
- distance (float): Distance traveled in meters
- velocity (float): Speed in km/h
- acceleration (float): Longitudinal accel in g's
- downforce (float): Total downforce in kN
- drag (float): Drag force in kN
- throttle (float): Throttle input 0-1
- brake (float): Brake input 0-1
- lateral_g (float): Lateral g's
- longitudinal_g (float): Longitudinal g's

Length: ~1000-2000 rows per lap (depends on track length)
Sampling rate: 20 Hz (dt=0.05s)
```

### Segment Dictionary

Output from `track.get_segment_at_distance()`:

```python
segment = {
    'start': 0,              # Segment start (m)
    'end': 250,              # Segment end (m)
    'length': 250,           # Segment length (m)
    'radius': 100,           # Corner radius (m), inf for straight
    'banking': 0,            # Bank angle (degrees)
    'elevation': 0           # Elevation change (m)
}
```

---

## Error Handling

All functions include input validation:

```python
try:
    telemetry, lap_time = simulate_lap(vehicle, track)
except ValueError as e:
    print(f"Invalid input: {e}")
```

Common errors:
- Invalid track geometry (negative lengths)
- Invalid vehicle parameters (negative mass)
- Invalid simulation timestep (dt ≤ 0)

---

**For implementation examples, see the main simulator files.**
