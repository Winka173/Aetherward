"""Replay accepted raw generations; does not invoke image generation or edit source art."""
import production as p
records=p.read(p.ROOT/'source/records.json')
for aid,r in records.items():
    p.process(aid,p.ROOT/r['source'],r['prompt'])
