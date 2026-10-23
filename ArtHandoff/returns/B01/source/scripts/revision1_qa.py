"""Report R1 value, resolution, bounds, and silhouette changes; produce review sheets."""
from pipeline import *
from scipy.ndimage import binary_erosion
from PIL import ImageDraw

def luminance(a):return a[...,:3]@[.2126,.7152,.0722]/255

def run():
    records=read(ROOT/'source/revision1_records.json');metrics=[]
    ground=float(luminance(np.array(Image.open(ROOT/'exports/Art/World/arena_background.png'))).mean())
    changed=[x for x in records if not x['id'].startswith('Icons/')]
    sheet=Image.new('RGB',(1000,len(changed)*270),'#292c31');dr=ImageDraw.Draw(sheet)
    for k,rec in enumerate(changed):
        uid=rec['id']; final=Image.open(ROOT/f'exports/Art/{uid}.png').convert('RGBA')
        master=Image.open(ROOT/f'source/masters/{uid}@2x.png')
        old=Image.open(ROOT/rec['reference']).convert('RGBA').resize(final.size,Image.Resampling.LANCZOS)
        a=np.array(final);b=np.array(old);mask=a[:,:,3]>128;bm=b[:,:,3]>128
        edge=mask&~binary_erosion(mask,iterations=3);be=bm&~binary_erosion(bm,iterations=3)
        l=float(luminance(a)[edge].mean());before=float(luminance(b)[be].mean())
        yy,xx=np.where(mask); bounds=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
        metrics.append(dict(id=uid,edgeL=l,beforeEdgeL=before,groundL=ground,passesContract=l>=.27,passesCurrentIntake=l>=ground+.1,footRow=bounds[3],bounds=bounds,silhouetteIoU=float((mask&bm).sum()/(mask|bm).sum()),rawSize=list(Image.open(ROOT/rec['source']).size),masterSize=list(master.size)))
        dr.text((5,k*270+5),uid+f' | before {before:.3f} -> R1 {l:.3f}',fill='white')
        for j,im in enumerate([old,final]):
            im=im.copy();im.thumbnail((230,235),Image.Resampling.LANCZOS);sheet.paste(im,(j*250+10,k*270+25),im)
        # Show both at actual 1440p canvas size, then 720p, beside the comparison.
        for j,height in enumerate([1440,720]):
            ppu=200 if uid.startswith('Heroes/') else 160
            scale=height/15/ppu*(1.25 if 'rift_warden' in uid else 1)
            for t,im in enumerate([old,final]):
                im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
                if im.height>230:im.thumbnail((240,230),Image.Resampling.LANCZOS)
                sheet.paste(im,(510+j*260+t*120,k*270+28),im)
    sheet.save(ROOT/'qa/r1_d2_before_after.png')
    icons=[x for x in records if x['id'].startswith('Icons/')]
    out=Image.new('RGB',(960,((len(icons)+3)//4)*180),'#24262b');dr=ImageDraw.Draw(out)
    for k,rec in enumerate(icons):
        im=Image.open(ROOT/f"exports/Art/{rec['id']}.png");x=k%4*240;y=k//4*180
        preview=im.copy();preview.thumbnail((128,128));out.paste(preview,(x+5,y+4),preview)
        tiny=im.resize((32,32),Image.Resampling.LANCZOS);out.paste(tiny,(x+145,y+40),tiny)
        gray=tiny.convert('LA').convert('RGBA');gray.putalpha(tiny.getchannel('A'));out.paste(gray,(x+190,y+40),gray)
        dr.text((x+5,y+143),rec['id'].split('/')[1],fill='white')
    out.save(ROOT/'qa/r1_icons_32px.png')
    write(ROOT/'qa/r1_metrics.json',dict(groundL=ground,units=metrics,iconCount=len(icons)))
    print(json.dumps(dict(groundL=ground,units=metrics,iconCount=len(icons)),indent=2))

if __name__=='__main__':run()
