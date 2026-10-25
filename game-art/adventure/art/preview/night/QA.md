# NIGHT host artwork review

Both `night_a` (indigo pajamas) and `night_b` (camping jacket) have the full seated set: idle 8, left/right scoot 4 each, catch 6, lift-jar 6, yawn 6, settlement cheer 8. Shared moth has 4 wing frames. There are 10 independent static resources (4 grass, 4 tree shadows, empty jar, separate engine-tinted glow). Fireflies, glow intensity, screen translation and gradients remain program operations.

The two wardrobe sheets are real built-in imagegen edits of the original NABO and approved hiker reference. Their generated heads are discarded. Final heads/neutral expression are copied from the frozen common front/left/right pixels with a NIGHT-local collar exclusion: rows below 93 retain only neck x121..137 through row100. No common file is edited. The resulting SVG parts embed inspectable PNG slices; these are not claimed to be hand-drawn vector paths. Source SHA/coordinates/alpha cleanup are in `rig/night/rig.json` and `games/night/source/generation.json`.

Source alpha below 16 is excluded before sampling; formal and runtime delivery use binary alpha threshold 128. Masters retain high-color RGBA. Each formal 256px action shares at most 63 visible colors plus transparent; runtime 56px actions share a fixed crop, scale, anchor and palette across the entire skin. Cheer uses its own 72px group. Runtime quantization samples masters directly, avoiding a second quantization of 256px deliverables. Exact quantization error and palette are in the manifest.

Actual frame/contact inspection found and repaired:

1. Initial affine sampling included a neighboring portrait. Each source view now has an explicit sampling window. The failed image is retained under `revisions/attempt1-view-window-bleed.png`.
2. Original hand partitions carried cut-out trouser pixels during raised-hand actions. Below the cuffs, only the original hand-skin pixels follow the hands; trouser fragments stay with the seated legs.
3. A small sleeve island in the torso layer rotated separately and floated near the waist. Deterministic connected-component reassignment attaches it to its original limb.
4. The resting hand occluded the knee. Lifting it exposed a hole. A low-variance fabric patch from that same source image now fills only the original hand coverage under the moving limb. The selected source rectangle and coverage formula are recorded. This is technical completion of hidden clothing, not a claim of original hidden-anatomy pixels.

All final action contacts and the combined actual-size/2x overview have been inspected. The head, hat and glasses remain recognizable against the actual NIGHT forest `#18303c`. Catch/lift reaches use a whole-upper-body lean, preserving the head and face together; the independent upright jar opening clears the head top at the peak. The forearm supports the jar from below near the peak. Yawn uses a hand-to-mouth gesture and a small nod with the original neutral mouth. Cheer is a seated friendly raised-arm celebration.

`night_a-continuity.gif` and `night_b-continuity.gif` show idle/action/idle in five lanes. All 56px action first/last runtime pixels equal neutral idle000 exactly. Scoots use the independently sourced left/right garments and head slices with eye-midpoint registration and premultiplied blending, never mirrored cap text. The program preview applies a separate eased 12px horizontal scoot. Four-frame blended turns have some mid-turn softness in the full-size source; this is disclosed rather than described as newly drawn 3D yaw. Feet/seat registration stays fixed; no per-frame resize/recenter occurs.

Independent saved-file checks cover source hashes, untouched common-head core, SVG/PNG pixel equality, binary alpha, per-animation shared colors, counts, loop wrap, neutral action endpoints and the raised jar collision point. Production C decoding was compared against indexed PNG input for 98 frames / 5,349 rows. Exact RLE + tables + estimated C3 descriptors: **215,853 bytes**, below the 260 KiB limit; final ELF alignment is not measured. `packing-validation.json` binds the exact manifest SHA and compiler command. Rebuild SHA evidence is in `reproducibility.json`.

These are host-rendered assets and host decoder checks. No user artwork approval or on-device visual acceptance is claimed.
