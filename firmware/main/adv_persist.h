#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "adv_model.h"

// Shared by the shell and the independently scheduled legacy dive task.
void adv_persist_set_test(bool enabled);
bool adv_persist_test(void);
void adv_persist_load(cg_settings_t *settings, uint32_t best[ADV_STATIONS], uint32_t *seen);
void adv_persist_restore(adv_model_t *model, uint32_t seed);
void adv_persist_u32(const char *key, uint32_t value);
void adv_persist_u8(const char *key, uint8_t value);
void adv_persist_settings(const cg_settings_t *settings);
void adv_persist_jump(uint32_t best);
