import os
import sys

# Ensure project root and virtualenv site-packages are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_PACKAGES = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")

if SITE_PACKAGES not in sys.path:
    sys.path.insert(0, SITE_PACKAGES)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn

if __name__ == "__main__":
    print(f"Starting Lakers in 5 server from {BASE_DIR}...")
    uvicorn.run("src.inference.api:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
