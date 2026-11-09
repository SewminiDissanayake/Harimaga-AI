# PythonAnywhere WSGI file for HariMaga AI
# ------------------------------------------
# Copy ALL of this into the WSGI configuration file on the PythonAnywhere
# "Web" tab (replace everything that is there).
import os
import sys

PROJECT = os.path.expanduser("~/Harimaga-AI")

sys.path.insert(0, PROJECT)
sys.path.insert(0, os.path.join(PROJECT, "webapp", "backend"))

# PythonAnywhere sits behind a proxy: use the real visitor IP for rate limiting
os.environ["HARIMAGA_BEHIND_PROXY"] = "1"

from app import app as application  # noqa: E402
