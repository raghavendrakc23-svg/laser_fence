import streamlit as st
import time
import serial
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import os

# --- Page Configuration ---
st.set_page_config(page_title="Laser Security Monitor", page_icon="🚨", layout="wide")

st.title("🚨 Laser Fencing Security Dashboard")

# --- Component Setup ---
# Use the local farm_component directory for the custom Streamlit component
component_path = os.path.join(os.path.dirname(__file__), "farm_component")
farm_sim = components.declare_component("farm_sim", path=component_path)

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
mode = st.sidebar.radio("Data Source", ["Embedded Simulation", "Simulator (File)", "Serial Port (Hardware)", "Manual Input"])

serial_port = ""
baud_rate = 9600
manual_ldr = 150

if mode == "Serial Port (Hardware)":
    serial_port = st.sidebar.text_input("COM Port", value="COM3")
    baud_rate = st.sidebar.number_input("Baud Rate", value=9600)
elif mode == "Manual Input":
    manual_ldr = st.sidebar.slider("Manual LDR Value (Threshold=500)", min_value=0, max_value=1023, value=150)

DATA_FILE = "ldr_data.txt"

# --- State Initialization ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'LDR Value', 'Status'])

if 'intrusion_count' not in st.session_state:
    st.session_state.intrusion_count = 0

if 'last_status' not in st.session_state:
    st.session_state.last_status = "SECURE"

if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False

if 'current_ldr' not in st.session_state:
    st.session_state.current_ldr = 0

if 'current_status' not in st.session_state:
    st.session_state.current_status = "WAITING..."

# --- Helper Functions ---
def read_simulator():
    try:
        with open(DATA_FILE, "r") as f:
            data = f.read().strip()
            if data:
                parts = data.split(",")
                if len(parts) == 2:
                    return int(parts[0]), parts[1]
    except Exception:
        pass
    return None, None

def read_serial():
    if 'ser' in st.session_state and st.session_state.ser and st.session_state.ser.in_waiting > 0:
        try:
            line = st.session_state.ser.readline().decode('utf-8').strip()
            return line
        except:
            pass
    return None

# --- Controls ---
if not st.session_state.monitoring:
    if st.sidebar.button("Start Monitoring"):
        st.session_state.monitoring = True
        if mode == "Serial Port (Hardware)":
            try:
                st.session_state.ser = serial.Serial(serial_port, baud_rate, timeout=1)
                st.sidebar.success(f"Connected to {serial_port}")
            except Exception as e:
                st.sidebar.error(f"Failed to connect: {e}")
                st.session_state.monitoring = False
        st.rerun()
else:
    if st.sidebar.button("Stop Monitoring"):
        st.session_state.monitoring = False
        if 'ser' in st.session_state:
            st.session_state.ser.close()
            del st.session_state.ser
        st.rerun()

# --- Main Dashboard Layout ---
if mode == "Embedded Simulation":
    st.markdown("### Farm Simulation View")
    # This renders the custom HTML/JS component and captures its returned data
    # It will render immediately but data will only be processed if monitoring is active
    sim_data = farm_sim()
else:
    sim_data = None

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### Current LDR Value")
    ldr_metric = st.empty()
with col2:
    st.markdown("### System Status")
    status_metric = st.empty()
with col3:
    st.markdown("### Total Intrusions")
    count_metric = st.empty()

st.divider()

col_chart, col_log = st.columns([2, 1])
with col_chart:
    st.markdown("### LDR Value History")
    chart_placeholder = st.empty()

with col_log:
    st.markdown("### Intrusion Log")
    log_placeholder = st.empty()

# --- Main Monitoring Logic ---
if st.session_state.monitoring:
    ldr_value = None
    status = None
    
    # 1. Fetch Data
    if mode == "Embedded Simulation":
        if sim_data:
            ldr_value = sim_data.get('ldr_value')
            status = sim_data.get('status')
    elif mode == "Simulator (File)":
        ldr_value, status = read_simulator()
    elif mode == "Serial Port (Hardware)":
        line = read_serial()
        if line:
            if line.startswith("LDR_VALUE:"):
                ldr_value = int(line.split(":")[1])
            elif line.startswith("STATUS:"):
                status = line.split(":")[1]
    elif mode == "Manual Input":
        ldr_value = manual_ldr
        status = "INTRUSION" if manual_ldr > 500 else "SECURE"
                
    # 2. Process Logic
    if ldr_value is not None:
        st.session_state.current_ldr = ldr_value
    if status is not None:
        if status == "INTRUSION" and st.session_state.last_status != "INTRUSION":
            st.session_state.intrusion_count += 1
        
        st.session_state.last_status = status
        st.session_state.current_status = status
        
    # 3. Update History
    now = datetime.now()
    if ldr_value is not None:
        new_row = {'Timestamp': now, 'LDR Value': st.session_state.current_ldr, 'Status': st.session_state.current_status}
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_row])]).tail(50)
    
    # 4. Render UI Updates
    ldr_metric.metric(label="LDR Reading", value=st.session_state.current_ldr)
    
    if st.session_state.current_status == "INTRUSION":
        status_metric.markdown("<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'><h3 style='color: red; margin: 0; text-align: center;'>⚠️ INTRUSION DETECTED ⚠️</h3></div>", unsafe_allow_html=True)
    elif st.session_state.current_status == "SECURE":
        status_metric.markdown("<div style='background-color: #ccffcc; padding: 10px; border-radius: 5px;'><h3 style='color: green; margin: 0; text-align: center;'>✅ SECURE</h3></div>", unsafe_allow_html=True)
    else:
        status_metric.markdown(f"<h3>{st.session_state.current_status}</h3>", unsafe_allow_html=True)
        
    count_metric.metric(label="Intrusions Detected", value=st.session_state.intrusion_count)
    
    # Update Line Chart
    if not st.session_state.history.empty:
        chart_data = st.session_state.history.set_index('Timestamp')['LDR Value']
        chart_placeholder.line_chart(chart_data)
        
        # Update Intrusion Logs Table
        intrusions = st.session_state.history[st.session_state.history['Status'] == 'INTRUSION']
        if not intrusions.empty:
            log_placeholder.dataframe(
                intrusions[['Timestamp', 'LDR Value']].sort_values(by="Timestamp", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            log_placeholder.info("No intrusions recorded yet.")
    
    # 5. Loop Control
    # If we are embedded, the component pushes updates automatically which trigger reruns.
    # Otherwise, we sleep and rerun manually.
    if mode != "Embedded Simulation":
        time.sleep(1.0)
        st.rerun()
