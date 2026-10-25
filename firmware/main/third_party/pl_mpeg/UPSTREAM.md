# PL_MPEG video decoder

Source: https://github.com/phoboslab/pl_mpeg/blob/master/pl_mpeg.h
Upstream downloaded SHA256: 3a8cb30c83c2a1147719c30fe0c8b93da2987aa43140077c575b39aaa75fc2c9

MIT license is retained at the beginning of pl_mpeg.h. The firmware links only the elementary video/buffer functions; no audio, demux, networking or file I/O is used.

Local `PLM_VIDEO_IP_ONLY` profile: two separately allocated YCbCr reference images instead of three, correct I/P buffer rotation, no floating point playback clock, allocation failure checks on the invoked constructors, and no discard/memmove on immutable fixed-memory streams. Its fixed immutable stream is validated as I/P-only by the packer; B frames and arbitrary external media are unsupported. Cadence and final hold use the firmware's integer millisecond clock. Both references are released on leaving the cover.
