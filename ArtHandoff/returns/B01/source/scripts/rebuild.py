"""Reproduce exports from retained sources. Optional --render reruns Blender first."""
from pipeline import *
import os, subprocess
if '--render' in sys.argv:
    tmp=ROOT/'_work/tmp';tmp.mkdir(parents=True,exist_ok=True);env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp),PYTHONDONTWRITEBYTECODE='1')
    blender='C:/Users/Winka/Tools/blender-4.5.14-windows-x64/blender.exe'
    for name in ['crystal','battlefield']:subprocess.run([blender,'-b','--factory-startup','--python',str(ROOT/f'source/blender/{name}.py')],cwd=ROOT,env=env,check=True)
run()
from ingest_sheets import run as sheets
from ingest_singles import run as singles
from finish_geometry import finish
sheets();singles();finish()
from local_qa import run as qa
if (ROOT/'source/revision1_records.json').exists():
    from revision1 import export_one
    for record in read(ROOT/'source/revision1_records.json'):
        export_one(record)
qa()
