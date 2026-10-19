import sys
from pathlib import Path

p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines()

for i, line in enumerate(lines, 1):
    if 80 <= i <= min(len(lines), 185):
        print(f"{i:04d}: {line!r}")