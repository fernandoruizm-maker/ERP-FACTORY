"""Run only from the immutable checkout of the PRIVATE reviewer repository."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reviewer.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
