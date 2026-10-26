#pragma once
// Fixed, packer-validated MPEG1 I/P boot media. No audio or file I/O.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef struct adv_video adv_video_t;
#define ADV_VIDEO_BAND_HEIGHT 16
#define ADV_VIDEO_BANDS 20
adv_video_t *adv_video_open(const uint8_t *data,size_t size,unsigned width,unsigned height);
void adv_video_close(adv_video_t *v);
bool adv_video_next(adv_video_t *v);
unsigned adv_video_frame(const adv_video_t *v); // zero-based; valid only after next
// Cumulative generations retain damage even when several frames are decoded before a draw.
uint32_t adv_video_band_generation(const adv_video_t *v,unsigned band);
size_t adv_video_reference_bytes(const adv_video_t *v);
// Paints into the renderer's current strip, using integer bilinear YCbCr sampling.
void adv_video_row(const void *video,int y,int x0,int x1,uint16_t *row);
