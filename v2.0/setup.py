import sys
from cx_Freeze import setup, Executable

include_files = ['autorun.inf']
base = None

if sys.platform == "win32":
    base = "Win32GUI"

setup(name="Remoter",
      version="0.1",
      description="Controls the computer",
      options={'build_exe': {'include_files': include_files}},
      executables=[Executable("Client.py", base=base)])
