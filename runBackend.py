import sys
from pathlib import Path
from packages.backend.server import app
from packages.shared.sharedConstants import WebServerHost, WebServerPort

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print(f"Server running at http://{WebServerHost}:{WebServerPort}")
    print("Press CTRL+C to quit\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
