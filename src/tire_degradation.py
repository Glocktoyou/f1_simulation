"""
F1 Tire Degradation Model
Author: F1 Simulation Team
Date: December 2025

Comprehensive tire degradation modeling including:
- Pirelli compound characteristics (C1-C5)
- Track abrasiveness factors
- Surface wear, thermal degradation
- Temperature dynamics
- Cliff effect modeling
- Flatspot damage

This module extends the F1 simulation without modifying existing code.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import sys
import os

# Import from existing F1 simulation module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from f1_simulation import F1Vehicle


@dataclass
class TireCompound:
    """Pirelli F1 tire compound characteristics"""
    name: str
    code: str  # C1-C5
    optimal_temp_min: float  # Celsius
    optimal_temp_max: float  # Celsius
    peak_grip: float  # Relative to baseline
    wear_rate: float  # Relative wear speed
    thermal_degradation: float  # Thermal sensitivity
    cliff_threshold: float  # Wear level where cliff begins (0-1)
    heating_rate: float  # How quickly tire heats up


# Pirelli compound database
TIRE_COMPOUNDS = {
    'C1': TireCompound(
        name='Hard',
        code='C1',
        optimal_temp_min=100,
        optimal_temp_max=110,
        peak_grip=0.95,
        wear_rate=0.5,
        thermal_degradation=0.3,
        cliff_threshold=0.85,
        heating_rate=0.7
    ),
    'C2': TireCompound(
        name='Medium-Hard',
        code='C2',
        optimal_temp_min=95,
        optimal_temp_max=105,
        peak_grip=0.98,
        wear_rate=0.7,
        thermal_degradation=0.4,
        cliff_threshold=0.82,
        heating_rate=0.8
    ),
    'C3': TireCompound(
        name='Medium',
        code='C3',
        optimal_temp_min=90,
        optimal_temp_max=100,
        peak_grip=1.0,
        wear_rate=1.0,
        thermal_degradation=0.5,
        cliff_threshold=0.80,
        heating_rate=1.0
    ),
    'C4': TireCompound(
        name='Soft',
        code='C4',
        optimal_temp_min=85,
        optimal_temp_max=95,
        peak_grip=1.03,
        wear_rate=1.4,
        thermal_degradation=0.6,
        cliff_threshold=0.75,
        heating_rate=1.2
    ),
    'C5': TireCompound(
        name='Hyper-Soft',
        code='C5',
        optimal_temp_min=80,
        optimal_temp_max=90,
        peak_grip=1.05,
        wear_rate=1.8,
        thermal_degradation=0.7,
        cliff_threshold=0.70,
        heating_rate=1.4
    ),
}


# Track abrasiveness factors
TRACK_ABRASIVENESS = {
    'Monaco': 0.6,        # Low abrasion (smooth street circuit)
    'Singapore': 0.7,     # Low-medium
    'Silverstone': 1.0,   # Medium (baseline)
    'Barcelona': 1.1,     # Medium-high
    'Spa': 1.2,           # High
    'Paul Ricard': 1.3,   # High
    'Bahrain': 1.5,       # Very high (sand, heat)
}


class TireDegradationModel:
    """
    Comprehensive tire degradation model for F1 simulation.
    
    Models:
    - Surface wear from sliding/abrasion
    - Thermal degradation (graining, blistering)
    - Temperature dynamics (surface and core)
    - Optimal temperature windows
    - Cliff effect (sudden grip drop-off)
    - Flatspot damage
    """
    
    def __init__(self, compound: str, track_name: str = 'Silverstone'):
        """
        Initialize tire degradation model.
        
        Args:
            compound: Tire compound code ('C1' to 'C5')
            track_name: Track name for abrasiveness factor
        """
        if compound not in TIRE_COMPOUNDS:
            raise ValueError(f"Unknown compound: {compound}. Must be C1-C5.")
        
        self.compound = TIRE_COMPOUNDS[compound]
        self.track_abrasiveness = TRACK_ABRASIVENESS.get(track_name, 1.0)
        
        # Tire state variables
        self.wear_level = 0.0  # 0=new, 1=worn out
        self.surface_temp = 60.0  # Celsius
        self.core_temp = 50.0  # Celsius
        self.thermal_damage = 0.0  # 0=no damage, 1=severe
        self.flatspot_damage = 0.0  # 0=no flatspot, 1=severe
        self.laps_completed = 0
        
        # Track history for visualization
        self.history = {
            'laps': [],
            'wear': [],
            'grip_multiplier': [],
            'surface_temp': [],
            'thermal_damage': []
        }
        
    def get_grip_multiplier(self) -> float:
        """
        Calculate current grip relative to fresh tire.
        
        Returns:
            Grip multiplier (1.0 = fresh tire performance)
        """
        # Base grip from compound
        base_grip = self.compound.peak_grip
        
        # Temperature effect
        temp_mult = self._calculate_temperature_effect()
        
        # Wear effect (gradual until cliff)
        wear_mult = self._calculate_wear_effect()
        
        # Thermal degradation (graining, blistering)
        thermal_mult = 1.0 - (self.thermal_damage * 0.5)
        
        # Flatspot damage
        flatspot_mult = 1.0 - (self.flatspot_damage * 0.3)
        
        # Combined grip
        total_grip = base_grip * temp_mult * wear_mult * thermal_mult * flatspot_mult
        
        return total_grip
    
    def _calculate_temperature_effect(self) -> float:
        """Calculate grip multiplier based on tire temperature"""
        temp = self.surface_temp
        opt_min = self.compound.optimal_temp_min
        opt_max = self.compound.optimal_temp_max
        
        if opt_min <= temp <= opt_max:
            # In optimal window
            return 1.0
        elif temp < opt_min:
            # Too cold - reduced grip
            temp_diff = opt_min - temp
            return max(0.7, 1.0 - temp_diff * 0.01)
        else:
            # Too hot - reduced grip and thermal damage risk
            temp_diff = temp - opt_max
            return max(0.75, 1.0 - temp_diff * 0.008)
    
    def _calculate_wear_effect(self) -> float:
        """Calculate grip loss due to wear, including cliff effect"""
        wear = self.wear_level
        cliff_threshold = self.compound.cliff_threshold
        
        if wear < cliff_threshold:
            # Gradual linear degradation before cliff
            return 1.0 - (wear * 0.15)
        else:
            # Cliff effect - rapid grip loss
            base_at_cliff = 1.0 - (cliff_threshold * 0.15)
            cliff_progress = (wear - cliff_threshold) / (1.0 - cliff_threshold)
            cliff_loss = cliff_progress * 0.5  # Lose up to 50% more grip in cliff
            return max(0.3, base_at_cliff - cliff_loss)
    
    def simulate_lap(self, avg_speed_kmh: float = 200.0, 
                     cornering_severity: float = 1.0,
                     lockup_events: int = 0) -> None:
        """
        Update tire state after one lap.
        
        Args:
            avg_speed_kmh: Average lap speed in km/h
            cornering_severity: Factor for corner intensity (0.5=easy, 1.5=hard)
            lockup_events: Number of lockups during lap
        """
        # Convert speed to m/s
        avg_speed_ms = avg_speed_kmh / 3.6
        
        # Base wear accumulation
        base_wear_per_lap = 0.015 * self.compound.wear_rate * self.track_abrasiveness
        wear_increment = base_wear_per_lap * cornering_severity
        self.wear_level = min(1.0, self.wear_level + wear_increment)
        
        # Temperature dynamics
        self._update_temperature(avg_speed_ms, cornering_severity)
        
        # Thermal degradation (if overheating)
        if self.surface_temp > self.compound.optimal_temp_max + 10:
            overheat_amount = (self.surface_temp - self.compound.optimal_temp_max - 10) / 50.0
            thermal_damage_increment = overheat_amount * self.compound.thermal_degradation * 0.02
            self.thermal_damage = min(1.0, self.thermal_damage + thermal_damage_increment)
        
        # Flatspot from lockups
        if lockup_events > 0:
            flatspot_increment = lockup_events * 0.15
            self.flatspot_damage = min(1.0, self.flatspot_damage + flatspot_increment)
        
        # Update lap counter
        self.laps_completed += 1
        
        # Record history
        self.history['laps'].append(self.laps_completed)
        self.history['wear'].append(self.wear_level)
        self.history['grip_multiplier'].append(self.get_grip_multiplier())
        self.history['surface_temp'].append(self.surface_temp)
        self.history['thermal_damage'].append(self.thermal_damage)
    
    def _update_temperature(self, speed_ms: float, cornering_severity: float) -> None:
        """Update tire temperatures based on usage"""
        # Heat generation from friction
        heat_generation = (speed_ms / 80.0) * cornering_severity * self.compound.heating_rate
        
        # Target temperature based on usage
        target_temp = 60 + heat_generation * 40
        
        # Approach target (thermal inertia)
        self.surface_temp += (target_temp - self.surface_temp) * 0.3
        self.core_temp += (target_temp - self.core_temp) * 0.15
        
        # Cooling (ambient)
        ambient_temp = 25.0
        self.surface_temp -= (self.surface_temp - ambient_temp) * 0.05
        self.core_temp -= (self.core_temp - ambient_temp) * 0.02
    
    def get_lap_time_delta(self, base_lap_time: float) -> float:
        """
        Calculate lap time loss due to degradation.
        
        Args:
            base_lap_time: Fresh tire lap time in seconds
            
        Returns:
            Time delta in seconds (positive = slower)
        """
        grip_mult = self.get_grip_multiplier()
        # Approximate: 10% grip loss ≈ 1% lap time increase
        time_penalty_factor = (1.0 - grip_mult) * 10.0
        return base_lap_time * (time_penalty_factor / 100.0)
    
    def get_remaining_life(self) -> int:
        """
        Estimate laps before cliff effect.
        
        Returns:
            Estimated laps remaining until cliff
        """
        if self.wear_level >= self.compound.cliff_threshold:
            return 0
        
        remaining_wear = self.compound.cliff_threshold - self.wear_level
        # Assume similar wear rate as recent laps
        if self.laps_completed > 0:
            avg_wear_per_lap = self.wear_level / self.laps_completed
            if avg_wear_per_lap > 0:
                return int(remaining_wear / avg_wear_per_lap)
        
        # Fallback estimate
        return int(remaining_wear / (0.015 * self.compound.wear_rate * self.track_abrasiveness))


class DegradingF1Vehicle:
    """
    Wrapper for F1Vehicle that adds tire degradation effects.
    Does NOT modify F1Vehicle - wraps it and adjusts grip.
    """
    
    def __init__(self, compound: str = 'C3', track_name: str = 'Silverstone'):
        """
        Initialize F1 vehicle with tire degradation.
        
        Args:
            compound: Tire compound code ('C1' to 'C5')
            track_name: Track name for abrasiveness
        """
        self.base_vehicle = F1Vehicle()
        self.tire_model = TireDegradationModel(compound, track_name)
        
    def get_effective_grip(self) -> float:
        """Get current tire grip coefficient"""
        base_mu = self.base_vehicle.tire_mu_peak
        grip_mult = self.tire_model.get_grip_multiplier()
        return base_mu * grip_mult
    
    def simulate_lap_with_degradation(self, avg_speed_kmh: float = 200.0) -> Dict:
        """
        Simulate one lap with tire degradation.
        
        Args:
            avg_speed_kmh: Average lap speed
            
        Returns:
            Dictionary with lap results
        """
        # Get current grip
        current_grip = self.get_effective_grip()
        
        # Update tire state
        self.tire_model.simulate_lap(avg_speed_kmh)
        
        return {
            'lap': self.tire_model.laps_completed,
            'grip': current_grip,
            'wear': self.tire_model.wear_level,
            'temp': self.tire_model.surface_temp,
        }


# Visualization functions

def plot_tire_degradation(compound: str, track_name: str = 'Silverstone', 
                          num_laps: int = 30, avg_speed: float = 200.0,
                          save_path: Optional[str] = None) -> None:
    """
    Plot single compound degradation analysis.
    
    Args:
        compound: Tire compound code
        track_name: Track name
        num_laps: Number of laps to simulate
        avg_speed: Average lap speed in km/h
        save_path: Optional path to save figure
    """
    model = TireDegradationModel(compound, track_name)
    
    # Simulate stint
    for lap in range(num_laps):
        model.simulate_lap(avg_speed_kmh=avg_speed)
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'Tire Degradation Analysis: {compound} ({model.compound.name}) @ {track_name}',
                 fontsize=14, fontweight='bold')
    
    laps = model.history['laps']
    
    # Grip multiplier
    ax = axes[0, 0]
    ax.plot(laps, model.history['grip_multiplier'], 'b-', linewidth=2)
    ax.axhline(y=model.compound.cliff_threshold * 0.85, color='r', linestyle='--', 
               label='Cliff zone', alpha=0.5)
    ax.set_xlabel('Lap')
    ax.set_ylabel('Grip Multiplier')
    ax.set_title('Grip vs Lap')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Wear level
    ax = axes[0, 1]
    ax.plot(laps, model.history['wear'], 'g-', linewidth=2)
    ax.axhline(y=model.compound.cliff_threshold, color='r', linestyle='--', 
               label=f'Cliff threshold ({model.compound.cliff_threshold:.0%})', alpha=0.7)
    ax.set_xlabel('Lap')
    ax.set_ylabel('Wear Level')
    ax.set_title('Tire Wear Progression')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Temperature
    ax = axes[1, 0]
    ax.plot(laps, model.history['surface_temp'], 'r-', linewidth=2, label='Surface')
    ax.axhspan(model.compound.optimal_temp_min, model.compound.optimal_temp_max,
               alpha=0.2, color='green', label='Optimal window')
    ax.set_xlabel('Lap')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('Tire Surface Temperature')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Thermal damage
    ax = axes[1, 1]
    ax.plot(laps, model.history['thermal_damage'], 'm-', linewidth=2)
    ax.set_xlabel('Lap')
    ax.set_ylabel('Thermal Damage')
    ax.set_title('Accumulated Thermal Damage')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()


def compare_compounds(track_name: str = 'Silverstone', num_laps: int = 40,
                     avg_speed: float = 200.0, save_path: Optional[str] = None) -> None:
    """
    Compare all tire compounds on same track.
    
    Args:
        track_name: Track name
        num_laps: Number of laps to simulate
        avg_speed: Average lap speed
        save_path: Optional path to save figure
    """
    compounds = ['C1', 'C2', 'C3', 'C4', 'C5']
    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Tire Compound Comparison @ {track_name}', 
                 fontsize=14, fontweight='bold')
    
    for compound, color in zip(compounds, colors):
        model = TireDegradationModel(compound, track_name)
        
        # Simulate
        for lap in range(num_laps):
            model.simulate_lap(avg_speed_kmh=avg_speed)
        
        laps = model.history['laps']
        
        # Plot grip
        ax = axes[0]
        ax.plot(laps, model.history['grip_multiplier'], color=color, linewidth=2,
                label=f"{compound} ({model.compound.name})")
        
        # Plot wear
        ax = axes[1]
        ax.plot(laps, model.history['wear'], color=color, linewidth=2,
                label=f"{compound} ({model.compound.name})")
    
    # Configure axes
    axes[0].set_xlabel('Lap', fontsize=11)
    axes[0].set_ylabel('Grip Multiplier', fontsize=11)
    axes[0].set_title('Grip Degradation', fontsize=12)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='best')
    
    axes[1].set_xlabel('Lap', fontsize=11)
    axes[1].set_ylabel('Wear Level', fontsize=11)
    axes[1].set_title('Wear Progression', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='best')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()


def simulate_stint(compound: str, track_name: str = 'Silverstone',
                  num_laps: int = 25, base_lap_time: float = 90.0):
    """
    Simulate full stint with degradation and return telemetry.
    
    Args:
        compound: Tire compound code
        track_name: Track name
        num_laps: Stint length in laps
        base_lap_time: Base lap time in seconds
        
    Returns:
        DataFrame with lap-by-lap data
    """
    model = TireDegradationModel(compound, track_name)
    
    data = []
    for lap in range(num_laps):
        # Simulate lap
        model.simulate_lap(avg_speed_kmh=200.0)
        
        # Calculate lap time with degradation
        time_delta = model.get_lap_time_delta(base_lap_time)
        lap_time = base_lap_time + time_delta
        
        data.append({
            'Lap': lap + 1,
            'Compound': compound,
            'Lap_Time': lap_time,
            'Grip': model.get_grip_multiplier(),
            'Wear': model.wear_level,
            'Temp': model.surface_temp,
            'Thermal_Damage': model.thermal_damage,
            'Remaining_Life': model.get_remaining_life()
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    """Demo: Tire degradation analysis"""
    
    print("="*70)
    print("F1 TIRE DEGRADATION MODEL - DEMONSTRATION")
    print("="*70)
    
    # Demo 1: Single compound analysis
    print("\n1. Analyzing C3 (Medium) compound at Silverstone...")
    plot_tire_degradation('C3', 'Silverstone', num_laps=30, 
                         save_path='tire_deg_c3_silverstone.png')
    print("   ✓ Created tire_deg_c3_silverstone.png")
    
    # Demo 2: Compare all compounds
    print("\n2. Comparing all compounds at Silverstone...")
    compare_compounds('Silverstone', num_laps=40,
                     save_path='compound_comparison.png')
    print("   ✓ Created compound_comparison.png")
    
    # Demo 3: Stint simulation with data
    print("\n3. Simulating 25-lap stint on C4 (Soft) at Bahrain...")
    stint_data = simulate_stint('C4', 'Bahrain', num_laps=25, base_lap_time=92.0)
    print(f"\n   Stint Summary:")
    print(f"   - Starting lap time: {stint_data.iloc[0]['Lap_Time']:.3f}s")
    print(f"   - Final lap time: {stint_data.iloc[-1]['Lap_Time']:.3f}s")
    print(f"   - Delta: +{stint_data.iloc[-1]['Lap_Time'] - stint_data.iloc[0]['Lap_Time']:.3f}s")
    print(f"   - Final grip: {stint_data.iloc[-1]['Grip']:.1%}")
    print(f"   - Final wear: {stint_data.iloc[-1]['Wear']:.1%}")
    
    # Demo 4: DegradingF1Vehicle wrapper
    print("\n4. Testing DegradingF1Vehicle wrapper...")
    vehicle = DegradingF1Vehicle(compound='C3', track_name='Monaco')
    print(f"   - Initial grip: {vehicle.get_effective_grip():.3f}")
    
    for lap in range(1, 6):
        result = vehicle.simulate_lap_with_degradation(avg_speed_kmh=180.0)
        print(f"   - Lap {lap}: grip={result['grip']:.3f}, wear={result['wear']:.1%}")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - tire_deg_c3_silverstone.png")
    print("  - compound_comparison.png")
    print("\nNext: Run src/race_strategy.py for race strategy optimization!")
