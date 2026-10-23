"""Supplemental source/export contract measurements, confined to B02."""
from pipeline import *
from scipy.ndimage import binary_erosion
def main():
    d=read(ROOT/'DELIVERABLE_MANIFEST.json');rows=[]
    for item in d['assets']:
        if item['status']!='delivered':continue
        a=np.array(Image.open(ROOT/item['export']));m=a[:,:,3]>128
        box=Image.fromarray(m.astype('uint8')*255).getbbox()
        row={'id':item['id'],'bounds':box,'mode':'RGBA','size':list(a.shape[1::-1]),'masterSize':list(Image.open(ROOT/item['master']).size),'issues':[]}
        if item['id'].startswith('Heroes/'):
            edge=m&~binary_erosion(m,iterations=3)
            lum=(a[:,:,0]*.2126+a[:,:,1]*.7152+a[:,:,2]*.0722)/255
            row['edgeLuminance']=float(lum[edge].mean());row['footRow']=box[3]-1
            if row['edgeLuminance']<.27:row['issues'].append('edge luminance below .27')
            if box[0]<40 or box[2]>361 or box[1]<80:row['issues'].append('outside icon box')
            if abs(row['footRow']-372)>(18 if 'downed' in item['id'] else 6):row['issues'].append('foot row')
        rows.append(row)
    write(ROOT/'qa/local_measurements.json',rows)
    print('Local measured:',len(rows),'issues:',sum(bool(x['issues']) for x in rows))
if __name__=='__main__':main()
