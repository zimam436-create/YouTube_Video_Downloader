from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
py_compile.compile(str(ROOT / "ytd.py"), doraise=True)
print("YTD syntax check passed.")
