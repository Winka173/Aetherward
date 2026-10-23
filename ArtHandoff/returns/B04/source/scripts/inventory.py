from pathlib import Path
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[2];m=json.loads((root/'DELIVERABLE_MANIFEST.json').read_text())
rows=[]
for a in m['assets']:
 if a['status']!='delivered':continue
 row={'id':a['id']}
 for key in ['source','master','export']:
  p=root/a[key]
  with Image.open(p) as im:row[key]={'path':a[key],'size':list(im.size),'mode':im.mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 rows.append(row)
(root/'qa/artifact_inventory.json').write_text(json.dumps(rows,indent=2))
print('Inventoried',len(rows),'delivered assets; source/master/export dimensions and hashes.')
