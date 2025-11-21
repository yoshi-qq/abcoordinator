import sys
from pathlib import Path
from packages.backend.server import app

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print(f"Starting Flask server from: {project_root}")
    print(f"Python path includes: {project_root}")
    print("Server running at http://localhost:5000")
    print("Press CTRL+C to quit\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
