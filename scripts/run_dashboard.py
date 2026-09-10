"""
CLI Launcher for the Lakers in 5 Streamlit Monitoring Dashboard.
"""

import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "src", "dashboard", "app.py")
    
    cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]
    print(f"Launching Streamlit Dashboard from {dashboard_path}...")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")

if __name__ == "__main__":
    main()
