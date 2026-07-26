import time
import random

DATA_FILE = "ldr_data.txt"

def run_simulator():
    print("Starting LDR Simulator...")
    print(f"Writing simulated data to '{DATA_FILE}'")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Normal LDR value with laser hitting it is high (e.g. 800-950)
            # When the beam is broken, the LDR value drops (e.g. 100-300)
            
            # 10% chance to simulate an intrusion (beam broken)
            is_intrusion = random.random() < 0.1
            
            if is_intrusion:
                ldr_value = random.randint(800, 950)
                status = "INTRUSION"
            else:
                ldr_value = random.randint(100, 300)
                status = "SECURE"
                
            with open(DATA_FILE, "w") as f:
                f.write(f"{ldr_value},{status}")
                
            print(f"Simulated -> LDR: {ldr_value}, Status: {status}")
            time.sleep(1.0) # Update every 1 second
            
    except KeyboardInterrupt:
        print("\nSimulator stopped.")

if __name__ == "__main__":
    run_simulator()
