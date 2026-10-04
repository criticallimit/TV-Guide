"""Executable entry point for the TV Guide add-on."""
import sys
from pathlib import Path

# Also support tools loading this entry point by file path.
root = str(Path(__file__).resolve().parent)
if root not in sys.path:
    sys.path.insert(0, root)

from tvguide import services as backend  # noqa: E402

if __name__ == "__main__":
    backend.main()
