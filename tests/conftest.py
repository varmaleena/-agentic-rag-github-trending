import sys
import os

# Add backend root directory to sys.path so tests can import app modules cleanly
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
