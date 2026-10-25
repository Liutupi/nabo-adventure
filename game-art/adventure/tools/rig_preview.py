"""Fixed-anchor 48px exports, per-animation shared palettes, world contact sheets and GIFs."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rig_config import WORLDS


def hexrgb(value):
    return tuple(bytes.fromhex(value.lstrip('#')))


def quantize(frames, colours=63, protect_head=False):
    # Palette is shared across the entire loop. Index 0 is always transparent.
    samples = []
    for frame in frames:
        data = np.asarray(frame)
        opaque = data[:, :, 3] >= 128
        samples.extend(data[:, :, :3][opaque])
        if protect_head:
            # Spend palette entries on the immutable face/glasses/hat instead of
            # background or detailed jacket texture. This samples original RGB only.
            protected = opaque.copy()
            protected[104 if protect_head is True else int(protect_head):] = False
            samples.extend(data[:, :, :3][protected])
            samples.extend(data[:, :, :3][protected])
    cloud = np.array(samples, dtype=np.uint8).reshape((-1, 1, 3))
    palette_image = Image.fromarray(cloud, 'RGB').quantize(colors=colours, method=Image.Quantize.MEDIANCUT)
    palette = palette_image.getpalette()[:colours*3]
    palette_rgb = np.array(palette, dtype=np.int32).reshape((-1, 3))
    outputs, errors, head_errors = [], [], []
    for frame in frames:
        data = np.asarray(frame)
        opaque = data[:, :, 3] >= 128
        rgb = data[:, :, :3][opaque].astype(np.int32)
        nearest = []
        for start in range(0, len(rgb), 8192):
            distance = ((rgb[start:start+8192, None, :] - palette_rgb[None, :, :])**2).sum(axis=2)
            nearest.extend(distance.argmin(axis=1)+1)
        indices = np.zeros(data.shape[:2], dtype=np.uint8)
        indices[opaque] = nearest
        indexed = Image.fromarray(indices.astype(np.uint8), 'P')
        indexed.putpalette([0, 0, 0] + palette + [0]*(768-(colours+1)*3))
        indexed.info['transparency'] = 0
        rgba = indexed.convert('RGBA')
        mask = data[:, :, 3] >= 128
        delta = np.asarray(rgba)[:, :, :3].astype(float) - data[:, :, :3]
        errors.append(float(np.mean(np.abs(delta[mask]))))
        protected = mask.copy()
        protected[104 if protect_head is True else int(protect_head) if protect_head else frame.height:] = False
        head_errors.append(float(np.mean(np.abs(delta[protected]))))
        outputs.append(rgba)
    return outputs, {'palette_size_including_transparency': colours+1, 'alpha_threshold': 128,
                     'palette_rgb': [[0,0,0]]+palette_rgb.tolist(), 'palette_index_0_transparent': True,
                     'max_rgb_mean_absolute_error': max(errors), 'mean_rgb_absolute_error': sum(errors)/len(errors),
                     'head_rgb_mean_absolute_error': sum(head_errors)/len(head_errors),
                     'protected_head_sampling_weight': 3 if protect_head else 1}


def target_frames(frames):
    union = frames[0].getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    for frame in frames[1:]:
        union = Image.fromarray(np.maximum(np.asarray(union), np.asarray(frame.getchannel('A').point(lambda a: 255 if a >= 128 else 0))))
    bbox = union.getbbox()
    scale = 48 / (bbox[3]-bbox[1])
    width = round((bbox[2]-bbox[0])*scale)
    # All frames use one global crop and one scale; no per-frame recentering jitter.
    sampled = [f.crop(bbox).resize((width, 48), Image.Resampling.LANCZOS) for f in frames]
    ready, report = quantize(sampled)
    report.update({'global_animation_bbox': list(bbox), 'scale': scale, 'canvas': [width, 48],
                   'target_anchor': [round((128-bbox[0])*scale), 48],
                   'height_policy': '48px union silhouette envelope; individual gait poses may be shorter, fixed crop/scale/anchor across all frames'})
    return ready, report


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)


def previews(art, name, facing, raw_frames):
    folder = Path(art) / 'preview/travel'
    folder.mkdir(parents=True, exist_ok=True)
    frames, report = target_frames(raw_frames)
    target_dir = folder / 'targets48' / name
    target_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(target_dir / f'{i:03d}.png')
    # Shared two-world view, includes actual 48px and exact nearest-neighbor 3x.
    cellw, cellh = 104, 235
    sheet = Image.new('RGB', (cellw*8, cellh*2), 'white')
    draw = ImageDraw.Draw(sheet)
    gif_paths = []
    for row, (world, colour) in enumerate(WORLDS.items()):
        rgb = hexrgb(colour)
        draw.rectangle((0, row*cellh, sheet.width, (row+1)*cellh), fill=rgb)
        draw.text((8, row*cellh+5), f'{name} / {facing} / {world} / 48px + 3x', fill='white' if row else '#24354b', font=font(13))
        gif_frames = []
        for i, frame in enumerate(frames):
            x, y = i*cellw, row*cellh
            sheet.paste(frame, (x+(cellw-frame.width)//2, y+33), frame)
            enlarged = frame.resize((frame.width*3, 144), Image.Resampling.NEAREST)
            sheet.paste(enlarged, (x+(cellw-enlarged.width)//2, y+86), enlarged)
            gif = Image.new('RGB', (160, 180), rgb)
            gif.paste(enlarged, ((160-enlarged.width)//2, 18), enlarged)
            gif_frames.append(gif)
        gifpath = folder / f'{name}-{world}.gif'
        gif_frames[0].save(gifpath, save_all=True, append_images=gif_frames[1:], duration=[80, 80, 90, 80, 80, 90, 80, 90], loop=0, disposal=2)
        gif_paths.append(gifpath.relative_to(art).as_posix())
    sheetpath = folder / f'{name}-contact.png'
    sheet.save(sheetpath)
    # 256px technical animation is visible without magnifying the target pixels.
    tech_frames = []
    for frame in raw_frames:
        bg = Image.new('RGBA', frame.size, '#24354b')
        bg.alpha_composite(frame)
        tech_frames.append(bg.convert('RGB'))
    techpath = folder / f'{name}-rig.gif'
    tech_frames[0].save(techpath, save_all=True, append_images=tech_frames[1:], duration=[80, 80, 90, 80, 80, 90, 80, 90], loop=0, disposal=2)
    report.update({'contact_sheet': sheetpath.relative_to(art).as_posix(), 'world_gifs': gif_paths,
                   'world_colours': WORLDS, 'world_colour_source': 'firmware/main/adv_ui_map.c WORLD[2], WORLD[0]',
                   'technical_gif': techpath.relative_to(art).as_posix(), 'frames': len(frames), 'fps': 12,
                   'gif_duration_ms': 670, 'gif_timing_note': 'GIF centiseconds approximate 12fps; PNG timeline/manifest remains exactly 12fps'})
    return report
