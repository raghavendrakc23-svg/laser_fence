# Laser Fencing Security Dashboard

A real-time security dashboard for monitoring a laser-based farm perimeter fencing system. 
This project features a high-performance **FastAPI** backend with a lag-free **Vanilla HTML/JS/CSS WebSockets** frontend, alongside legacy **Streamlit** and **Pygame** simulation modules.

## Features
- **Real-Time WebSockets**: Instant updates from hardware serial ports or simulators without page reloads.
- **Embedded Simulation**: An interactive HTML5 Canvas-based farm simulation built directly into the dashboard. Test intrusion logic by dragging animals into the laser fence!
- **Data Source Modes**: 
  - **Serial Port (Hardware)**: Reads from physical Arduino sensors (e.g., LDRs) connected via USB.
  - **Simulator (File)**: Reads synthetic data from a background Python script (`simulator.py`).
  - **Manual Input**: Use a slider to test LDR threshold values on the fly.
  - **Embedded Simulation**: HTML5 canvas simulation.
- **Premium UI**: Sleek dark mode design with glassmorphism, micro-animations, and Chart.js graphs.

## Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the primary FastAPI dashboard:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. Open your browser and navigate to `http://localhost:8000`.

## Modules Included

- `main.py` and `static/`: The new high-performance FastAPI/WebSockets dashboard.
- `simulator.py`: A lightweight script that simulates background LDR data to `ldr_data.txt`.
- `app.py`: A legacy Streamlit implementation of the dashboard (run with `streamlit run app.py`).
- `farm_simulator.py`: A legacy Pygame-based desktop simulation of the farm.
- `farm_component/`: Legacy Streamlit custom HTML component files.
