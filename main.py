import os
import sys

# Ensure frontend/backend are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend.ui import demo

if __name__ == "__main__":
    print("Starting Math Adventure on http://0.0.0.0:3000")
    demo.launch(server_name="0.0.0.0", server_port=3000)
