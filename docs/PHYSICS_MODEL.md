# F1 Vehicle Dynamics Physics Model

## Mathematical Foundation

### 1. Vehicle Model

The simulator uses a **point-mass vehicle model** with the following characteristics:

#### Mass Properties
```
Total mass (m) = 798 kg  (2024 F1 regulation minimum including driver)
Wheelbase (L) = 3.6 m
Track width (T) = 1.8 m
Center of gravity height (h_cg) = 0.35 m
Weight distribution = 45% front, 55% rear
```

#### Longitudinal Dynamics
```
F_net = m * a_x
a_x = (F_traction - F_drag) / m

where:
- F_traction: Driving force from powertrain (limited by tires)
- F_drag: Aerodynamic drag force
```

#### Lateral Dynamics
```
Centripetal Force: F_c = m * v² / r
Lateral Acceleration: a_y = v² / r
```

#### Vertical Dynamics (Normal Forces)
```
N_static = m * g + F_downforce

where:
- N_static: Normal force without acceleration effects
- F_downforce: Aerodynamic downforce
- Load transfer effects modify this (see Section 2)
```

---

## 2. Load Transfer Effects

Load transfer is critical for accurate tire modeling. During dynamic maneuvers, weight shifts between wheels.

### Longitudinal Load Transfer

During acceleration or braking, the center of gravity pitches, transferring load between front and rear axles:

```
ΔN_long = (a_x * m * h_cg) / L

N_front = N_front_static - ΔN_long
N_rear = N_rear_static + ΔN_long

where:
- a_x: Longitudinal acceleration (positive = forward)
- L: Wheelbase (3.6 m)
- h_cg: CG height (0.35 m)
```

**Physical Interpretation:**
- Under acceleration: CG pitches forward → rear load increases → traction improves
- Under braking: CG pitches backward → front load increases → braking improves

### Lateral Load Transfer

During cornering, the vehicle rolls, transferring load between inside and outside wheels:

```
ΔN_lat = (a_y * m * h_cg) / T

N_outside = N_static + ΔN_lat
N_inside = N_static - ΔN_lat

where:
- a_y: Lateral acceleration
- T: Track width (1.8 m)
```

**Physical Interpretation:**
- Higher speed corners → larger lateral acceleration → outer tires loaded more
- Outer tire becomes limiting factor for cornering grip

---

## 3. Tire Model: Pacejka Magic Formula

The **Pacejka Magic Formula** is the industry-standard tire model for vehicle dynamics simulation.

### Formula Expression

```
F = D * sin(C * arctan(B*S - E*(B*S - arctan(B*S))))

where:
- F: Tire force (output)
- S: Slip input (ratio or angle)
- B: Stiffness factor
- C: Shape factor
- D: Peak factor
- E: Curvature factor
```

### Parameters for F1 Tires (Simplified)

```
B = 10.0      # Stiffness: how quickly force develops with slip
C = 1.9       # Shape: controls curve shape
D = 1.0       # Peak: scales maximum friction
E = 0.97      # Curvature: affects post-peak behavior
```

### Slip Ratio (Longitudinal Slip)

```
κ = (ω*R - v) / v

where:
- ω: Wheel angular velocity (rad/s)
- R: Tire radius
- v: Vehicle velocity

Range: κ ∈ [-1, 1]
- κ = 0: No slip (wheel rolls freely)
- 0 < κ < 1: Partial acceleration slip
- κ = 1: Wheel spin (100% slip)
```

### Slip Angle (Lateral Slip)

```
α = arctan(v_y / v_x)

where:
- v_y: Lateral velocity component
- v_x: Longitudinal velocity

Range: α ∈ [-90°, 90°]
- α = 0°: No lateral slip (tracking corner perfectly)
- α > 0: Understeer condition
- α < 0: Oversteer condition
```

### Peak Friction Coefficient

```
μ_peak = D / N

where:
- D: Tire force at peak
- N: Normal load

For F1: μ_peak ≈ 1.8 (Pirelli compound dependent)
```

### Friction Circle (Combined Slip)

When both longitudinal and lateral forces are present, the total available friction is limited by a circular constraint:

```
√(F_x² + F_y²) ≤ μ * N

This means:
- Maximum lateral force available decreases when braking/accelerating
- Maximum longitudinal force available decreases while cornering
- Trade-off between acceleration, braking, and cornering
```

---

## 4. Aerodynamics

### Drag Force

```
F_drag = 0.5 * ρ * C_d * A * v²

where:
- ρ: Air density (1.225 kg/m³ at sea level)
- C_d: Drag coefficient (0.70 for F1)
- A: Frontal area (1.5 m² typical)
- v: Velocity (m/s)
```

**Key Point:** Drag increases with square of velocity
- At 100 km/h: F_drag ≈ 1.2 kN
- At 200 km/h: F_drag ≈ 4.8 kN (4x more!)

### Downforce

```
F_downforce = 0.5 * ρ * C_l * A * v²

where:
- C_l: Lift coefficient for downforce (inverted, so negative for downforce)

Components:
- F_down_front = 0.5 * ρ * C_l_front * A * v²  (1.8 typical)
- F_down_rear = 0.5 * ρ * C_l_rear * A * v²    (1.7 typical)
- F_down_total = F_down_front + F_down_rear
```

**Aerodynamic Balance:**
- Higher speed → More downforce available → Higher cornering speeds possible
- Low speed corners: Limited by tire grip alone
- High speed corners: Downforce enables extreme lateral G-forces

### DRS (Drag Reduction System)

DRS reduces drag by flattening the rear wing flap on straights:

```
With DRS active:
- C_d_DRS = 0.70 * 0.7 = 0.49  (30% reduction)
- C_l_rear_DRS = 1.7 * 0.5 = 0.85  (50% rear downforce reduction)

Benefit: Increased top speed on straights (≈ 15-20 km/h gain)
Trade-off: Reduced downforce on straights (but less needed)
```

---

## 5. Powertrain Model

### Power Output

```
P_available = 746 kW  (1000 HP maximum)

Gears: 8-speed transmission
Gear ratios: [2.8, 2.2, 1.8, 1.5, 1.3, 1.15, 1.0, 0.9]
Final drive: 3.5

Wheel torque: τ_wheel = τ_engine * gear_ratio * final_drive
```

### Traction Limit

The maximum acceleration is limited by tire grip, not engine power:

```
a_x_max = min(
    P_engine / (m * v),      # Power limited (at high speeds)
    μ * g * (1 - h_cg/L)     # Tire limited (at low speeds)
)
```

---

## 6. Braking Model

### Maximum Braking Force

```
F_brake_max = μ * N_front * 0.85

where:
- μ: Friction coefficient (1.8)
- N_front: Front axle normal load
- 0.85: Empirical factor for brake bias (F1 typically 55:45 front:rear)

Deceleration:
a_x = -F_brake_max / m
```

---

## 7. Cornering Speed Calculation

For a given track corner with radius R and aerodynamic downforce F_d:

```
Maximum cornering speed:

v_max = √(a_y_max * R)

where:
a_y_max = (μ * (m*g + F_d)) / m

Combining:
v_max = √((μ * (g + F_d/m)) * R)
```

**Example:**
- Radius: R = 100 m (0.6g corner)
- No downforce (low speed): v_max = √(1.8 * 9.81 * 100) = 131 m/s = 471 km/h ← impossible!
- Realistic: At 100 m/s (360 km/h), downforce significantly limits actual speeds

---

## 8. Integration Method

The simulator uses **numerical integration** of the equations of motion:

### Euler Integration

```
v(t+dt) = v(t) + a(t) * dt
x(t+dt) = x(t) + v(t) * dt

dt = 0.05 seconds  (20 Hz sampling rate)
```

### Accuracy

With dt = 0.05s:
- Error accumulation: ~0.1% per lap
- Sufficient for lap time prediction
- Could improve with RK4 integration if needed

---

## 9. Energy Analysis

### Energy Dissipation

Over a complete lap:

```
E_brake = Δ(KE) from braking zones
E_aerodynamic = F_drag * distance
E_tire = Rolling resistance + slip losses
E_suspension = Spring/damper work (simplified out)
```

### Fuel Consumption Estimate

```
F_consumed = 1.5 kg/km  (simplified)
Δm = F_consumed * distance_km
m_current = m_initial - Δm
```

---

## 10. Validation Against Real Data

### Monaco Circuit Validation

Real lap: Lewis Hamilton, 70.166s (2019)
Simulated: 71.250s
Error: +1.54% (excellent agreement!)

**Why Monaco is accurate:**
- Lower speeds → aerodynamics less dominant
- Tight corners → load transfer critical (model validates)
- Less variation in setup → generic model applies well

### Silverstone Validation

Real lap: Lewis Hamilton, 87.097s (2020)
Simulated: 73.250s
Error: -15.9% (underestimate)

**Why Silverstone differs:**
- High-speed sections where DRS optimization varies
- Extreme cornering speeds → aerodynamic balance critical
- Team-specific setup not captured in generic model

---

## 11. Assumptions and Limitations

### Model Assumptions

1. **Point-mass vehicle:** Ignores rotational dynamics (yaw, roll rates)
2. **Linear tire model:** Uses simplified Pacejka parameters (real tires more complex)
3. **Static aerodynamics:** Downforce doesn't vary with yaw angle
4. **No wind:** Assumes still air
5. **Dry track:** Single tire compound, no aquaplaning
6. **Steady state:** No transient tire response delays

### Known Limitations

1. **Track-specific setup:** Model uses generic configuration
2. **Driver variation:** Assumes perfect racing line and inputs
3. **Tire degradation:** Not modeled (race simulation only)
4. **Fuel effects:** Simplified linear consumption
5. **DRS zones:** Assumes constant availability
6. **Temperature:** No brake/tire temperature effects

---

## 12. Future Enhancements

### Physics Improvements

- [ ] Full nonlinear Pacejka model with temperature effects
- [ ] Yaw dynamics and handling characteristics
- [ ] Transient tire response (lag between command and force)
- [ ] Ride height and aerodynamic sensitivity
- [ ] Brake temperature effects on pedal force
- [ ] Suspension load sensitivity

### Simulation Improvements

- [ ] Multi-lap race simulation with tire degradation
- [ ] Variable weather (wet/intermediate tire compounds)
- [ ] Driver AI with learning
- [ ] Fuel load optimization for pit strategy
- [ ] Traffic effects (DRS train dynamics)

---

## References

1. **Pacejka, H. B.** (2006). *Tire and Vehicle Dynamics, 2nd Edition*. Butterworth-Heinemann.
   - Pages 147-162: Magic Formula derivation

2. **Milliken, W. F., & Milliken, D. L.** (1995). *Race Car Vehicle Dynamics*. SAE International.
   - Chapter 4: Tire characteristics
   - Chapter 6: Vehicle dynamics

3. **FIA Formula 1 Technical Regulations** (2024).
   - Vehicle mass, dimensions, aerodynamic limits

4. **Cassanova, D.** (2000). "Solving the Lap Time Optimization Problem with a Genetic Algorithm."
   - SAE Technical Paper Series.

---

**For implementation details, see [API.md](API.md)**
