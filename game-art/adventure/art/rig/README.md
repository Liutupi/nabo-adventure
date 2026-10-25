# Travel rig, rounds 2 and 4

The user selected **v2 option 1, light hiking**, on 2026-10-25. The other two outfits are not approved. The rejected v1 SVG face and its earlier false automated identity pass are not inputs to this package.

These SVGs are **wrappers around approved-image pixel slices**, not hand-drawn vector paths. `common/<facing>/head.svg` retains the whole source head, hair, cap and glasses. `expression_neutral.svg` is an unchanged same-source neutral facial overlay; no new eyelids or mouth have been drawn. All skins can reuse each facing's common head. Left and right originate from separate source views, with no mirroring.

`rig.json` locks the transparent source SHA256, source windows, sampling transforms, 256px canvas, pivots, parent relationships, drawing order, polygons, source-pixel overlap circles and eight periodic keyframes per loop. Every layer includes its raster PNG and an explicit binary `*-mask.png`. Joint overlap uses original source pixels; hidden anatomy has not been synthesized.

The source background-removal edit slightly changed the approved board and retains low-alpha fringe. See `source/travel-three-views-generation.json` and `source/travel-three-views-qa.json`. The rig only discards source alpha below 16, as authorized; source files and RGB stay unchanged. The final binary-alpha delivery uses threshold 128. This does not imply human acceptance of the source matte or new animation.

Rebuild and verify from the repository root with the bundled Python (Pillow + NumPy):

```powershell
& 'C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' game-art/adventure/tools/render_travel.py
& 'C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' game-art/adventure/tools/rig_atlas.py
& 'C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' game-art/adventure/tools/verify_travel.py
```

The stable entry point rebuilds the complete travel group together so its runtime scale, crop and palette cannot diverge. It accepts the earlier CLI flags for compatibility; canonical frames remain 256×256. The manifest preserves unrelated skins and references the separate shared-static manifest without modifying that package.

Outputs:

- `../frames/travel/masters/<anim>/`: lossless high-color RGBA masters, never discarded.
- `../frames/travel/<anim>/`: 256×256 RGBA delivery frames, one shared palette of 63 visible colors plus transparent index 0 per loop, binary alpha. These are the formal `manifest.frames` entries.
- `../frames/travel/runtime/<anim>/`: directly sampled from masters at 48/72/120px with explicit `runtime_frames`, `runtime_anchor` and `runtime_canvas` fields. All 48px clips share one crop, scale and palette. The 120px welcome uses 48 visible colors plus transparency to fit the UI cover palette. The earlier `preview/travel/targets48/` is superseded; use manifest runtime paths.
- `../preview/travel/`: source-versus-64-color comparisons, source and delivery technical GIFs, target-size GIFs and contact sheets on the exact town `#f6e2b4` and deep-sea `#061434` station grounds from `firmware/main/adv_ui_map.c`.

The contractual anchor remains **(128,224)**. Walking, idle, turns, sad and welcome keep core soles at y=224; cheer intentionally lifts the complete body at its hop apex. The 48px exports share a single union crop and scale across all related clips, so an individual pose can be shorter. No per-frame recentering is used.

Clips are idle8, walk_left8, walk_right8, cheer8 (72px), sad6 (48px), welcome16 (120px), and four six-frame facing transitions. The turns register the immutable source head slices at their eye midpoint, ease the premultiplied facing blend, and reuse the idle/walk endpoint frames exactly. They are deterministic source dissolves, not new 3D views. `idle-walk-continuity.gif` demonstrates both directions with eased root travel on one screen; `continuity-qa.json` records root, centroid, sole and head-frame differences.

`motion-quality.json` records actual self-repairs, including the discarded cheer neck-gap frame and repaired source-joint connection. Sad retains the original neutral face and communicates through a slump; welcome retains the original mouth and uses a small nod/invitation, not fabricated lip sync. `welcome-voice-preview.html` is a standalone host preview with the original WAV embedded read-only and WebAudio scheduling at 1.400s. The voice ends at 4.090625s. Two welcome cycles take 2.666667s, followed by a 23.958ms neutral hold. Firmware performs entry translation and still needs real-device timing validation.

`preview/travel/validation.json` records frame transitions, wrap difference, transforms, original color counts and quantization error. `verification.json` checks the actual saved files, embedded SVG pixels, source RGB, source SHA, binary alpha, shared color budget and exact target envelope. Full-size 64-color delivery visibly posterizes the original smooth illustration; the masters and comparison sheets preserve that difference. Hardware RLE packing, firmware integration, on-device motion and human visual acceptance are not claimed.
