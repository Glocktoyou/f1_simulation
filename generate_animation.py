"""
F1 Lap Animation Generator (GIF only)
Creates an animated GIF of simulated lap with telemetry overlay

Dependencies:  pip install matplotlib numpy pandas pillow
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import pandas as pd
from f1_simulation import F1Vehicle, create_monza_style_track, simulate_lap


def create_track_from_segments(track):
    """
    Create track x,y coordinates from track segments
    """
    x, y = [0.0], [0.0]
    heading = 0.0
    distances = [0.0]
    current_dist = 0.0
    
    step_size = 5  # meters per point
    
    for seg in track.segments:
        length = seg['length']
        radius = seg['radius']
        num_steps = max(1, int(length / step_size))
        step = length / num_steps
        
        for _ in range(num_steps):
            if radius == np.inf:
                # Straight
                dx = step * np.cos(heading)
                dy = step * np.sin(heading)
            else:
                # Curve
                arc_angle = step / abs(radius)
                if radius > 0:
                    heading += arc_angle / 2
                    dx = step * np.cos(heading)
                    dy = step * np.sin(heading)
                    heading += arc_angle / 2
                else: 
                    heading -= arc_angle / 2
                    dx = step * np.cos(heading)
                    dy = step * np.sin(heading)
                    heading -= arc_angle / 2
            
            x.append(x[-1] + dx)
            y.append(y[-1] + dy)
            current_dist += step
            distances.append(current_dist)
    
    return np.array(x), np.array(y), np.array(distances)


def animate_lap(track, telemetry, lap_time, output_file='lap_animation.gif', fps=20):
    """
    Create animated lap visualization with telemetry overlay (GIF)
    
    Args:
        track:  Track instance
        telemetry: DataFrame from simulate_lap()
        lap_time: Total lap time in seconds
        output_file: Output GIF filename
        fps: Frames per second
    """
    
    print("Generating track coordinates...")
    track_x, track_y, track_distances = create_track_from_segments(track)
    
    # Interpolate car position from telemetry
    from scipy.interpolate import interp1d
    
    x_interp = interp1d(track_distances, track_x, bounds_error=False, fill_value='extrapolate')
    y_interp = interp1d(track_distances, track_y, bounds_error=False, fill_value='extrapolate')
    
    # Create figure with dark theme
    fig = plt.figure(figsize=(14, 9), facecolor='#1a1a2e')
    
    # Track map (left side)
    ax_track = fig.add_axes([0.02, 0.25, 0.50, 0.70])
    ax_track.set_facecolor('#1a1a2e')
    
    # Speed trace (top right)
    ax_speed = fig.add_axes([0.58, 0.55, 0.38, 0.35])
    ax_speed.set_facecolor('#16213e')
    
    # G-Force display (bottom right)
    ax_gforce = fig.add_axes([0.58, 0.25, 0.25, 0.25])
    ax_gforce.set_facecolor('#16213e')
    
    # Telemetry panel (bottom)
    ax_info = fig.add_axes([0.02, 0.02, 0.94, 0.18])
    ax_info.set_facecolor('#0f0f23')
    ax_info.axis('off')
    
    # Plot track outline
    ax_track.plot(track_x, track_y, 'w-', linewidth=12, alpha=0.2)
    ax_track.plot(track_x, track_y, '#555555', linewidth=6)
    ax_track.set_aspect('equal')
    ax_track.axis('off')
    ax_track.set_title(f'{track.name}', color='white', fontsize=16, fontweight='bold', pad=10)
    
    # Start/Finish marker
    ax_track.plot(track_x[0], track_y[0], 's', color='white', markersize=10, label='Start/Finish')
    
    # Initialize car marker
    car_marker, = ax_track.plot([], [], 'o', color='#e94560', markersize=14, zorder=10)
    trail_line, = ax_track.plot([], [], '-', color='#e94560', linewidth=2, alpha=0.5)
    
    # Speed trace setup
    ax_speed.set_xlim(0, track.total_length)
    ax_speed.set_ylim(0, telemetry['velocity'].max() * 1.1)
    ax_speed.set_xlabel('Distance (m)', color='white', fontsize=9)
    ax_speed.set_ylabel('Speed (km/h)', color='white', fontsize=9)
    ax_speed.set_title('SPEED TRACE', color='#00d4ff', fontsize=11, fontweight='bold')
    ax_speed.tick_params(colors='white', labelsize=8)
    ax_speed.grid(True, alpha=0.2, color='white')
    for spine in ax_speed.spines.values():
        spine.set_color('#444444')
    
    # Plot full speed trace faded
    ax_speed.plot(telemetry['distance'], telemetry['velocity'], 'white', linewidth=1, alpha=0.2)
    speed_line, = ax_speed.plot([], [], 'cyan', linewidth=2)
    speed_marker, = ax_speed.plot([], [], 'o', color='#e94560', markersize=8)
    
    # G-Force gauge setup
    ax_gforce.set_xlim(-5, 5)
    ax_gforce.set_ylim(-8, 3)
    ax_gforce.set_xlabel('Lateral G', color='white', fontsize=9)
    ax_gforce.set_ylabel('Long G', color='white', fontsize=9)
    ax_gforce.set_title('G-FORCE', color='#e94560', fontsize=11, fontweight='bold')
    ax_gforce.tick_params(colors='white', labelsize=8)
    ax_gforce.axhline(0, color='white', alpha=0.3, linewidth=0.5)
    ax_gforce.axvline(0, color='white', alpha=0.3, linewidth=0.5)
    ax_gforce.set_aspect('equal')
    for spine in ax_gforce.spines.values():
        spine.set_color('#444444')
    
    # G-force reference circles
    for r in [2, 4, 6]: 
        circle = plt.Circle((0, 0), r, fill=False, color='white', alpha=0.15, linestyle='--')
        ax_gforce.add_patch(circle)
    
    g_marker, = ax_gforce.plot([], [], 'o', color='#e94560', markersize=10)
    g_trail, = ax_gforce.plot([], [], '-', color='#e94560', alpha=0.4, linewidth=1)
    
    # Text elements for telemetry display
    speed_text = ax_info.text(0.08, 0.65, '', color='#00d4ff', fontsize=32,
                               fontweight='bold', transform=ax_info.transAxes,
                               family='monospace')
    ax_info.text(0.08, 0.25, 'SPEED (km/h)', color='#888888', fontsize=10,
                 transform=ax_info.transAxes)
    
    throttle_text = ax_info.text(0.28, 0.65, '', color='#00ff88', fontsize=32,
                                  fontweight='bold', transform=ax_info.transAxes,
                                  family='monospace')
    ax_info.text(0.28, 0.25, 'THROTTLE', color='#888888', fontsize=10,
                 transform=ax_info.transAxes)
    
    brake_text = ax_info.text(0.48, 0.65, '', color='#ff4466', fontsize=32,
                               fontweight='bold', transform=ax_info.transAxes,
                               family='monospace')
    ax_info.text(0.48, 0.25, 'BRAKE', color='#888888', fontsize=10,
                 transform=ax_info.transAxes)
    
    time_text = ax_info.text(0.68, 0.65, '', color='#ffcc00', fontsize=32,
                              fontweight='bold', transform=ax_info.transAxes,
                              family='monospace')
    ax_info.text(0.68, 0.25, 'LAP TIME', color='#888888', fontsize=10,
                 transform=ax_info.transAxes)
    
    gear_text = ax_info.text(0.88, 0.65, '', color='white', fontsize=32,
                              fontweight='bold', transform=ax_info.transAxes,
                              family='monospace')
    ax_info.text(0.88, 0.25, 'GEAR', color='#888888', fontsize=10,
                 transform=ax_info.transAxes)
    
    # Trail history storage
    trail_x, trail_y = [], []
    g_trail_x, g_trail_y = [], []
    
    num_frames = len(telemetry)
    
    def init():
        car_marker.set_data([], [])
        trail_line.set_data([], [])
        speed_line.set_data([], [])
        speed_marker.set_data([], [])
        g_marker.set_data([], [])
        g_trail.set_data([], [])
        return car_marker, trail_line, speed_line, speed_marker, g_marker, g_trail
    
    def animate(frame):
        nonlocal trail_x, trail_y, g_trail_x, g_trail_y
        
        # Get current telemetry values
        idx = min(frame, len(telemetry) - 1)
        row = telemetry.iloc[idx]
        
        distance = row['distance']
        speed = row['velocity']
        throttle = row['throttle']
        brake = row['brake']
        lat_g = row['lateral_g']
        long_g = row['longitudinal_g']
        current_time = row['time']
        
        # Calculate car position on track
        car_x = float(x_interp(distance))
        car_y = float(y_interp(distance))
        
        # Update car trail
        trail_x.append(car_x)
        trail_y.append(car_y)
        if len(trail_x) > 80:
            trail_x = trail_x[-80:]
            trail_y = trail_y[-80:]
        
        # Update car position
        car_marker.set_data([car_x], [car_y])
        trail_line.set_data(trail_x, trail_y)
        
        # Update speed trace
        speed_data = telemetry.iloc[:idx+1]
        speed_line.set_data(speed_data['distance'], speed_data['velocity'])
        speed_marker.set_data([distance], [speed])
        
        # Update G-force display
        g_trail_x.append(lat_g)
        g_trail_y.append(long_g)
        if len(g_trail_x) > 25:
            g_trail_x = g_trail_x[-25:]
            g_trail_y = g_trail_y[-25:]
        
        g_marker.set_data([lat_g], [long_g])
        g_trail.set_data(g_trail_x, g_trail_y)
        
        # Update telemetry text
        speed_text.set_text(f'{speed:.0f}')
        throttle_text.set_text(f'{throttle*100:.0f}%')
        brake_text.set_text(f'{brake*100:.0f}%')
        time_text.set_text(f'{current_time:.2f}s')
        
        # Estimate gear from speed (simplified)
        gear = min(8, max(1, int(speed / 45) + 1))
        gear_text.set_text(f'{gear}')
        
        return car_marker, trail_line, speed_line, speed_marker, g_marker, g_trail
    
    print(f"Creating animation with {num_frames} frames at {fps} FPS...")
    print("This may take a minute...")
    
    # Create animation
    anim = FuncAnimation(
        fig, animate, init_func=init, 
        frames=num_frames, interval=1000/fps, blit=False
    )
    
    # Save as GIF
    print(f"Saving GIF to {output_file}...")
    writer = PillowWriter(fps=fps)
    anim.save(output_file, writer=writer, dpi=100)
    
    print(f"✓ Animation saved:  {output_file}")
    plt.close()
    
    return output_file


def main():
    """Generate lap animation"""
    
    print("=" * 60)
    print("🏎️  F1 LAP ANIMATION GENERATOR")
    print("=" * 60)
    
    # Create vehicle and track
    vehicle = F1Vehicle()
    track = create_monza_style_track()
    
    print(f"\nTrack:  {track.name}")
    print(f"Length: {track.total_length:.0f}m")
    
    print("\nSimulating lap...")
    telemetry, lap_time = simulate_lap(vehicle, track)
    
    print(f"Lap time: {lap_time:.3f}s")
    print(f"Telemetry points: {len(telemetry)}")
    
    # Generate animation - save to images folder
    output_file = animate_lap(
        track=track,
        telemetry=telemetry,
        lap_time=lap_time,
        output_file='images/lap_animation.gif',
        fps=20
    )
    
    print("\n" + "=" * 60)
    print("✅ ANIMATION COMPLETE!")
    print("=" * 60)
    print(f"\nOutput:  {output_file}")
    print("\nAdd to your README:")
    print("  ![Lap Animation](images/lap_animation.gif)")


if __name__ == "__main__": 
    main()
