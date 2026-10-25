#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
// Pure, bounded decoders. Buffers are caller-owned; no allocation or rendering.
bool nabo_jump_decode_platform(const uint8_t *data,size_t bytes,unsigned skin,unsigned y,uint16_t *out,size_t capacity);
bool nabo_jump_decode_pcm_block(const uint8_t *data,size_t bytes,unsigned block,int16_t *out,size_t capacity);
