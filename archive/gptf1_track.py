# UPDATED PORTFOLIO VERSION (MULTI-TRACK)
# Tracks: Spa, Monaco, Silverstone
# Portfolio-grade physics with explicit assumptions

import numpy as np
import pandas as pd
from datetime import datetime

# ===================== VEHICLE MODEL =====================
class F1Vehicle:
    def __init__(self, fuel_load=10):
        self.mass_empty = 798
        self.fuel_load = fuel_load
        self.fuel_consumption_rate = 1.8
        self.g = 9.81

        # Aero (portfolio tuned)
        self.Cd = 0.68
        self.Cd_drs = 0.52
        self.Cl_total = 5.0
        self.frontal_area = 1.5
        self.air_density = 1.225
        self.aero_front_frac = 0.45

        # Power
        self.max_power = 746_000

        # DRS
        self.drs_min_speed = 80

    def get_current_mass(self, distance_km):
        fuel_burned = distance_km * self.fuel_consumption_rate
        return self.mass_empty + max(0, self.fuel_load - fuel_burned)

    def can_use_drs(self, segment_type, speed_kmh):
        return segment_type == 'straight' and speed_kmh >= self.drs_min_speed

    def aero_forces(self, v, drs=False):
        Cd = self.Cd_drs if drs else self.Cd
        drag = 0.5 * self.air_density * Cd * self.frontal_area * v**2
        downforce = 0.5 * self.air_density * self.Cl_total * self.frontal_area * v**2
        return drag, downforce, downforce * self.aero_front_frac, downforce * (1 - self.aero_front_frac)

    def tire_mu(self, Fz):
        mu0, k = 2.0, 0.00015
        return max(1.2, mu0 - k * (Fz / 1000))

    def corner_speed(self, radius, df, mass):
        if radius == np.inf:
            return np.inf
        Fz = mass * self.g + df
        mu = self.tire_mu(Fz)
        return np.sqrt((mu * Fz / mass) * radius)


# ===================== TRACK MODEL =====================
class RealF1Track:
    def __init__(self, name, length, record):
        self.name = name
        self.length = length
        self.record = record
        self.segments = []
        self.total_length = 0

    def add(self, name, length, radius=np.inf, seg_type='corner', aero_limited=False):
        self.segments.append({
            'name': name,
            'start': self.total_length,
            'end': self.total_length + length,
            'length': length,
            'radius': radius,
            'type': seg_type,
            'aero_limited': aero_limited
        })
        self.total_length += length

    def segment_at(self, d):
        for s in self.segments:
            if s['start'] <= d < s['end']:
                return s
        return self.segments[-1]


# ===================== TRACK DEFINITIONS =====================

def create_spa():
    t = RealF1Track('Spa-Francorchamps', 7004, 106.286)
    t.add('La Source', 120, 30)
    t.add('Eau Rouge', 180, 800, aero_limited=True)
    t.add('Raidillon', 140, 600, aero_limited=True)
    t.add('Kemmel', 800, seg_type='straight')
    t.add('Les Combes', 160, 50, 'chicane')
    t.add('Malmedy', 200, 120)
    t.add('Rivage', 220, 35)
    t.add('Pouhon', 200, 400, aero_limited=True)
    t.add('Campus', 450, seg_type='straight')
    t.add('Stavelot', 160, 100)
    t.add('Blanchimont', 300, 500, aero_limited=True)
    t.add('Bus Stop', 150, 40, 'chicane')
    t.add('Start Straight', 724, seg_type='straight')
    return t


def create_monaco():
    t = RealF1Track('Monaco', 3337, 70.166)
    t.add('Sainte Devote', 100, 25)
    t.add('Beau Rivage', 250, seg_type='straight')
    t.add('Massenet', 90, 40)
    t.add('Casino', 110, 35)
    t.add('Mirabeau', 80, 18)
    t.add('Hairpin', 120, 15)
    t.add('Portier', 140, 45)
    t.add('Tunnel', 400, seg_type='straight')
    t.add('Nouvelle Chicane', 100, 25, 'chicane')
    t.add('Tabac', 120, 45)
    t.add('Swimming Pool', 180, 35, 'chicane')
    t.add('Rascasse', 140, 20)
    t.add('Anthony Noghes', 110, 28)
    t.add('Start Straight', 597, seg_type='straight')
    return t


def create_silverstone():
    t = RealF1Track('Silverstone', 5891, 87.097)
    t.add('Abbey', 250, 300, aero_limited=True)
    t.add('Farm', 400, seg_type='straight')
    t.add('Village', 80, 35)
    t.add('Loop', 150, 60)
    t.add('Aintree', 120, 80)
    t.add('Wellington', 650, seg_type='straight')
    t.add('Brooklands', 120, 120)
    t.add('Luffield', 140, 45)
    t.add('Woodcote', 180, 200)
    t.add('Copse', 160, 350, aero_limited=True)
    t.add('Maggots', 140, 500, aero_limited=True)
    t.add('Becketts', 180, 400, aero_limited=True)
    t.add('Chapel', 120, 300, aero_limited=True)
    t.add('Hangar', 1100, seg_type='straight')
    t.add('Stowe', 140, 90)
    t.add('Vale', 180, 50)
    t.add('Club', 160, 70)
    t.add('Start Straight', 301, seg_type='straight')
    return t


# ===================== SIMULATION =====================

def simulate(vehicle, track, dt=0.02):
    t = d = v = 0
    rows = []

    while d < track.total_length:
        seg = track.segment_at(d)
        mass = vehicle.get_current_mass(d / 1000)
        drs = vehicle.can_use_drs(seg['type'], v * 3.6)
        drag, df, df_f, df_r = vehicle.aero_forces(v, drs)

        if seg['aero_limited']:
            v_target = np.inf
        else:
            v_target = vehicle.corner_speed(seg['radius'], df, mass)

                # --- Robust driver controller (fixes NaN / inf issues) ---
        if not np.isfinite(v_target):
            throttle = 1.0
            brake = 0.0
        else:
            err = v_target - v
            denom = max(v_target, 10.0)  # prevent divide-by-zero / tiny numbers
            throttle = np.clip(err / denom, 0.0, 1.0)
            brake = np.clip(-err / denom, 0.0, 1.0)

        engine = min(
            vehicle.max_power / max(v, 5.0),
            vehicle.tire_mu(mass * vehicle.g + df_r) * (mass * vehicle.g + df_r)
        )
        brake_force = brake * vehicle.tire_mu(mass * vehicle.g + df) * (mass * vehicle.g + df)

        a = (throttle * engine - brake_force - drag) / mass
        v = max(0.0, v + a * dt)
        d += v * dt
        t += dt

        rows.append([track.name, t, d, v * 3.6, seg['name']])([track.name, t, d, v * 3.6, seg['name']])

    return pd.DataFrame(rows, columns=['track', 'time', 'distance', 'speed_kmh', 'segment']), t


# ===================== MAIN =====================
if __name__ == '__main__':
    car = F1Vehicle()
    tracks = [create_spa(), create_monaco(), create_silverstone()]
    all_data = []

    print('\nPORTFOLIO SIMULATION RESULTS')
    print('-' * 50)

    for trk in tracks:
        df, lap = simulate(car, trk)
        all_data.append(df)
        print(f"{trk.name:15s}  Sim: {lap:6.2f}s  Real: {trk.record:6.2f}s  Error: {(lap - trk.record)/trk.record*100:+.2f}%")

    telemetry = pd.concat(all_data, ignore_index=True)
    telemetry.to_csv('telemetry_all_tracks.csv', index=False)
    print('\n✓ Telemetry saved: telemetry_all_tracks.csv')
