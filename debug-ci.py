import subprocess
import sys

result = subprocess.run(
    ["uv", "run", "ruff", "format", "--check", ".", "--diff"], capture_output=True, text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
sys.exit(0)
