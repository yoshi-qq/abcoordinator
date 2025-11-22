import sys
from pathlib import Path
import faulthandler
faulthandler.enable()

def main() -> None:
	project_root = Path(__file__).parent
	if str(project_root) not in sys.path:
		sys.path.insert(0, str(project_root))
	from frontend.entryPoint import entryPointFunc
	entryPointFunc()

if __name__ == "__main__":
	main()