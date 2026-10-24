#pragma once
// The nine map stations: the passport kiosk and eight games, bottom of the map to the top in
// ADV_PATH. Same table as STATION in game-art/adventure/prototype/adv_core.js.
#include <stdbool.h>
#include <stdint.h>
#include "adv_game.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ADV_STATIONS 9
#define ADV_KIOSK 0
#define ADV_START_STATION 1

typedef enum { ADV_KIND_KIOSK, ADV_KIND_LEGACY, ADV_KIND_SESSION } adv_kind_t;

typedef struct {
    const char *id, *cn, *en, *world, *resource;
    uint8_t kind;
    bool placeholder;           // runs the demo game with ADV_DEMO_THRESHOLDS for now
    uint32_t thresholds[3];     // bronze, silver, gold of the real game
    uint16_t color;             // RGB565 world colour (resource bar, labels)
    const adv_game_t *game;     // session games only
} adv_station_t;

extern const adv_station_t adv_station[ADV_STATIONS];
extern const uint8_t adv_path[ADV_STATIONS];
extern const uint32_t adv_demo_thresholds[3];

uint32_t adv_threshold(int station, int tier);
int adv_path_index(int station);

#ifdef __cplusplus
}
#endif
