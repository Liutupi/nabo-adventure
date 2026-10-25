"""Render the isolated typography proposal, verify 1x bounds and estimate glyph bytes."""
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
from ui_refine_v2_fonts import ART,OUT,ROOT,Type,write_json,sha,P
from ui_refine_v2_pages import cover,map_page,passport

sys.path.insert(0,str(ROOT/'tools'))
from generate_adv_sprites import index_frames,pack,decode


def colors(im):return set(map(tuple,np.asarray(im.convert('RGBA')).reshape(-1,4)))
def ui_colors(im,before,source):
    if not source:return colors(im)
    pixels=np.array(im);sprite=Image.open(ART/source['path']).convert('RGBA');a=source['anchor'];r=source['root']
    x,y=r[0]-a[0],r[1]-a[1];alpha=np.array(sprite)[:,:,3]>0
    original=np.array(before);pixels[y:y+sprite.height,x:x+sprite.width][alpha]=original[y:y+sprite.height,x:x+sprite.width][alpha]
    return colors(Image.fromarray(pixels))|colors(before)


def rle_size(im):
    total=rows=tables=0
    for y in range(0,im.height,256):
        tile=im.crop((0,y,im.width,min(im.height,y+256)));palette,frames=index_frames([tile]);encoded=pack(tile.width,tile.height,frames)
        if decode(encoded,0)!=frames[0]:raise ValueError('RLE roundtrip failed')
        total+=len(encoded['data']);rows+=tile.height
        tables+=len(palette)*2+len(encoded['keys'])*2+len(encoded['rows'])*4
    return {'rle_bytes':total,'table_bytes':tables,'descriptor_estimate_c3':32,'static_estimate_c3':total+tables+32,
            'decoded_rows':rows,'note':'exact streams/tables; descriptor estimate excludes catalog strings and linker padding'}


def main():
    OUT.mkdir(parents=True,exist_ok=True);t=Type();screens={};ui=set();roles=[];assets=[]
    for name,fn in [('cover',cover),('map',map_page),('passport',passport)]:
        start=len(t.runs);im,before,source=fn(t);assert im.size==(240,320)
        if source and sha(ART/source['path'])!=source['sha256']:raise ValueError('Frozen role source SHA mismatch')
        pal=ui_colors(im,before,source);ui|=pal;rgba=len(colors(im));im.save(OUT/f'{name}.png',optimize=True)
        im.resize((720,960),Image.Resampling.NEAREST).save(OUT/f'{name}-3x.png',optimize=True)
        screens[name]=im
        assets.append({'name':name,'path':f'{name}.png','size':[240,320],'sha256':sha(OUT/f'{name}.png'),
                       'ui_colors_excluding_actor':len(pal),'total_rgba_colors':rgba,'text_runs':t.runs[start:],
                       'role_source':source,'safe_bars':None if name=='cover' else {'top':[0,32],'bottom':[290,320]}})
        if source:roles.append(source)
    assert len(ui)<=32,('shared UI palette',len(ui))
    assert len(colors(screens['cover']))<=64,('cover palette',len(colors(screens['cover'])))
    board=Image.new('RGB',(720,320),'#fffaf0')
    for i,im in enumerate(screens.values()):board.paste(im,(i*240,0))
    board.save(OUT/'screens-1x.png');board.resize((1440,640),Image.Resampling.NEAREST).save(OUT/'screens-2x.png')
    comparison=Image.new('RGB',(720,640),'#fffaf0')
    for i,(name,im) in enumerate(screens.items()):
        previous=Image.open(ART/f'ui/preview/{name}.png').convert('RGB');comparison.paste(previous,(i*240,0));comparison.paste(im,(i*240,320))
    comparison.save(OUT/'before-after-1x.png')
    wordmark=screens['cover'].crop((10,12,230,100));wordmark.save(OUT/'collection-wordmark-paper.png')
    # Raw 4bpp glyph estimates execute the same font rasterizer and unique text
    # repertoire used in this proposal. This is not a linked LVGL size claim.
    groups={}
    for run in t.runs:
        key=(run['font'],run['size_px']);groups.setdefault(key,set()).update(c for c in run['text'] if not c.isspace())
    estimates=[]
    for (key,size),chars in sorted(groups.items()):
        bitmaps=sum(math.ceil(t.mask(c,key,size).width*t.mask(c,key,size).height/2) for c in chars)
        estimates.append({'font':key,'size_px':size,'glyphs':''.join(sorted(chars)),'glyph_count':len(chars),
                          'uncompressed_4bpp_bytes':bitmaps,'bitmap_plus_24b_metrics_and_4b_cmap_estimate':bitmaps+len(chars)*28+128})
        if key=='bold' and size in (16,18):(OUT/f'bold{size}-subset.txt').write_text(''.join(sorted(chars))+'\n','utf-8')
    licenses=OUT/'licenses';licenses.mkdir(exist_ok=True)
    source_ofl=ROOT.parent/'nabo-fortune/tools/fonts/OFL-SourceHanSans.txt'
    text=source_ofl.read_text('utf-8');standard=text[text.index('SIL OPEN FONT LICENSE Version 1.1'):]
    (licenses/'NotoSansSC-Bold-OFL.txt').write_text('\n'.join(t.sources['bold']['names']['0'])+'\n\n'+
        '\n'.join(t.sources['bold']['names']['13'])+'\n\n'+standard,'utf-8')
    (licenses/'SourceHanSans-OFL.txt').write_bytes(source_ofl.read_bytes())
    mont=ROOT.parent/'table-undercover/repo/xiaozhi-esp32/managed_components/lvgl__lvgl/scripts/built_in_font/font_license/Montserrat/OFL.txt'
    (licenses/'Montserrat-OFL.txt').write_bytes(mont.read_bytes())
    write_json(OUT/'fonts.json',{'fonts':t.sources,'subsets':['bold16-subset.txt','bold18-subset.txt'],
        'license_texts':['licenses/NotoSansSC-Bold-OFL.txt','licenses/SourceHanSans-OFL.txt','licenses/Montserrat-OFL.txt'],
        'production_reader':'firmware/main/adv_text.c consumes fixed 4bpp; this plan preserves that format',
        'font_files_copied_or_converted':False})
    palette=['#%02x%02x%02x'%p[:3] for p in sorted(ui) if p[3]]
    write_json(OUT/'palette.json',{'basis':'selected 01-passport navy/paper/red; cool neutrals + measured font edge colors',
                                 'visible_colors':len(palette),'colors':palette,'limit':32})
    report={'schema':'nabo-ui-refinement-v2','status':'new design proposal, not selected, not production integration',
        'fonts':t.sources,'screens':assets,'shared_ui_visible_colors':len(palette),'cover_rgba_colors':len(colors(screens['cover'])),
        'wordmark':{'path':'collection-wordmark-paper.png','size':list(wordmark.size),'colors':len(colors(wordmark)),
                    'rle':rle_size(wordmark),'matte':'white paper only; editable source should rerasterize for other backgrounds'},
        'glyph_estimates':estimates,'raw_subset_bitmap_metrics_sum':sum(x['bitmap_plus_24b_metrics_and_4b_cmap_estimate'] for x in estimates),
        'implementation_plan':['Fixed title/logo is raster wordmark, not full TTF/OTF embedded.',
          'Use a bounded Bold16 Chinese/ASCII subset for dynamic station names; keep existing Medium12 body.',
          'Do not add all Chinese glyphs to every 22/24/26 size; those fixed headings are small sprites.',
          'Keep number sprites20/36; regenerate only those twelve glyphs if choosing the new numeral style.',
          'Existing adv_text.c is fixed 4bpp; generated production subsets must stay 4bpp unless separately implemented/tested.',
          'No full-screen framebuffer or heap font rasterization at runtime.'],
        'not_claimed':['official-file cryptographic provenance beyond audited local file metadata and SHA',
                       'font-file conversion or redistribution','final LVGL compressed size','device visual/user acceptance']}
    common=json.loads((ROOT/'firmware/main/generated/adv_assets_generated.json').read_text('utf-8'))
    welcome=json.loads((ROOT/'firmware/main/generated/adv_assets_travel_welcome__p0.json').read_text('utf-8'))
    ui_existing=common['groups']['ui']['static_bytes_estimate_c3'];welcome_bytes=welcome['data_bytes']+welcome['table_bytes']+32
    subset_bytes=sum(e['bitmap_plus_24b_metrics_and_4b_cmap_estimate'] for e in estimates if e['font']=='bold' and e['size_px'] in (16,18))
    digits=0
    for size in (20,36):
        digits+=sum(math.ceil(t.mask(c,'latin',size).width*t.mask(c,'latin',size).height/2)+28 for c in '0123456789m+')+128
    # Conservative: retain the complete old UI and welcome and add replacements
    # without subtracting old logo/numbers. Final integration must run real C packing.
    report['combined_cover_ui_budget']={'existing_ui':ui_existing,'boot_character_welcome':welcome_bytes,
        'baseline_combined':ui_existing+welcome_bytes,'new_wordmark_added_without_removing_old':report['wordmark']['rle']['static_estimate_c3'],
        'new_20_36_digit_4bpp_estimate':digits,
        'conservative_total_estimate':ui_existing+welcome_bytes+report['wordmark']['rle']['static_estimate_c3']+digits,
        'limit':160*1024,'not_hidden_in_travel_group':True,'boundary':'design estimate; final all-assets C pack and linked ELF still required'}
    report['dynamic_font_app_delta']={'budget_baseline_collection_fonts':105053,
        'existing_medium_fonts_removed':0,'bold16_18_added_4bpp_estimate':subset_bytes,
        'estimated_delta':subset_bytes,'estimated_collection_total_if_added':105053+subset_bytes,
        'charged_to':'app flash font baseline separately, not UI sprite budget',
        'scope':'current bounded design repertoire only; real converter C output/ELF and any expanded repertoire must be remeasured'}
    assert report['combined_cover_ui_budget']['conservative_total_estimate']<=160*1024
    tokens={'schema':'nabo-ui-refinement-v2-layout-tokens','map_preview_scope':'typography/card layout demonstration only; not a replacement for the nine-world vertical map',
        'fixture_values':'12 best / 1 of24 are layout examples, not current hardware NVS. Production binds all strings to adv_model state.',
        'preserve_production':{'path_order':'adv_path[] unchanged','world_y':'120 + (8 - path_index) * 112',
            'node_x':'path_index % 2 ? 160 : 80','camera':'existing camera()/traveler() including animated turns and walk',
            'navigation':'UP/DOWN follow adv_path; do not bind two static mockup nodes','world_ground_and_landmarks':'existing WORLD[] gradient, frozen landmark/decor, scroll geometry unchanged'},
        'safe_bars':{'top':[0,32],'bottom':[290,320]},
        'header':{'title':{'font':'bold18','ink':P['white'],'x':20,'ink_top':8,'text':'冒险地图'},
            'world':{'font':'existing medium12','ink':P['white'],'x':104,'ink_top':11,'max_width':56},
            'count':{'font':'latin12 or existing numeric12','ink':P['white'],'right':224,'ink_top':11}},
        'station_cards':{'coordinate_space':'node_screen=(node_x(i),world_y(i)-cam)',
            'box':{'x':'node_x<120 ? node_x+25 : node_x-137','y':'node_y-26','width':112,'height':52},
            'selected':{'fill':P['ink'],'accent_left_px':4,'accent':P['accent'],'text':P['white'],'secondary_text':P['white'],'border':None},
            'normal':{'fill':P['white'],'text':P['ink'],'secondary_text':P['coolgray'],'border':None},
            'locked':{'text':P['coolgray'],'selected_text':P['white']},
            'title':{'font':'bold16','ink_xy_relative':[8,8],'max_ink_height':18},
            'secondary':{'font':'existing medium12','ink_xy_relative':[8,30],'max_ink_height':14},
            'best':{'font':'numeric12','right_relative':104,'ink_top_relative':30},
            'stamps':{'center_x_relative':[13,24,35],'center_y_relative':37,'radius':4},
            'padding_px':8,'font_baseline_rule':'ink_top + actual generated glyph box_h + ofs_y; verify in real C renderer, not nominal point size'},
        'cover':{'wordmark_xy':[10,12],'wordmark_size':[220,88],'character_root':[120,266],
            'caption_ink_top':270,'button':[16,284,208,34],'button_text':P['white']},
        'selected_dynamic_text':'cream #fffaf0 for titles, scores and secondary labels; never navy on navy'}
    write_json(OUT/'layout-tokens.json',tokens)
    write_json(OUT/'qa.json',report)
    print(json.dumps({'output':str(OUT),'shared_ui_colors':len(palette),'cover_colors':report['cover_rgba_colors'],
                      'wordmark':report['wordmark'],'raw_glyph_estimate':report['raw_subset_bitmap_metrics_sum']},indent=2))


if __name__=='__main__':main()
