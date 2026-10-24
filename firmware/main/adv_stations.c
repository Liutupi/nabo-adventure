#include "adv_stations.h"
#include "adv_demo.h"

#define C565(r, g, b) ((uint16_t)(((r) >> 3) << 11 | ((g) >> 2) << 5 | (b) >> 3))

const uint32_t adv_demo_thresholds[3] = {3, 6, 10};
const uint8_t adv_path[ADV_STATIONS] = {2, 0, 1, 3, 4, 5, 6, 7, 8};

const adv_station_t adv_station[ADV_STATIONS] = {
    {"kiosk", "护照亭", "PASSPORT", "小镇", "", ADV_KIND_KIOSK, false, {0, 0, 0}, C565(240, 196, 92), 0},
    {"jump", "跳一跳", "JUMP", "小镇", "体力", ADV_KIND_LEGACY, false, {10, 25, 50}, C565(240, 150, 80), 0},
    {"dive", "深潜", "DIVE", "深海", "氧气", ADV_KIND_LEGACY, false, {100, 300, 600}, C565(80, 200, 230), 0},
    {"post", "小火车", "POST", "铁路平原", "蒸汽", ADV_KIND_SESSION, true, {5, 12, 25}, C565(230, 90, 70), &adv_demo_game},
    {"night", "萤火虫", "NIGHT", "夜林", "精神", ADV_KIND_SESSION, true, {15, 35, 60}, C565(200, 230, 90), &adv_demo_game},
    {"climb", "登山", "CLIMB", "雪山", "体力", ADV_KIND_SESSION, true, {50, 150, 300}, C565(150, 170, 200), &adv_demo_game},
    {"ski", "滑雪", "SKI", "雪坡", "体温", ADV_KIND_SESSION, true, {10, 25, 45}, C565(110, 170, 240), &adv_demo_game},
    {"sky", "热气球", "SKY", "云端", "热气", ADV_KIND_SESSION, true, {200, 500, 1000}, C565(250, 160, 190), &adv_demo_game},
    {"space", "太空", "SPACE", "太空", "燃料", ADV_KIND_SESSION, true, {300, 600, 900}, C565(170, 140, 250), &adv_demo_game},
};

uint32_t adv_threshold(int station, int tier)
{
    return adv_station[station].placeholder ? adv_demo_thresholds[tier] : adv_station[station].thresholds[tier];
}

int adv_path_index(int station)
{
    for (int i = 0; i < ADV_STATIONS; i++)
        if (adv_path[i] == station) return i;
    return -1;
}
