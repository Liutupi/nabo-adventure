"""Real-size fall/neutral slope playback with an existing shared snow lip at contact."""
import json
import numpy as np
from PIL import Image,ImageDraw
from ski_config import ART,GAME,PREVIEW
from rig_preview import font
from travel_export import durations


def load(path):return Image.open(path).convert('RGBA')


def scene(entry,index,background,lip):
    screen=Image.new('RGBA',(240,320),tuple(background))
    for x,y in [(8,35),(174,91),(3,220)]:screen.alpha_composite(load(GAME/'props/pine-large.png'),(x,y))
    for x,y in [(156,16),(205,185)]:screen.alpha_composite(load(ART/'map/tiles/ski/snow-pine.png'),(x,y))
    screen.alpha_composite(load(GAME/'props/gate-red.png'),(74,68))
    screen.alpha_composite(load(GAME/'props/gate-blue.png'),(135,229))
    screen.alpha_composite(load(GAME/'props/hot-cocoa-cabin.png'),(7,113))
    # Existing shared snow tile; one physical lip remains fixed throughout the
    # sequence. Its top opaque pixel is adjacent to the final mitten bottom.
    snow=load(ART/'map/tiles/ski/snow-mound.png');a=np.asarray(snow)[:,:,3];yy,xx=np.where(a>0)
    top=int(yy.min());crown=int(round(xx[yy==top].mean()))
    screen.alpha_composite(snow,(lip[0]-crown,lip[1]-top))
    frame=load(ART/entry['runtime_frames'][index]);ax,ay=entry['runtime_anchor']
    screen.alpha_composite(frame,(119-ax,211-ay))
    return screen.convert('RGB')


def main():
    m=json.loads((ART/'ski-manifest.json').read_text('utf-8'));lookup={(e['skin'],e['name']):e for e in m['animations']}
    fall=lookup['ski_a','fall'];straight=lookup['ski_a','straight'];background=m['background']['preview_rgb']
    contact=fall['fall_contract']['per_frame'][3]['runtime_contact_edge'];a=fall['runtime_anchor']
    lip=[119+contact[0]-a[0],211+contact[1]-a[1]]
    sequence=[(straight,i,'straight') for i in range(6)]+[(fall,i,fall['fall_contract']['phases'][i]) for i in range(8)]+[(straight,i,'straight') for i in range(6)]
    frames=[]
    for e,i,label in sequence:
        screen=scene(e,i,background,lip);ImageDraw.Draw(screen).text((4,4),label,fill='#203849',font=font(12));frames.append(screen)
    frames[0].save(PREVIEW/'fall-v2-slope-continuity.gif',save_all=True,append_images=frames[1:],duration=durations(len(frames)),loop=0,disposal=2)
    sheet=Image.new('RGB',(1200,1280),tuple(background))
    for j,frame in enumerate(frames):sheet.paste(frame,((j%5)*240,(j//5)*320))
    sheet.save(PREVIEW/'fall-v2-slope-continuity-contact.png')
    eight=Image.new('RGB',(240*8,320),tuple(background))
    for i in range(8):
        im=scene(fall,i,background,lip);ImageDraw.Draw(im).text((4,4),f'{i}: '+fall['fall_contract']['phases'][i],fill='#203849',font=font(12))
        eight.paste(im,(i*240,0))
    eight.save(PREVIEW/'fall-v2-slope-all8.png')
    hit=scene(fall,3,background,lip);hit.save(PREVIEW/'fall-v2-snow-contact-1x.png')
    cut=hit.crop((lip[0]-36,lip[1]-48,lip[0]+36,lip[1]+24));cut.resize((432,432),Image.Resampling.NEAREST).save(PREVIEW/'fall-v2-snow-contact-detail.png')


if __name__=='__main__':main()
