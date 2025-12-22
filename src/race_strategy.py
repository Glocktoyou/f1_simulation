"""
F1 Race Strategy Optimizer
Author: F1 Simulation Team
Date: December 2025

Race strategy optimization using Monte Carlo simulation with realistic tire degradation.
Analyzes different pit stop strategies to find optimal race approach.

Features:
- Full race simulation with tire degradation
- Multiple pit stop strategy comparison
- Grid search for optimal stop windows
- Comprehensive visualization and analysis

This module extends the F1 simulation without modifying existing code.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import sys
import os

# Import from existing modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tire_degradation import TireDegradationModel, TIRE_COMPOUNDS


@dataclass
class PitStop:
    """Represents a pit stop during the race"""
    lap: int
    compound_before: str
    compound_after: str
    time_loss: float  # Time lost in pits (seconds)


@dataclass
class Strategy:
    """Represents a complete race strategy"""
    name: str
    compounds: List[str]  # List of compounds in order of use
    pit_laps: List[int]  # Laps on which to pit
    
    def __str__(self):
        return f"{self.name}: {' → '.join(self.compounds)}"


class RaceStrategySimulator:
    """
    Simulates full F1 race with different pit strategies.
    Uses tire degradation model for realistic tire behavior.
    """
    
    def __init__(self, track_name: str = 'Silverstone', total_laps: int = 52,
                 base_lap_time: float = 90.0, pit_loss: float = 22.0,
                 fuel_effect: float = 0.03):
        """
        Initialize race strategy simulator.
        
        Args:
            track_name: Track name for tire modeling
            total_laps: Total race laps
            base_lap_time: Base lap time on fresh C3 tires (seconds)
            pit_loss: Time lost per pit stop (seconds)
            fuel_effect: Lap time gain per lap due to fuel burn (seconds)
        """
        self.track_name = track_name
        self.total_laps = total_laps
        self.base_lap_time = base_lap_time
        self.pit_loss = pit_loss
        self.fuel_effect = fuel_effect
        
    def simulate_strategy(self, strategy: Strategy, verbose: bool = False) -> Dict:
        """
        Simulate race with given strategy.
        
        Args:
            strategy: Strategy to simulate
            verbose: Print lap-by-lap details
            
        Returns:
            Dictionary with race results
        """
        if len(strategy.compounds) != len(strategy.pit_laps) + 1:
            raise ValueError("Number of compounds must be one more than pit stops")
        
        # Initialize tracking
        current_lap = 1
        stint_lap = 1
        stint_index = 0
        total_time = 0.0
        
        # History for visualization
        lap_times = []
        cumulative_times = []
        grip_levels = []
        compounds_used = []
        tire_ages = []
        
        # Start first stint
        current_compound = strategy.compounds[stint_index]
        tire_model = TireDegradationModel(current_compound, self.track_name)
        
        if verbose:
            print(f"\nSimulating: {strategy}")
            print(f"{'Lap':<5} {'Stint':<6} {'Compound':<10} {'Age':<5} {'Grip':<6} {'Lap Time':<10} {'Total':<10}")
            print("-" * 70)
        
        while current_lap <= self.total_laps:
            # Check for pit stop
            if current_lap in strategy.pit_laps:
                # Pit stop
                total_time += self.pit_loss
                stint_index += 1
                stint_lap = 1
                
                # Change tires
                old_compound = current_compound
                current_compound = strategy.compounds[stint_index]
                tire_model = TireDegradationModel(current_compound, self.track_name)
                
                if verbose:
                    print(f"{current_lap:<5} {'PIT':<6} {old_compound} → {current_compound:<7} {'-':<5} {'-':<6} {f'+{self.pit_loss:.1f}s':<10} {total_time:.1f}s")
            
            # Simulate lap
            grip_mult = tire_model.get_grip_multiplier()
            
            # Calculate lap time
            # Base time + tire degradation - fuel effect
            tire_delta = tire_model.get_lap_time_delta(self.base_lap_time)
            fuel_benefit = (self.total_laps - current_lap) * self.fuel_effect
            lap_time = self.base_lap_time + tire_delta - fuel_benefit
            
            # Record lap
            total_time += lap_time
            lap_times.append(lap_time)
            cumulative_times.append(total_time)
            grip_levels.append(grip_mult)
            compounds_used.append(current_compound)
            tire_ages.append(stint_lap)
            
            if verbose:
                print(f"{current_lap:<5} {stint_lap:<6} {current_compound:<10} {stint_lap:<5} {grip_mult:.3f}  {lap_time:.3f}s    {total_time:.1f}s")
            
            # Update tire state for next lap
            tire_model.simulate_lap(avg_speed_kmh=200.0)
            
            current_lap += 1
            stint_lap += 1
        
        return {
            'strategy': strategy,
            'total_time': total_time,
            'lap_times': lap_times,
            'cumulative_times': cumulative_times,
            'grip_levels': grip_levels,
            'compounds_used': compounds_used,
            'tire_ages': tire_ages,
            'avg_lap_time': np.mean(lap_times),
            'pit_stops': len(strategy.pit_laps)
        }
    
    def compare_strategies(self, strategies: List[Strategy], 
                          verbose: bool = False) -> List[Dict]:
        """
        Compare multiple strategies and return sorted results.
        
        Args:
            strategies: List of strategies to compare
            verbose: Print detailed results
            
        Returns:
            List of results sorted by total time (fastest first)
        """
        results = []
        
        print(f"\n{'='*70}")
        print(f"RACE STRATEGY COMPARISON - {self.track_name} ({self.total_laps} laps)")
        print(f"{'='*70}")
        
        for strategy in strategies:
            result = self.simulate_strategy(strategy, verbose=verbose)
            results.append(result)
            
            print(f"\n{strategy.name}:")
            print(f"  Compounds: {' → '.join(strategy.compounds)}")
            print(f"  Pit laps: {strategy.pit_laps}")
            print(f"  Total time: {result['total_time']:.3f}s")
            print(f"  Avg lap: {result['avg_lap_time']:.3f}s")
        
        # Sort by total time
        results.sort(key=lambda x: x['total_time'])
        
        print(f"\n{'='*70}")
        print("RANKING:")
        print(f"{'='*70}")
        for i, result in enumerate(results, 1):
            time_diff = result['total_time'] - results[0]['total_time']
            print(f"{i}. {result['strategy'].name:<30} {result['total_time']:.3f}s (+{time_diff:.3f}s)")
        
        return results
    
    def find_optimal_1stop(self, compound1: str = 'C4', compound2: str = 'C2',
                          search_range: Tuple[int, int] = None) -> Tuple[Strategy, Dict]:
        """
        Grid search for optimal 1-stop strategy.
        
        Args:
            compound1: First stint compound
            compound2: Second stint compound
            search_range: Tuple of (min_lap, max_lap) to search, or None for auto
            
        Returns:
            Tuple of (best_strategy, result)
        """
        if search_range is None:
            # Search middle third of race
            search_range = (self.total_laps // 3, 2 * self.total_laps // 3)
        
        print(f"\nSearching for optimal 1-stop: {compound1} → {compound2}")
        print(f"Search range: laps {search_range[0]} to {search_range[1]}")
        
        best_time = float('inf')
        best_lap = None
        best_result = None
        
        for pit_lap in range(search_range[0], search_range[1] + 1):
            strategy = Strategy(
                name=f"1-Stop L{pit_lap}",
                compounds=[compound1, compound2],
                pit_laps=[pit_lap]
            )
            result = self.simulate_strategy(strategy, verbose=False)
            
            if result['total_time'] < best_time:
                best_time = result['total_time']
                best_lap = pit_lap
                best_result = result
        
        print(f"Optimal pit lap: {best_lap}")
        print(f"Total time: {best_time:.3f}s")
        
        return best_result['strategy'], best_result


# Visualization functions

def plot_strategy_comparison(results: List[Dict], save_path: Optional[str] = None) -> None:
    """
    Visualize comparison of multiple strategies.
    
    Args:
        results: List of simulation results
        save_path: Optional path to save figure
    """
    n_strategies = len(results)
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Title
    track_name = results[0]['strategy'].name.split('-')[0] if results else "Race"
    fig.suptitle(f'F1 Race Strategy Analysis', fontsize=16, fontweight='bold')
    
    # 1. Total race time comparison (bar chart)
    ax1 = fig.add_subplot(gs[0, 0])
    strategy_names = [r['strategy'].name for r in results]
    total_times = [r['total_time'] for r in results]
    colors = plt.cm.Set3(np.linspace(0, 1, n_strategies))
    
    bars = ax1.barh(strategy_names, total_times, color=colors)
    ax1.set_xlabel('Total Race Time (s)', fontsize=11)
    ax1.set_title('Total Race Time Comparison', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add time labels
    for i, (bar, time) in enumerate(zip(bars, total_times)):
        time_diff = time - min(total_times)
        label = f"{time:.1f}s (+{time_diff:.1f}s)" if time_diff > 0 else f"{time:.1f}s"
        ax1.text(time + 1, i, label, va='center', fontsize=9)
    
    # 2. Lap time progression
    ax2 = fig.add_subplot(gs[0, 1])
    for i, result in enumerate(results):
        laps = list(range(1, len(result['lap_times']) + 1))
        ax2.plot(laps, result['lap_times'], label=result['strategy'].name, 
                linewidth=2, alpha=0.8, color=colors[i])
    ax2.set_xlabel('Lap', fontsize=11)
    ax2.set_ylabel('Lap Time (s)', fontsize=11)
    ax2.set_title('Lap Time Evolution', fontsize=12, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Cumulative race time
    ax3 = fig.add_subplot(gs[1, 0])
    for i, result in enumerate(results):
        laps = list(range(1, len(result['cumulative_times']) + 1))
        ax3.plot(laps, result['cumulative_times'], label=result['strategy'].name,
                linewidth=2, alpha=0.8, color=colors[i])
    ax3.set_xlabel('Lap', fontsize=11)
    ax3.set_ylabel('Cumulative Time (s)', fontsize=11)
    ax3.set_title('Cumulative Race Time', fontsize=12, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Grip evolution
    ax4 = fig.add_subplot(gs[1, 1])
    for i, result in enumerate(results):
        laps = list(range(1, len(result['grip_levels']) + 1))
        ax4.plot(laps, result['grip_levels'], label=result['strategy'].name,
                linewidth=2, alpha=0.8, color=colors[i])
    ax4.set_xlabel('Lap', fontsize=11)
    ax4.set_ylabel('Grip Multiplier', fontsize=11)
    ax4.set_title('Tire Grip Evolution', fontsize=12, fontweight='bold')
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    # 5. Tire age progression
    ax5 = fig.add_subplot(gs[2, 0])
    for i, result in enumerate(results):
        laps = list(range(1, len(result['tire_ages']) + 1))
        ax5.plot(laps, result['tire_ages'], label=result['strategy'].name,
                linewidth=2, alpha=0.8, color=colors[i])
    ax5.set_xlabel('Lap', fontsize=11)
    ax5.set_ylabel('Tire Age (laps)', fontsize=11)
    ax5.set_title('Tire Age During Race', fontsize=12, fontweight='bold')
    ax5.legend(loc='best', fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    # 6. Strategy summary table
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis('off')
    
    table_data = []
    headers = ['Strategy', 'Compounds', 'Pit Laps', 'Total Time', 'Δ Best']
    
    for result in results:
        time_diff = result['total_time'] - results[0]['total_time']
        table_data.append([
            result['strategy'].name,
            ' → '.join(result['strategy'].compounds),
            ', '.join(map(str, result['strategy'].pit_laps)) if result['strategy'].pit_laps else 'None',
            f"{result['total_time']:.2f}s",
            f"+{time_diff:.2f}s" if time_diff > 0 else "BEST"
        ])
    
    table = ax6.table(cellText=table_data, colLabels=headers, loc='center',
                     cellLoc='left', colWidths=[0.2, 0.2, 0.15, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style rows
    for i in range(1, len(table_data) + 1):
        if i == 1:
            for j in range(len(headers)):
                table[(i, j)].set_facecolor('#C8E6C9')
        else:
            for j in range(len(headers)):
                table[(i, j)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nSaved visualization to {save_path}")
    else:
        plt.show()


def analyze_race(track_name: str = 'Monaco', total_laps: int = 78,
                base_lap_time: float = 72.0, save_path: Optional[str] = None) -> None:
    """
    Complete race strategy analysis with visualization.
    
    Args:
        track_name: Track name
        total_laps: Total race laps
        base_lap_time: Base lap time in seconds
        save_path: Optional path to save figure
    """
    print(f"\n{'='*70}")
    print(f"F1 RACE STRATEGY ANALYSIS - {track_name.upper()}")
    print(f"{'='*70}")
    print(f"Track: {track_name}")
    print(f"Laps: {total_laps}")
    print(f"Base lap time: {base_lap_time:.3f}s")
    
    # Initialize simulator
    simulator = RaceStrategySimulator(
        track_name=track_name,
        total_laps=total_laps,
        base_lap_time=base_lap_time,
        pit_loss=22.0
    )
    
    # Define strategies to test
    strategies = []
    
    # 1-stop strategies
    if total_laps >= 50:
        strategies.extend([
            Strategy(name="1-Stop: Medium-Hard", compounds=['C3', 'C2'], 
                    pit_laps=[total_laps // 2]),
            Strategy(name="1-Stop: Soft-Hard", compounds=['C4', 'C2'], 
                    pit_laps=[total_laps // 3]),
            Strategy(name="1-Stop: Soft-Medium", compounds=['C4', 'C3'], 
                    pit_laps=[total_laps // 3]),
        ])
    else:
        strategies.extend([
            Strategy(name="1-Stop: Medium-Hard", compounds=['C3', 'C2'], 
                    pit_laps=[total_laps // 2]),
            Strategy(name="1-Stop: Soft-Medium", compounds=['C4', 'C3'], 
                    pit_laps=[total_laps // 3]),
        ])
    
    # 2-stop strategies (if race is long enough)
    if total_laps >= 50:
        strategies.extend([
            Strategy(name="2-Stop: Soft-Medium-Medium", 
                    compounds=['C4', 'C3', 'C3'],
                    pit_laps=[total_laps // 4, 2 * total_laps // 3]),
            Strategy(name="2-Stop: Soft-Soft-Medium", 
                    compounds=['C4', 'C4', 'C3'],
                    pit_laps=[total_laps // 5, total_laps // 2]),
            Strategy(name="2-Stop: Medium-Medium-Soft", 
                    compounds=['C3', 'C3', 'C4'],
                    pit_laps=[total_laps // 3, 2 * total_laps // 3]),
        ])
    
    # Run comparison
    results = simulator.compare_strategies(strategies)
    
    # Visualize
    plot_strategy_comparison(results, save_path=save_path)


if __name__ == "__main__":
    """Demo: Race strategy optimization"""
    
    print("="*70)
    print("F1 RACE STRATEGY OPTIMIZER - DEMONSTRATION")
    print("="*70)
    
    # Demo 1: Monaco Grand Prix (78 laps, technical circuit)
    print("\n" + "="*70)
    print("DEMO 1: MONACO GRAND PRIX")
    print("="*70)
    analyze_race(
        track_name='Monaco',
        total_laps=78,
        base_lap_time=72.0,
        save_path='strategy_monaco.png'
    )
    print("\n✓ Created strategy_monaco.png")
    
    # Demo 2: Silverstone Grand Prix (52 laps, high-speed circuit)
    print("\n" + "="*70)
    print("DEMO 2: SILVERSTONE GRAND PRIX")
    print("="*70)
    analyze_race(
        track_name='Silverstone',
        total_laps=52,
        base_lap_time=90.0,
        save_path='strategy_silverstone.png'
    )
    print("\n✓ Created strategy_silverstone.png")
    
    # Demo 3: Optimal pit window search
    print("\n" + "="*70)
    print("DEMO 3: OPTIMAL PIT WINDOW SEARCH")
    print("="*70)
    simulator = RaceStrategySimulator(
        track_name='Spa',
        total_laps=44,
        base_lap_time=106.0
    )
    
    best_strategy, best_result = simulator.find_optimal_1stop(
        compound1='C4',
        compound2='C2',
        search_range=(12, 30)
    )
    
    print(f"\nOptimal Strategy: {best_strategy}")
    print(f"Total Time: {best_result['total_time']:.3f}s")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - strategy_monaco.png")
    print("  - strategy_silverstone.png")
    print("\nThese visualizations show:")
    print("  • Comparative race times for different strategies")
    print("  • Lap time evolution with tire degradation")
    print("  • Grip levels throughout the race")
    print("  • Optimal pit stop windows")
