import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from produce import ROOT, LIVE, REPO, FACTS, savejson

OUT=ROOT/'previews';OUT.mkdir(exist_ok=True)
try: FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
except OSError: FONT=ImageFont.load_default()
BG=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGBA')

def art(aid):
 p=ROOT/'exports/Art'/(aid+'.png')
 if not p.exists():p=LIVE/(aid+'.png')
 return Image.open(p).convert('RGBA') if p.exists() else None

def seq(cat,c):
 if cat=='Heroes':return [c+'_walk_'+x for x in 'abcd'],[c+'_windup',c+'_attack',c+'_follow',c+'_idle']
 return [c+'_'+x for x in 'abcd'],[c+('_tell' if c=='rift_warden' else '_windup'),c+'_attack',c+'_a']

def paste(canvas,aid,x,foot,game=True):
 im=art(aid);d=ImageDraw.Draw(canvas)
 if im is None:
  d.text((x-70,foot-45),'BLOCKED: '+aid.split('/')[-1],font=FONT,fill='white');return
 cat=aid.split('/')[0];size=(192 if cat=='Heroes' else 384 if 'rift_warden' in aid else 154) if game else 230
 im=im.resize((size,size),Image.Resampling.LANCZOS)
 f=476/512 if cat=='Heroes' else 486/512 if 'rift_warden' in aid else 236/256
 canvas.alpha_composite(im,(round(x-size/2),round(foot-size*f)))

def build():
 chars=list(dict.fromkeys((f['id'].split('/')[0],f['like'].split('/')[1].rsplit('_',1)[0]) for f in FACTS))
 rows=[]
 for cat,c in chars:
  walk,attack=seq(cat,c);row=BG.resize((3200,440),Image.Resampling.LANCZOS);d=ImageDraw.Draw(row)
  d.rectangle((0,0,3200,38),fill=(20,12,32,235));d.text((16,9),c+' | OFFLINE PREVIEW | walk a-b-c-d; attack preparation-strike-recovery',font=FONT,fill='white')
  for k,n in enumerate(walk+attack):
   x=200+k*400;paste(row,cat+'/'+n,x,415);d.text((x-90,420),n,font=FONT,fill='white')
  rows.append(row)
  # One GIF per sequence and a combined GIF per character. GIF time base is 10 ms:
  # alternating delays approximate 8 fps (120/130 ms) and 12 fps (80/80/90 ms).
  allframes=[];alldurations=[]
  for kind,names,delays in [('walk',walk,[120,130,120,130]),('attack',attack,[80,80,90,80])]:
   frames=[];dur=[]
   for k,n in enumerate(names):
    frame=BG.resize((640,520),Image.Resampling.LANCZOS);dd=ImageDraw.Draw(frame)
    dd.rectangle((0,0,640,62),fill=(20,12,32,255));dd.text((12,8),'OFFLINE PREVIEW - '+c+' / '+kind,font=FONT,fill='white');dd.text((12,33),n,font=FONT,fill='white')
    paste(frame,cat+'/'+n,320,490);frames.append(frame.convert('RGB'));dur.append(delays[k%len(delays)])
   frames[0].save(OUT/(c+'_'+kind+'.gif'),save_all=True,append_images=frames[1:],duration=dur,loop=0,optimize=False)
   allframes+=frames;alldurations+=dur
  allframes[0].save(OUT/(c+'.gif'),save_all=True,append_images=allframes[1:],duration=alldurations,loop=0,optimize=False)
 full=Image.new('RGBA',(3200,len(rows)*440))
 for i,r in enumerate(rows):full.alpha_composite(r,(0,i*440))
 full.convert('RGB').save(OUT/'cycles_game_scale.png')
 overview=Image.new('RGBA',(2560,1440),(20,12,32,255));od=ImageDraw.Draw(overview)
 od.text((16,8),'OFFLINE PREVIEW - all characters (reduced overview). Game-size rows: cycles_game_scale.png / cycles_page_*.png',font=FONT,fill='white')
 for i,row in enumerate(rows):
  small=row.resize((1280,176),Image.Resampling.LANCZOS);overview.alpha_composite(small,((i%2)*1280,42+(i//2)*278))
 overview.convert('RGB').save(OUT/'cycles_1440.png')
 for start in range(0,len(rows),3):
  page=Image.new('RGBA',(2560,1440),(20,12,32,255))
  for k,row in enumerate(rows[start:start+3]):
   # Preserve rendered unit scale by removing spacing rather than resampling sprites.
   cat,c=chars[start+k];walk,attack=seq(cat,c);band=BG.resize((2560,440),Image.Resampling.LANCZOS);bd=ImageDraw.Draw(band)
   bd.rectangle((0,0,2560,38),fill=(20,12,32,255));bd.text((12,8),'OFFLINE PREVIEW - '+c+' - 1440p game scale',font=FONT,fill='white')
   for z,name in enumerate(walk+attack):
    x=160+z*320;paste(band,cat+'/'+name,x,415);bd.text((x-90,420),name,font=FONT,fill='white')
   page.alpha_composite(band,(0,k*470+15))
  page.convert('RGB').save(OUT/f'cycles_page_{start//3+1}_1440.png')
 # These dimensions preserve true 1440p game-size units across ten character rows;
 # the contact sheet intentionally scrolls vertically and is not a screenshot.
 for h in [1080,720]:overview.resize((round(2560*h/1440),h),Image.Resampling.LANCZOS).convert('RGB').save(OUT/f'cycles_{h}.png')
 delivered=[f for f in FACTS if (ROOT/'exports/Art'/(f['id']+'.png')).exists()]
 for mode in ['colour','silhouette','grayscale']:
  sheet=Image.new('RGBA',(1600,((len(delivered)+7)//8)*230),(160,160,160,255));d=ImageDraw.Draw(sheet)
  for i,f in enumerate(delivered):
   im=art(f['id']).resize((190,190),Image.Resampling.LANCZOS)
   if mode=='silhouette':
    a=im.getchannel('A');im=Image.new('RGBA',im.size,(0,0,0,255));im.putalpha(a)
   elif mode=='grayscale':
    a=im.getchannel('A');im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(a)
   x=(i%8)*200;y=(i//8)*230;sheet.alpha_composite(im,(x,y));d.text((x+3,y+193),f['id'].split('/')[-1],font=FONT,fill=(25,12,30))
  sheet.convert('RGB').save(OUT/f'review_{mode}.png')
 print('Saved cycles and 30 labelled GIFs; missing frames visibly labelled BLOCKED.')

if __name__=='__main__':build()
