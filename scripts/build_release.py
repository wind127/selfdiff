"""Build the offline UI, then wheel and source distribution."""
from pathlib import Path
import os
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
output=(root/'src/selfdiff/static').resolve()
output.relative_to(root)
subprocess.run(['npm','--prefix','web','run','build'],cwd=root,check=True,shell=os.name=='nt')
assert (output/'index.html').is_file(), 'Frontend build did not produce index.html'
subprocess.run([sys.executable,'-m','build','--no-isolation'],cwd=root,check=True)
subprocess.run([sys.executable,'scripts/check_package.py','dist'],cwd=root,check=True)
