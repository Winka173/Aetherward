"""Run the required repository tools with all outputs and temp files scoped to R02."""
import os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; REPO=ROOT.parents[2]
env=os.environ.copy(); env.update(TEMP=str(ROOT/'_work/tmp'),TMP=str(ROOT/'_work/tmp'),PYTHONDONTWRITEBYTECODE='1')
tool=REPO/'Tools/ArtPipeline/handoff.py'
stage=(ROOT/'_work/stage').resolve()
if not stage.is_relative_to(ROOT.resolve()): raise ValueError('Stage escapes R02')
commands={
 'preview':[sys.executable,str(tool),'preview','--batch','R02','--overlay',str(ROOT/'exports/Art'),'--out',str(ROOT/'previews'),'--tag','R02'],
 'intake':[sys.executable,str(tool),'intake','--batch','R02','--stage-dir',str(stage),'--qa-dir',str(ROOT/'qa')],
 'vfx_preview':[sys.executable,str(ROOT/'source/scripts/preview_vfx.py')],
 'vfx_checks':[sys.executable,str(ROOT/'source/scripts/check_vfx.py')],
}
for name,cmd in commands.items():
    result=subprocess.run(cmd,cwd=REPO,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (ROOT/'qa'/f'{name}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    print(name,'exit',result.returncode,result.stdout[-3000:],flush=True)
