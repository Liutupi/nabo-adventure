"""Technical layer/pivot visualizations; guide marks are not character artwork."""
import json
from PIL import Image, ImageDraw
from build_travel_rig import ART, RIG
from rig_preview import font


def main():
    rig = json.loads((RIG/'rig.json').read_text('utf-8'))
    folder = ART/'preview/travel'
    contract = Image.new('RGB', (900,620), '#e9e5df')
    cd = ImageDraw.Draw(contract)
    cd.text((15,8), 'Pixel-slice SVG rig: source RGB + explicit masks / pivots', fill='#182439', font=font(20))
    for column, (facing, view) in enumerate(rig['views'].items()):
        reference = Image.open(RIG/view['reference']).convert('RGBA')
        enlarged = reference.resize((512,512),Image.Resampling.NEAREST)
        # Contract view is one full 256px frame, at 1x, plus explicit coordinates.
        contract.paste(reference,(column*300+20,50),reference)
        cd.text((column*300+20,320),f'{facing}: independent source', fill='#182439',font=font(15))
        cd.text((column*300+20,345),'anchor (128,224) / no mirror', fill='#182439',font=font(14))
        for name, part in view['parts'].items():
            x,y=part['pivot']
            px,py=column*300+20+x,50+y
            cd.ellipse((px-2,py-2,px+2,py+2),fill='#ff7040')
        cd.line((column*300+20,274,column*300+276,274),fill='#ff7040',width=1)
        atlas=Image.new('RGB',(1120,500),'#24354b')
        ad=ImageDraw.Draw(atlas)
        for i,name in enumerate(rig['draw_order']):
            part=view['parts'][name]
            layer=Image.open(RIG/part['raster']).convert('RGBA')
            layer.thumbnail((150,220),Image.Resampling.LANCZOS)
            x0,y0=(i%7)*160,(i//7)*250
            atlas.paste(layer,(x0+5,y0+20),layer)
            ad.text((x0+5,y0+225),name,fill='white',font=font(12))
        atlas.save(folder/f'layers-{facing}.png')
    cd.text((15,405),'Orange dots: pivots; orange line: y=224. SVGs embed raster slices, not new vector faces.',fill='#182439',font=font(16))
    cd.text((15,440),'Masks and overlap circles are stored per layer in rig.json and *-mask.png.',fill='#182439',font=font(16))
    cd.text((15,475),'Head + neutral expression use exactly the same rigid translation in every pose.',fill='#182439',font=font(16))
    cd.text((15,510),'Source alpha <16 discarded explicitly; final delivery alpha threshold =128.',fill='#182439',font=font(16))
    cd.text((15,545),'This diagram establishes coordinates, not human identity or animation acceptance.',fill='#182439',font=font(16))
    contract.save(folder/'rig-contract.png')


if __name__=='__main__':
    main()
