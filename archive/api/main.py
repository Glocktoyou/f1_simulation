"""
F1 Simulator REST API
FastAPI backend that connects the web interface to the Python physics engine
"""

import sys
import os

# Add src directory to path (absolute)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from fastapi import FastAPI, HTTPException
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    # Import only for type checking to satisfy linters/static analyzers
    from f1_realtrack_tiremodel import RealF1Track

# Heavy simulation modules are imported lazily inside handlers to avoid
# long import-time work that can break platform startup.

app = FastAPI(
    title="F1 Vehicle Dynamics Simulator API",
    description="REST API for F1 lap time simulation with adjustable vehicle parameters",
    version="1.0.0"
)

# Logger for startup/runtime diagnostics
logger = logging.getLogger("f1_simulation")
logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def _startup_event():
    logger.info("f1_simulation: startup event fired")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VehicleParams(BaseModel):
    """Vehicle parameters that can be adjusted via the web interface"""
    power: Optional[float] = 1000  # HP (will be converted to W)
    downforce: Optional[float] = 100  # Percentage (100 = baseline)
    tire: Optional[float] = 100  # Tire grip percentage
    mass: Optional[float] = 798  # kg
    drag: Optional[float] = 100  # Drag percentage


class SimulationRequest(BaseModel):
    """Request body for simulation endpoint"""
    track: str  # "silverstone", "monaco", or "spa"
    vehicle_params: VehicleParams


class SegmentResult(BaseModel):
    """Result for a single track segment"""
    name: str
    type: str
    length: float
    sim_time: float
    avg_speed: float
    max_speed: float
    min_speed: float


class SimulationResponse(BaseModel):
    """Response from simulation endpoint"""
    track_name: str
    track_length: float
    record_time: float
    record_holder: str
    sim_time: float
    difference: float
    error_percent: float
    max_speed: float
    avg_speed: float
    segments: List[SegmentResult]
    telemetry: Dict[str, List[float]]


def apply_params_to_vehicle(vehicle, params: VehicleParams):
    """Apply user parameters to vehicle model"""
    # Power: convert HP to Watts (1 HP = 746 W)
    vehicle.max_power = params.power * 746
    
    # Mass: direct value in kg
    vehicle.mass = params.mass
    
    # Downforce: scale Cl values by percentage
    downforce_scale = params.downforce / 100
    vehicle.Cl_front = 1.8 * downforce_scale
    vehicle.Cl_rear = 1.7 * downforce_scale
    
    # Tire grip: scale mu_peak by percentage
    vehicle.tire_mu_peak = 1.8 * (params.tire / 100)
    
    # Drag: scale Cd by percentage
    vehicle.Cd = 0.70 * (params.drag / 100)
    
    return vehicle


def get_track(track_name: str):
    """Get track object by name"""
    # Lazy import to avoid expensive module initialization at import time
    from f1_realtrack_tiremodel import create_silverstone, create_monaco, create_spa

    tracks = {
        "silverstone": create_silverstone,
        "monaco": create_monaco,
        "spa": create_spa
    }

    if track_name.lower() not in tracks:
        raise HTTPException(status_code=400, detail=f"Unknown track: {track_name}")

    return tracks[track_name.lower()]()


def analyze_segments(telemetry_df, track: RealF1Track) -> List[SegmentResult]:
    """Analyze performance for each track segment"""
    segments_results = []
    
    for segment in track.segments:
        # Filter telemetry for this segment
        mask = (telemetry_df['distance'] >= segment['start']) & \
               (telemetry_df['distance'] < segment['end'])
        segment_data = telemetry_df[mask]
        
        if len(segment_data) > 0:
            # Calculate segment time
            if len(segment_data) > 1:
                seg_time = segment_data['time'].iloc[-1] - segment_data['time'].iloc[0]
            else:
                seg_time = 0.0
            
            segments_results.append(SegmentResult(
                name=segment['name'],
                type=segment['type'],
                length=segment['length'],
                sim_time=float(seg_time),
                avg_speed=float(segment_data['velocity'].mean()),
                max_speed=float(segment_data['velocity'].max()),
                min_speed=float(segment_data['velocity'].min())
            ))
    
    return segments_results


@app.get("/")
async def root():
    """Serve the main page or redirect to the web UI when available."""
    # If the web UI exists in the archive/web folder, redirect to `/app`.
    web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
    index_path = os.path.join(web_dir, 'index.html')
    if os.path.exists(index_path):
        # Redirect to deployed Render app by default
        return RedirectResponse(url="https://f1-simulation-1.onrender.com/app")

    return {
        "name": "F1 Vehicle Dynamics Simulator API",
        "version": "1.0.0",
        "endpoints": {
            "GET /tracks": "List available tracks",
            "POST /simulate": "Run simulation with custom parameters",
            "GET /defaults": "Get default vehicle parameters"
        }
    }


@app.get("/tracks")
async def get_tracks():
    """Get list of available tracks with their details"""
    return {
        "tracks": [
            {
                "id": "silverstone",
                "name": "Silverstone Circuit",
                "country": "UK",
                "flag": "🇬🇧",
                "length": 5891,
                "record_time": 87.097,
                "record_holder": "Lewis Hamilton (Mercedes)",
                "year": 2020,
                "type": "High-speed"
            },
            {
                "id": "monaco",
                "name": "Circuit de Monaco",
                "country": "Monaco",
                "flag": "🇲🇨",
                "length": 3337,
                "record_time": 70.166,
                "record_holder": "Lewis Hamilton (Mercedes)",
                "year": 2019,
                "type": "Street Circuit"
            },
            {
                "id": "spa",
                "name": "Spa-Francorchamps",
                "country": "Belgium",
                "flag": "🇧🇪",
                "length": 7004,
                "record_time": 106.286,
                "record_holder": "Valtteri Bottas (Mercedes)",
                "year": 2018,
                "type": "Mixed Speed"
            }
        ]
    }


@app.get("/defaults")
async def get_defaults():
    """Get default vehicle parameters"""
    return {
        "power": 1000,  # HP
        "downforce": 100,  # %
        "tire": 100,  # %
        "mass": 798,  # kg
        "drag": 100  # %
    }


@app.get("/health")
async def health():
    """Lightweight health check for deployment platforms."""
    return {"status": "ok"}


@app.post("/simulate", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    """Run simulation with custom vehicle parameters"""
    try:
        # Lazy-import heavy modules to avoid import-time work
        from f1_simulation import F1Vehicle
        from f1_realtrack_tiremodel import simulate_real_track, validate_against_real_f1

        # Create vehicle and apply parameters
        vehicle = F1Vehicle()
        vehicle = apply_params_to_vehicle(vehicle, request.vehicle_params)

        # Get track
        track = get_track(request.track)

        # Run simulation
        telemetry_df, lap_time = simulate_real_track(vehicle, track)

        # Validate against real F1 time
        validation = validate_against_real_f1(lap_time, track)
        
        # Analyze segments
        segments = analyze_segments(telemetry_df, track)
        
        # Prepare telemetry data for response (downsample for transfer)
        # Take every nth point to reduce data size
        sample_rate = max(1, len(telemetry_df) // 200)
        sampled = telemetry_df.iloc[::sample_rate]
        
        telemetry_data = {
            "time": sampled['time'].tolist(),
            "distance": sampled['distance'].tolist(),
            "velocity": sampled['velocity'].tolist(),
            "drs_active": sampled['drs_active'].tolist() if 'drs_active' in sampled else []
        }
        
        return SimulationResponse(
            track_name=track.name,
            track_length=track.length,
            record_time=track.record_lap_time,
            record_holder=f"{track.record_holder} ({track.year})",
            sim_time=lap_time,
            difference=validation['difference'],
            error_percent=validation['error_percent'],
            max_speed=float(telemetry_df['velocity'].max()),
            avg_speed=float(telemetry_df['velocity'].mean()),
            segments=segments,
            telemetry=telemetry_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files (web frontend)
web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")
    
    @app.get("/app")
    async def serve_app():
        """Serve the web application"""
        return FileResponse(os.path.join(web_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("Starting F1 Simulator API...")
    print("Open https://f1-simulation-1.onrender.com/app in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
