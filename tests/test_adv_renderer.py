"""Render the production adventure screens and the legacy jump page into an emulated panel.

Every screen is saved under docs/images/ui/ (UI_DESIGN.md shows them) and private/previews/.
After every input the incremental frame must equal a full redraw, and no frame may overflow.
"""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from PIL import Image
from host_tools import CC, SHARED_EXPORT, asm_section, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'
HOST = ROOT/'tests/adv_host'
UP, DOWN, OK = 0, 1, 2
PRESS, CLICK, DOUBLE, LONG, RELEASE = 0, 1, 2, 3, 4
SOURCES = ['adv_boot_motion.c', 'adv_model.c', 'adv_stations.c', 'adv_demo.c', 'adv_post.c','adv_night.c','adv_ui_night.c','adv_climb.c','adv_ui_climb.c','adv_ski.c','adv_ui_ski.c','adv_sky.c','adv_ui_sky.c','adv_space.c','adv_ui_space.c', 'adv_ui_post.c', 'adv_ui_post_session.c', 'collection_model.c', 'adv_gfx.c', 'adv_ninepatch.c', 'adv_shapes.c', 'adv_sprite.c',
           'adv_text.c', 'adv_ui.c', 'adv_ui_animation.c', 'adv_ui_art.c', 'adv_ui_map.c', 'adv_ui_session.c', 'adv_ui_jump.c', 'collection_portrait.c',
           'nabo_jump_model.c', 'nabo_jump_rig.c', 'nabo_jump_codec.c','nabo_dive_text.c', 'collection_font_12.c', 'collection_font_16.c',
           'collection_font_18.c', 'nabo_poster_font_28.c', 'nabo_poster_font_48.c', 'nabo_mono_font_12.c','adv_video.c','adv_ui_boot_video.c']

def ui_color(name):
    palette=json.loads((ROOT/'game-art/adventure/art/ui/palette.json').read_text('utf-8'))
    r,g,b=bytes.fromhex(palette[name].lstrip('#'))
    return (r>>3)<<11 | (g>>2)<<5 | b>>3

class Renderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        folder = Path(cls.tmp.name)
        assembly = folder/'assets.S'
        lines = [asm_section()]
        for filename in ('jump_sprites.bin',):
            stem = filename.replace('.', '_')
            lines += ['.balign 4', f'.global _binary_{stem}_start', f'_binary_{stem}_start:',
                      f'.incbin "{(BOARD/filename).as_posix()}"',
                      f'.global _binary_{stem}_end', f'_binary_{stem}_end:']
        assembly.write_text('\n'.join(lines)+'\n', 'utf-8')
        library = folder/'adv_render.dll'
        arguments = (['-std=gnu11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-Wno-missing-field-initializers', '-I', str(HOST), '-I', str(BOARD), '-I', str(BOARD/'generated')] +
                       [str(BOARD/s) for s in SOURCES] + [str(p) for p in sorted((BOARD/'generated').glob('*.c'))] + [str(HOST/'adv_ui_host.c'), str(assembly), '-lm', '-o',
                       str(library)])
        # Eight games exceed Windows CreateProcess's command-line limit. GCC's
        # response file also preserves paths containing spaces on every host.
        response = folder/'render-arguments.rsp'
        response.write_text('\n'.join('"'+arg.replace('\\', '\\\\').replace('"', '\\"')+'"'
                                      for arg in arguments)+'\n', 'utf-8')
        subprocess.run([CC, '@'+str(response)], check=True)
        cls.lib = lib = ctypes.CDLL(str(library))
        lib.host_new.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        lib.host_legacy.argtypes = [ctypes.c_uint32]
        lib.host_snapshot.argtypes = [ctypes.POINTER(ctypes.c_uint16)]
        lib.host_jump_reset.argtypes = [ctypes.c_int]
        lib.host_jump_tick.argtypes = [ctypes.c_uint32, ctypes.c_int]
        lib.host_jump_item.argtypes = [ctypes.c_int, ctypes.c_int]
        lib.host_band.argtypes = [ctypes.c_uint16, ctypes.c_uint16]
        lib.host_draw_at.argtypes = [ctypes.c_uint32]
        lib.host_boot_start.argtypes = [ctypes.c_uint32]
        lib.host_fail_caps.argtypes = [ctypes.c_size_t]
        lib.adv_ui_staging_bytes.restype = ctypes.c_uint32
        lib.ui_space_staging_bytes.restype = ctypes.c_uint32
        lib.ui_space_cache_bytes.restype = ctypes.c_uint32
        lib.adv_boot_motion_enabled.restype = ctypes.c_bool
        class BootStats(ctypes.Structure):
            _fields_=[(name,ctypes.c_uint32) for name in ('frames','skipped','last_frame','elapsed_ms')]
        lib.ui_boot_video_stats.restype=BootStats
        cls.previews = ROOT/'private/previews'
        cls.previews.mkdir(parents=True, exist_ok=True)
        cls.docs = ROOT/'docs/images/ui'
        cls.docs.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.lib.host_close()
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def snapshot(self):
        pixels = (ctypes.c_uint16 * (240*320))()
        self.lib.host_snapshot(pixels)
        return list(pixels)

    def view_image(self):
        rgb = [((v >> 11)*255//31, ((v >> 5)&63)*255//63, (v&31)*255//31) for v in self.snapshot()]
        image = Image.new('RGB', (240, 320)); image.putdata(rgb)
        if self.lib.adv_ui_width()==320:image=image.transpose(Image.Transpose.ROTATE_270)
        return image

    def save(self, name, docs=False):
        image=self.view_image()
        image.save(self.previews/name)
        if docs: image.save(self.docs/name)

    def new(self, best, seen=0, seed=1):
        self.assertEqual(self.lib.host_new(seed, (ctypes.c_uint32 * 9)(*best), seen), 1)

    def check(self, label):
        """Draws the next frame incrementally and proves it equals a full redraw."""
        self.lib.host_draw()
        self.assertFalse(self.lib.host_overflow(), f'display list overflow at {label}')
        incremental = self.snapshot()
        self.last_incremental_bytes=self.lib.host_bytes()
        self.lib.host_full()
        self.assertEqual(incremental, self.snapshot(), f'stale pixels at {label}')

    def ev(self, button, event):
        self.lib.host_event(button, event)
        self.check(f'event {button},{event}')

    def click(self, button):
        for event in (PRESS, RELEASE, CLICK): self.ev(button, event)

    def steps(self, n):
        self.lib.host_steps(n)
        self.check(f'{n} steps')

    def test_v2_landscape_dma_staging_is_fenced_and_released(self):
        for game in ('night','ski','space'):
            self.new([0]*9,seen=0xffffff)
            getattr(self.lib,'host_'+game+'_case')(0)
            self.check(game+' action pipeline')
            self.assertEqual(self.lib.adv_ui_staging_bytes(),61440)
            for _ in range(6):self.steps(5)
            self.ev(DOWN,LONG)
            self.assertEqual(self.lib.host_phase(),3)
            self.ev(UP,DOUBLE)
            self.assertIn(self.lib.host_page(),(1,5))
            self.assertEqual(self.lib.adv_ui_staging_bytes(),0)
            self.lib.host_close()
            self.assertEqual(self.lib.adv_ui_staging_bytes(),0)

    def test_v2_landscape_allocation_failure_keeps_identical_pixels(self):
        for game in ('night','ski','space'):
            self.new([0]*9,seen=0xffffff)
            getattr(self.lib,'host_'+game+'_case')(0)
            self.lib.host_fail_caps(61440)
            self.lib.host_draw()
            self.assertEqual(self.lib.adv_ui_staging_bytes(),0)

            self.assertFalse(self.lib.host_overflow())
            fallback=self.snapshot()
            self.lib.host_full()
            self.assertEqual(self.lib.adv_ui_staging_bytes(),61440)
            self.assertFalse(self.lib.host_overflow())
            self.assertEqual(fallback,self.snapshot())
            self.ev(DOWN,LONG);self.ev(UP,DOUBLE)
            self.assertEqual(self.lib.adv_ui_staging_bytes(),0)

    def test_space_marks_release_on_exit_and_recover_after_allocation_failure(self):
        self.new([0]*9,seen=0xffffff);self.lib.host_space_case(1);self.lib.host_fail_caps(8192)
        self.lib.host_draw();self.assertTrue(self.lib.host_overflow());self.assertEqual(self.lib.ui_space_staging_bytes(),0)
        self.lib.host_full();self.assertFalse(self.lib.host_overflow());self.assertEqual(self.lib.ui_space_staging_bytes(),8192)
        self.check('SPACE recovered render');self.ev(DOWN,LONG);self.ev(UP,DOUBLE)
        self.assertEqual(self.lib.ui_space_staging_bytes(),0)
        self.lib.host_space_case(1);self.check('SPACE re-entry');self.lib.host_close()
        self.assertEqual(self.lib.ui_space_staging_bytes(),0)

    def test_space_cloud_cache_is_exact_with_failure_retry_and_exit(self):
        self.new([0]*9,seen=0xffffff);self.lib.host_space_case(1)
        # Each context holds one pointer and two ints; device pointers are 32-bit.
        size=39680+32*(ctypes.sizeof(ctypes.c_void_p)+8)
        self.lib.host_fail_caps(size);self.lib.host_draw()
        self.assertEqual(self.lib.ui_space_cache_bytes(),0)
        original=self.snapshot();self.lib.host_full()
        self.assertEqual(self.lib.ui_space_cache_bytes(),size)
        self.assertEqual(self.snapshot(),original)
        self.check('cloud cache exact incremental composition')
        self.ev(DOWN,LONG);self.ev(UP,DOUBLE)
        self.assertEqual(self.lib.ui_space_cache_bytes(),0)
        self.lib.host_space_case(1);self.lib.host_full();self.lib.host_close()
        self.assertEqual(self.lib.ui_space_cache_bytes(),0)

    def test_every_screen(self):
        self.new([0, 12, 350, 7, 0, 0, 0, 0, 0], seen=0b11011001)
        self.check('cover'); self.save('cover.png', True)
        self.click(OK); self.save('map-town.png', True)
        self.click(DOWN); self.click(DOWN); self.save('map-sea.png', True)
        for _ in range(4): self.click(UP)
        self.save('map-locked.png', True)
        self.click(DOWN); self.click(OK); self.save('title.png', True)
        self.click(OK); self.steps(30); self.save('ready.png', True)
        self.steps(160); self.save('play.png', True)
        self.ev(UP, PRESS); self.ev(UP, LONG); self.ev(UP, RELEASE); self.save('pause.png', True)
        self.click(OK)
        for _ in range(30000):
            self.lib.host_steps(1)
            if self.lib.host_phase() == 4: break
        self.check('end'); self.save('end.png', True)
        self.steps(120); self.assertEqual(self.lib.host_phase(), 5); self.save('result.png', True)
        self.ev(UP, DOUBLE)
        self.click(DOWN); self.click(DOWN); self.click(OK); self.save('kiosk.png', True)
        self.click(OK); self.click(DOWN); self.save('passport.png', True)
        self.click(OK); self.click(DOWN); self.click(OK); self.save('settings.png', True)
        self.click(OK); self.click(UP); self.save('settings-edit.png')
        self.click(OK)
        for _ in range(4): self.click(DOWN)
        self.click(OK); self.save('status.png', True)

    def test_post_native_playfield_reactions_and_dense_scene(self):
        self.new([0,99,0,0,0,0,0,0,0],seen=7)
        names=('idle','whistle','hit','throw','delivered','switch','dense','ready-to-send','wrong-track','choose-upper','choose-lower','route-locked','route-selected')
        for case,name in enumerate(names):
            self.lib.host_post_case(case);self.check('POST '+name);self.save('post-'+name+'.png',True)
        self.lib.host_post_case(0);self.check('POST fixed upper backdrop')
        before=self.view_image().crop((0,90,320,98)).tobytes()
        for _ in range(20):self.steps(3)
        self.assertEqual(before,self.view_image().crop((0,90,320,98)).tobytes())
        self.assertLess(self.last_incremental_bytes,240*200*2,'H redraw should stay below a full screen')

    def test_post_practice_steps_remain_visible_and_incremental(self):
        self.new([0,99,0,0,0,0,0,0,0],seen=7)
        for lesson in range(6):
            self.lib.host_post_practice_case(lesson);self.check('POST practice '+str(lesson))
            self.save('post-practice-'+str(lesson)+'.png',True)
        self.lib.host_post_practice_case(2);self.check('POST waiting for a tap');self.steps(1200)
        self.assertEqual(self.lib.host_phase(),2)

    def test_climb_native_scenes_and_every_session_phase_are_incremental(self):
        self.new([0,50,600,25,60,0,0,0,0],seen=0xfff)
        names=('idle','switch','charge','jump','hit-slide','holds','rocks','snow','title','ready','pause','end','result','max-record','milestone','cold')
        for case,name in enumerate(names):
            self.lib.host_climb_case(case);self.check('CLIMB '+name);self.save('climb-'+name+'.png',True)
            self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(240,320))
            if name=='title':
                source=Image.open(ROOT/'game-art/adventure/art/ui/wordmarks/climb.png').convert('RGBA')
                got=self.view_image().crop((20,42,220,122))
                for (r,g,b,a),pixel in zip(source.getdata(),got.getdata()):
                    if a==255:self.assertEqual(pixel,((r>>3)*255//31,(g>>2)*255//63,(b>>3)*255//31));break
        # Climbing for real scrolls every frame; each frame must still equal a full redraw.
        self.lib.host_climb_case(0)
        for _ in range(3):
            self.ev(OK,PRESS);self.steps(2);self.ev(OK,RELEASE);self.ev(OK,CLICK)
            for _ in range(6):self.steps(5)
        self.ev(OK,PRESS);self.steps(30);self.ev(OK,RELEASE);self.ev(OK,LONG)
        for _ in range(8):self.steps(5)
        self.ev(UP,LONG);self.assertEqual(self.lib.host_phase(),3)
        for _ in range(2):self.ev(UP,PRESS);self.ev(UP,RELEASE);self.ev(UP,CLICK)
        self.ev(UP,DOUBLE);self.assertIn(self.lib.host_page(),(1,5))   # map, or the stamp ceremony first

    def test_ski_sky_space_scenes_and_phases_are_incremental(self):
        self.new([0,50,600,25,60,300,45,1000,0],seen=0x7fffff)
        games={'sky':('drift','heat','vent','hit','stamp','dense','low','warm')}
        phases=('title','ready','pause','end','result','max-record')
        for game,names in games.items():
            case=getattr(self.lib,'host_'+game+'_case')
            for which,name in enumerate(names+phases):
                case(which);self.check(game+' '+name);self.save(game+'-'+name+'.png',True)
                self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(240,320))
            case(0)
            for _ in range(6):self.ev(OK,PRESS);self.steps(4);self.ev(OK,RELEASE);self.steps(10)
            for button in (UP,DOWN):
                self.ev(button,PRESS);self.steps(12);self.ev(button,RELEASE)
            for _ in range(2):self.ev(UP,PRESS);self.ev(UP,RELEASE);self.ev(UP,CLICK)
            self.ev(UP,DOUBLE);self.assertIn(self.lib.host_page(),(1,5))

    def test_space_v2_native_journey_scenes_and_controls(self):
        self.new([0]*9,seen=0xffffff)
        names=('ignite','ascent','boost','landed','flag','lost','orbit','transfer','title','ready','pause','end','result','max-record','dense','separation','upper','landing')
        for which,name in enumerate(names):
            self.lib.host_space_case(which);self.check('SPACE V2 '+name);self.save('space-'+name+'.png',True)
            self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(320,240))
        self.lib.host_space_case(1)
        for _ in range(6):self.steps(4)
        self.ev(UP,DOUBLE);self.assertEqual(self.lib.host_page(),7)
        self.ev(DOWN,LONG);self.assertEqual(self.lib.host_phase(),3)
        self.ev(UP,DOUBLE);self.assertEqual(self.lib.host_page(),1)

    def test_ski_v2_scenes_fit_the_op_budget_and_leave_only_from_pause(self):
        self.new([0,50,600,25,60,300,0,0,0],seen=0x7fffff)
        names=('straight','carve','hop','crash','spin','dense','gate','avalanche-fog','title','ready','pause','end','result','max-record')
        for which,name in enumerate(names):
            self.lib.host_ski_case(which);self.check('SKI '+name);self.save('ski-'+name+'.png',True)
            self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(320,240))
        self.lib.host_ski_case(0)
        for _ in range(10):self.steps(3)
        self.check('SKI scrolling')
        self.ev(UP,PRESS);self.ev(UP,RELEASE);self.ev(UP,CLICK);self.ev(UP,DOUBLE)
        self.assertEqual(self.lib.host_page(),7,'Double UP while playing must not leave SKI V2')
        self.ev(DOWN,PRESS);self.ev(DOWN,LONG);self.ev(DOWN,RELEASE)
        self.assertEqual(self.lib.host_phase(),3)
        self.ev(UP,DOUBLE);self.assertEqual(self.lib.host_page(),1)

    def test_night_v2_scenes_fit_the_op_budget_and_leave_only_from_pause(self):
        self.new([0,50,600,25,0,0,0,0,0],seen=0xffffff)
        names=('walk','run','swing','moth-gold','low-light','owl','burst','event','title','ready','pause','end','result','max-record','dense')
        for case,name in enumerate(names):
            self.lib.host_night_case(case);self.check('NIGHT '+name);self.save('night-'+name+'.png',True)
            self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(320,240))
        self.lib.host_night_case(0);self.check('NIGHT play')
        for _ in range(20):self.steps(3)
        self.check('NIGHT scrolling')
        self.ev(UP,PRESS);self.ev(UP,RELEASE);self.ev(UP,CLICK);self.ev(UP,DOUBLE)
        self.assertEqual(self.lib.host_page(),7,'Double UP while playing must not leave NIGHT V2')
        self.ev(DOWN,PRESS);self.ev(DOWN,LONG);self.ev(DOWN,RELEASE)
        self.assertEqual(self.lib.host_phase(),3)
        self.ev(UP,DOUBLE);self.assertEqual(self.lib.host_page(),1)
        self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(240,320))

    def test_route_guidance_never_covers_ahead_station_or_its_mail(self):
        self.new([0,99,0,0,0,0,0,0,0],seen=7)
        for lane in (0,1):
            for x in (200,240,280):
                self.lib.host_post_station_at(lane,x);self.check(f'station visible {lane},{x}')
                actual=self.view_image()
                if x==240:self.save('post-station-visible-'+('lower' if lane else 'upper')+'.png',True)
                self.lib.host_post_station_reference(lane,x);reference=self.view_image()
                opaque=[(i,p) for i,p in enumerate(reference.getdata()) if p!=(255,0,255)]
                self.assertGreater(len(opaque),500,'the real station and envelope must be present')
                scene=list(actual.getdata())
                self.assertTrue(all(scene[i]==p for i,p in opaque),f'UI obscures station/mail at lane={lane},x={x}')

    def test_landscape_rotation_has_no_mirror_and_returns_to_portrait(self):
        self.new([0,99,0,0,0,0,0,0,0],seen=7)
        self.lib.host_post_case(0);self.check('landscape enter')
        self.assertEqual((self.lib.adv_ui_width(),self.lib.adv_ui_height()),(320,240))
        self.assertEqual(self.lib.host_rotation_patch(),1)
        image=self.snapshot()
        self.assertEqual([image[y*240+x] for y in (311,312) for x in (9,10,11)],
                         [0x1002,0x1004,0x1006,0x1001,0x1003,0x1005])
        self.lib.host_full();self.ev(UP,DOUBLE)
        self.assertEqual((self.lib.host_page(),self.lib.adv_ui_width(),self.lib.adv_ui_height()),(1,240,320))

    def test_viewport_clips_landscape_edges_and_forces_full_orientation_change(self):
        self.assertEqual(self.lib.host_viewport_edges(),1)

    def test_post_alpha_trims_cover_every_original_opaque_pixel(self):
        import re
        art=ROOT/'game-art/adventure/art';manifest=json.loads((art/'post-manifest.json').read_text('utf-8'))
        source=(BOARD/'adv_ui_post.c').read_text('utf-8')
        clips={a['skin']+'/'+a['name']:a['runtime_frames'] for a in manifest['animations']}
        clips.update({'game/'+a['id']:[a['path']] for a in manifest['assets']})
        for name in ('post_props/wheel-cycle','post_props/whistle-cord','game/post/props/locomotive-body','game/post/props/cab-foreground'):
            match=re.search(r'ui_art_crop\(g,"'+re.escape(name)+r'"[^;\n]*,(\d+),(\d+),(\d+),(\d+)\);',source)
            self.assertIsNotNone(match,name);box=tuple(map(int,match.groups()))
            boxes=[Image.open(art/p).getbbox() for p in clips[name]]
            union=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
            self.assertEqual(box,union,name)

    def test_stamp_ceremony_every_tier(self):
        self.new([0, 60, 0, 0, 0, 0, 0, 0, 0])
        self.click(OK)
        for tier, name in enumerate(('stamp-bronze.png', 'stamp-silver.png', 'stamp-gold.png')):
            self.assertEqual(self.lib.host_page(), 5)
            self.save(name, True)
            pixels=self.snapshot()
            caption=[pixels[y*240+x] for y in range(230,251) for x in range(95,145)]
            self.assertGreater(caption.count(ui_color('ink')),20,'stamp tier captions need dark text contrast')
            self.click(OK)
        self.assertEqual(self.lib.host_page(), 1)

    def test_whole_map_fully_unlocked(self):
        self.new([0, 60, 700, 30, 70, 400, 50, 1200, 1000], seen=0xffffff)
        self.click(OK)
        for _ in range(3): self.click(DOWN)
        for i in range(9):
            self.save(f'map-{i}.png')
            self.click(UP)
        self.save('map-space.png', True)

    def test_passport_locked_selection_and_uint32_records(self):
        self.new([0]*9)
        self.click(OK); self.ev(OK, LONG); self.click(DOWN)
        self.save('passport-selected-locked.png')
        pixels=self.snapshot()
        lock=[pixels[y*240+x] for y in range(99,117) for x in range(204,220)]
        self.assertGreater(lock.count(ui_color('white')),10,'selected lock must contrast with the navy card')
        self.new([0xffffffff]*9, seen=0xffffff)
        self.click(OK); self.ev(OK, LONG)
        self.save('passport-max-records.png')
        maximum=self.snapshot()
        self.new([10000]*9, seen=0xffffff)
        self.click(OK); self.ev(OK, LONG)
        self.assertEqual(maximum,self.snapshot(),'all overflow records use the same bounded display marker')

    def test_boot_and_map_animation_incremental_matches_full_at_boundaries(self):
        self.new([0, 60, 700, 30, 70, 400, 50, 1200, 1000], seen=0xffffff)
        self.lib.host_boot_start(1000)
        frames = []
        times = (0, 250, 449, 450, 600, 1000, 1399, 1400, 1500, 2000, 2733, 2734, 4066, 4067, 4417, 5000,6000,6599,6600,7000)
        next_pose=1
        for t in times:
            # Advance the real movie between observation boundaries. Production
            # submits each pose rather than seeking past unseen frames.
            while next_pose<73 and next_pose*1000//12<=t:
                self.lib.host_draw_at(1000+next_pose*1000//12);next_pose+=1
            self.lib.host_draw_at(1000 + t)
            self.check(f'boot {t}')
            frames.append(self.snapshot())
            if t in (0, 1000, 2000, 5000): self.save(f'boot-{t}.png', True)
        if self.lib.adv_boot_motion_enabled():
            self.assertNotEqual(frames[times.index(2000)], frames[-1], 'selected introduction must perform a gesture')
        selected=json.loads((ROOT/'game-art/adventure/art/boot/selection.json').read_text('utf-8'))
        if selected.get('kind')=='mpeg1-ip':
            self.assertNotEqual(frames[0],frames[-1],'Grok final pose must be held without snapping to the opening frame')
        else:self.assertEqual(frames[0], frames[-1], 'the one-shot returns to its original neutral pose')
        self.assertEqual(frames[-2], frames[-1], 'cover settles after its one-time introduction')
        self.click(OK)
        self.click(UP)
        frames = []
        for t in (0, 200, 416, 499, 500, 800, 1166, 1167, 1500, 1666, 1667, 1800):
            self.lib.host_draw_at(6000 + t)
            self.check(f'map travel {t}')
            frames.append(self.snapshot())
        self.assertNotEqual(frames[0], frames[4])

    def test_every_grok_boot_frame_renders_with_native_caption_and_permanent_final_hold(self):
        self.new([0]*9);self.lib.host_boot_start(1000)
        frames=[];snapshots=[]
        for index in range(73):
            self.lib.host_draw_at(1000+index*1000//12);self.check(f'Grok frame{index}')
            frames.append(self.view_image());snapshots.append(hash(tuple(self.snapshot())))
        self.assertGreater(len(set(snapshots)),65)
        last=self.snapshot()
        stats=self.lib.ui_boot_video_stats()
        self.assertEqual((stats.frames,stats.skipped,stats.last_frame),(73,0,72))
        for elapsed in (6001,6599,6600,7000,12000,0x7fffffff):
            self.lib.host_draw_at(1000+elapsed);self.check(f'Grok held{elapsed}');self.assertEqual(self.snapshot(),last)
        frames[0].save(self.docs/'boot-v3-silent.gif',save_all=True,append_images=frames[1:],duration=[80 if i%3<2 else 90 for i in range(72)]+[600],loop=0,disposal=2)
        frames[-1].save(self.docs/'boot-6000.png')
        self.assertEqual(self.lib.ui_boot_video_stats().frames,73,'Repeated hold/full redraws must not count as new poses')

    def test_boot_after_a_slow_draw_submits_every_pose_and_full_redraw_is_stable(self):
        self.new([0]*9);self.lib.host_boot_start(1000)
        self.lib.host_draw_at(1000);self.check('first pose')
        # Simulate a delayed worker, then repeated immediate catch-up flushes.
        for index in range(1,73):
            self.lib.host_draw_at(10000+index);self.check(f'catch-up {index}')
            stats=self.lib.ui_boot_video_stats()
            self.assertEqual((stats.frames,stats.skipped,stats.last_frame),(index+1,0,index))

    def test_deferred_dma_fixture_detects_buffer_reuse_before_transfer_completion(self):
        self.assertEqual(self.lib.host_dma_selftest(),1)

    def test_random_inputs_never_leave_stale_pixels(self):
        self.new([0, 30, 700, 12, 11, 0, 0, 0, 0])
        state = 12345
        def rnd():
            nonlocal state
            state = (state * 1103515245 + 12345) & 0x7fffffff
            return state >> 8
        for i in range(700):
            v = rnd() % 100
            if v < 35: self.steps(1 + rnd() % 30)
            elif v < 37 and self.lib.host_page() == 6:
                self.lib.host_legacy(rnd() % 800); self.check('legacy')
            elif v < 65: self.ev(rnd() % 3, rnd() % 5)
            else: self.click(rnd() % 3)

    def test_gradient_band_dithers_between_rgb565_levels(self):
        self.lib.host_band(0x0841, 0x18e7)    # a dark, narrow ramp: the worst case for RGB565 bands
        pixels = self.snapshot()
        def level(v): return (v >> 11) * 2 + ((v >> 5) & 63) + (v & 31) * 2
        # What the eye sees: the mean of each 4-row block across the width.
        blocks = [sum(level(pixels[y * 240 + x]) for y in range(b, b + 4) for x in range(240)) / 960
                  for b in range(0, 320, 4)]
        for a, b in zip(blocks, blocks[1:]):
            self.assertGreaterEqual(b, a, 'the ramp must never step back')
        plain = {level(v) for v in pixels}
        self.assertGreater(len(set(blocks)), 3 * len(plain), 'dither should place shades between levels')

    def test_bitmap_clipping_movement_and_image_replacement(self):
        for x, y, alternate in [(-2, -1, 0), (238, 318, 0), (238, 318, 1), (500, 500, 0), (110, 90, 1)]:
            self.lib.host_bitmap(x, y, alternate, 0)
            incremental = self.snapshot()
            expected = [0x1357] * (240 * 320)
            for sy in range(4):
                for sx in range(4):
                    if 0 <= x + sx < 240 and 0 <= y + sy < 320:
                        index = sy * 4 + sx
                        expected[(y + sy) * 240 + x + sx] = 16 - index if alternate else index + 1
            self.assertEqual(incremental, expected)
            self.lib.host_bitmap(x, y, alternate, 1)
            self.assertEqual(incremental, self.snapshot())

    def test_all_six_one_person_items_render(self):
        self.assertEqual(self.lib.host_jump_reset(5), 1)
        for skin in range(6):
            self.lib.host_jump_item(2, skin)
            self.save(f'jump-item-{skin}.png')

    def test_incremental_jump_frame_matches_complete_frame(self):
        self.assertEqual(self.lib.host_jump_reset(5), 1)
        self.lib.host_jump_tick(10, 1)
        hold = self.lib.host_jump_hold()
        for _ in range(hold//10): self.lib.host_jump_tick(10, 0)
        self.lib.host_jump_tick(hold % 10, 2)
        for frame in range(100):
            self.lib.host_jump_tick(10, 0)
            incremental = self.snapshot()
            self.lib.host_jump_full()
            self.assertEqual(incremental, self.snapshot(), f'stale jump pixels at frame {frame}')
        self.save('jump.png', True)

    def _jump_throw(self, hold):
        self.lib.host_jump_tick(10, 1)
        for _ in range(hold // 10): self.lib.host_jump_tick(10, 0)
        self.lib.host_jump_tick(hold % 10, 2)
        for _ in range(160): self.lib.host_jump_tick(10, 0)

    def test_jump_charge_streak_and_over_card(self):
        # 2026-10-30 collection polish: perfect-streak label, medal pips, warm power bar and the game-over card.
        self.assertEqual(self.lib.host_jump_reset(5), 1)
        for _ in range(4): self._jump_throw(self.lib.host_jump_hold())
        self.assertGreaterEqual(self.lib.host_jump_score(), 12)
        self.lib.host_jump_tick(10, 1)
        for frame in range(45):
            self.lib.host_jump_tick(10, 0)
            incremental = self.snapshot(); self.lib.host_jump_full()
            self.assertEqual(incremental, self.snapshot(), f'stale charge pixels at frame {frame}')
        self.save('jump-charge.png', True)
        for _ in range(100): self.lib.host_jump_tick(10, 0)        # hold to the clamp: far overshoot
        self.lib.host_jump_tick(10, 2)
        for frame in range(160):
            self.lib.host_jump_tick(10, 0)
            incremental = self.snapshot(); self.lib.host_jump_full()
            self.assertEqual(incremental, self.snapshot(), f'stale over pixels at frame {frame}')
        self.save('jump-over.png', True)

if __name__ == '__main__':
    unittest.main(verbosity=2)
