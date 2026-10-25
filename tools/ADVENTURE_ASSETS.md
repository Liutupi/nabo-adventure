# Adventure runtime asset packing

Run from the repository root:

```powershell
$env:CC='D:\nabo-passport-tools\w64devkit\bin\gcc.exe'
python tools/build_adventure_assets.py --verify-c
```

Integrated game groups (pass both `--group X --integrated-game X`): `post`, `night`, `climb`. Firmware regeneration command: `python tools/build_adventure_assets.py --group travel --group ui --group static --group post --group night --group climb --integrated-game post --integrated-game night --integrated-game climb --verify-c`. Generated files are always written with CRLF so every host produces the same bytes.

Default groups are `travel`, `ui`, and `static`; repeat `--group` to select a subset. `--art` and `--output` support isolated test/CI directories. The default output is `firmware/main/generated/`. The script does not modify CMake, handwritten firmware, the art manifests, device state or private data.

## Input contracts

- `travel` reads `art/manifest.json` and requires each animation's explicit `runtime_frames`, `runtime_sha256`, `runtime_canvas`, `runtime_anchor`, `fps`, and `loop`. It does not guess paths or substitute 256px delivery frames/masters.
- `ui` reads `art/ui/ui-manifest.json`; only explicit `pack:true` assets are included. Every item's `size`, `color_limit`, and SHA256 is checked. Shared UI pixels must fit the declared merged palette of at most 32 entries including transparency. Preview composites, editable nine-slice atlases and the static cover-character reference remain excluded.
- `static` reads `art/shared-static-manifest.json`, using each stable id, PNG path, size, anchor, color limit and SHA256.

All source pixels must have alpha 0 or 255, and each sprite family has at most 63 visible colors plus transparent index zero. The existing `generate_adv_sprites.py` supplies `index_frames`, `pack`, `decode`, and `generate`; no second compression format is introduced. Comparison is exact against shared RGB565-indexed source pixels. Source PNG hashes and manifest hashes are recorded separately from temporary derived fragment PNG hashes.

A logical image may exceed the decoder's 256px side limit. The packer crops it into native pieces no larger than 256×256 and preserves every piece's x/y offset. For example, 240×320 becomes 240×256 at (0,0) and 240×64 at (0,256). No image rescaling occurs. Explicit `draw_offset` from an already split UI asset is retained.

## Stable C catalog

Include `generated/adv_assets_catalog.h`:

```c
const adv_asset_record_t *asset = adv_assets_find("travel/welcome");
// asset: id, pieces, piece_count, width, height, anchor_x, anchor_y, fps, loop
// piece: const adv_sprite_t *sprite; int16_t x, y;
```

For an animation drawn with its foot at (anchor_x, anchor_y), draw each piece at:

```text
x = desired_anchor_x - asset->anchor_x + piece->x
y = desired_anchor_y - asset->anchor_y + piece->y
```

Looped animations wrap their frame index. Nonloop animations must clamp at their last frame or explicitly transition to a compatible next animation; the catalog never silently turns them into loops. Playback state and audio synchronization belong to the caller.

Resource ids:

- Animations: `<skin>/<name>`, for example `travel/idle`, `travel/welcome`, `travel/turn_front_from_right`.
- UI: `ui/<PNG-relative-path-without-extension>`, for example `ui/bars/top`, `ui/wordmarks/collection`, `ui/cover-background-bottom`.
- Shared static: `static/<manifest-id>`, for example `static/landmark/kiosk` or `static/tiles/deep-sea/seaweed`.

Every fragment also exports an immutable `const adv_sprite_t` under a sanitized `adv_assets_...__pN` symbol. `adv_assets_find(NULL)` and an unknown id return NULL.

Six exported patches use row-major native parts (`top-left`, `top`, `top-right`, `left`, `center`, `right`, `bottom-left`, `bottom`, `bottom-right`):

```text
adv_assets_patch_menu_normal
adv_assets_patch_menu_selected
adv_assets_patch_menu_disabled
adv_assets_patch_info_normal
adv_assets_patch_info_current
adv_assets_patch_popup_normal
```

`adv_assets_digits_20[12]` and `adv_assets_digits_36[12]` contain glyph byte, pointer to its catalog record, and advance. Glyph order follows the manifest; identify the glyph byte rather than assuming a numeric-only array. `adv_assets_ui_palette`/`adv_assets_ui_palette_count` expose RGB565 colors, and `ADV_ASSETS_UI_INK`, `ADV_ASSETS_UI_PAPER`, etc. preserve named theme roles.

## Verification and safe publication

All manifests, source hashes, target dimensions, binary alpha and color limits are validated before creating the staging package. The existing Python decoder checks every encoded frame. With `--verify-c`, the script compiles the real generated C together with production `adv_sprite.c` and `adv_ninepatch.c`, compares every frame row's decoded indices, and verifies each generated ninepatch at 48×32 and 240×120 against native tile pixels.

The UI's actual RLE streams and tables, plus explicit C3 descriptor/catalog estimates, must stay at or below 160 KiB. Failure, source changes during packing, or C verification failure leaves the previous effective generated package untouched. Only after those checks does the script publish staged files. The former `adv_assets_generated.json` ownership list is the only authority for removing obsolete generated files; unrelated or unowned files are not deleted or overwritten.

`adv_assets_generated.json` records source SHA256 values, fragments and offsets, animation metadata, Python/C comparison counts, per-group stream/table bytes, and the generated file ownership list. Stream/table lengths are exact; C3 structure sizes are estimates based on 32-bit pointers. Linker padding, merging and final ELF/Flash occupancy still require build/map measurement. Host packing success is not device or artwork acceptance.

High-value regressions:

```powershell
python -m unittest discover -s tests -p test_adventure_assets.py -v
```

They cover actual generated C decode, large-image splitting, animation anchors, native ninepatch rendering, required runtime contracts, hash/dimension/alpha/palette rejection, C-identifier safety, budget refusal preserving the existing package, and cleanup confined to explicitly owned files.
