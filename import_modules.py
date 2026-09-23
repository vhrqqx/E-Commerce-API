import sys
import os

# Add the src/ directory to the Python path so tests can import app modules directly
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "src"))
