import asyncio
import json
import os
import serial
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Dict

app = FastAPI(title="Laser Fencing Dashboard API")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

DATA_FILE = "ldr_data.txt"

# State
class DashboardState:
    def __init__(self):
        self.mode = "Simulator (File)" # Embedded Simulation, Simulator (File), Serial Port (Hardware), Manual Input
        self.serial_port = "COM3"
        self.baud_rate = 9600
        self.manual_ldr = 150
        
        self.current_ldr = 0
        self.current_status = "WAITING..."
        self.last_status = "SECURE"
        self.intrusion_count = 0
        
        self.history: List[Dict] = []
        
        self.ser = None
        
    def add_history(self, ldr, status):
        now = datetime.now().strftime("%H:%M:%S")
        self.history.append({"time": now, "ldr": ldr, "status": status})
        if len(self.history) > 50:
            self.history.pop(0)

state = DashboardState()
clients = []

async def broadcast_state():
    if not clients:
        return
        
    data = {
        "ldr": state.current_ldr,
        "status": state.current_status,
        "intrusion_count": state.intrusion_count,
        "history": state.history,
        "mode": state.mode
    }
    
    dead_clients = []
    for client in clients:
        try:
            await client.send_json(data)
        except:
            dead_clients.append(client)
            
    for client in dead_clients:
        if client in clients:
            clients.remove(client)

def process_reading(ldr_value, status):
    if ldr_value is not None:
        state.current_ldr = ldr_value
    if status is not None:
        if status == "INTRUSION" and state.last_status != "INTRUSION":
            state.intrusion_count += 1
        state.last_status = status
        state.current_status = status
        
    state.add_history(state.current_ldr, state.current_status)

async def data_loop():
    while True:
        try:
            if state.mode == "Simulator (File)":
                try:
                    with open(DATA_FILE, "r") as f:
                        data = f.read().strip()
                        if data:
                            parts = data.split(",")
                            if len(parts) == 2:
                                process_reading(int(parts[0]), parts[1])
                except Exception:
                    pass
                    
            elif state.mode == "Serial Port (Hardware)":
                if state.ser and state.ser.in_waiting > 0:
                    try:
                        line = state.ser.readline().decode('utf-8').strip()
                        ldr_val = None
                        stat = None
                        if line.startswith("LDR_VALUE:"):
                            ldr_val = int(line.split(":")[1])
                        elif line.startswith("STATUS:"):
                            stat = line.split(":")[1]
                            
                        # If we read parts on separate lines, we need to process them as they come.
                        if ldr_val is not None:
                            state.current_ldr = ldr_val
                        if stat is not None:
                            process_reading(state.current_ldr, stat)
                    except:
                        pass
                        
            elif state.mode == "Manual Input":
                # Manual input is pushed by client, we just process it continuously or rely on client push.
                process_reading(state.manual_ldr, "INTRUSION" if state.manual_ldr > 500 else "SECURE")
                
            elif state.mode == "Embedded Simulation":
                # Embedded simulation data is pushed via websocket by the frontend.
                pass 
                
            if clients:
                await broadcast_state()
                
        except Exception as e:
            print(f"Error in data loop: {e}")
            
        await asyncio.sleep(0.5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(data_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    # Send initial state
    await websocket.send_json({
        "ldr": state.current_ldr,
        "status": state.current_status,
        "intrusion_count": state.intrusion_count,
        "history": state.history,
        "mode": state.mode
    })
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            action = msg.get("action")
            
            if action == "set_mode":
                new_mode = msg.get("mode")
                state.mode = new_mode
                
                if state.ser:
                    state.ser.close()
                    state.ser = None
                    
                if new_mode == "Serial Port (Hardware)":
                    port = msg.get("serial_port", "COM3")
                    baud = int(msg.get("baud_rate", 9600))
                    try:
                        state.ser = serial.Serial(port, baud, timeout=1)
                    except Exception as e:
                        print(f"Serial Error: {e}")
                        
                await broadcast_state()
            
            elif action == "manual_input":
                if state.mode == "Manual Input":
                    state.manual_ldr = int(msg.get("ldr_value", 150))
                    
            elif action == "embedded_input":
                if state.mode == "Embedded Simulation":
                    ldr = msg.get("ldr_value")
                    status = msg.get("status")
                    process_reading(ldr, status)
                    await broadcast_state()
                    
            elif action == "reset_count":
                state.intrusion_count = 0
                await broadcast_state()
                
    except WebSocketDisconnect:
        clients.remove(websocket)
