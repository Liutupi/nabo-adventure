// NIGHT V2「萤火虫之夜」screen, 320x240 clockwise landscape. Layout follows
// game-art/adventure/prototype/adv_night_draw.js; NABO uses the shared travel frames.
#include <stdio.h>
#include <stdlib.h>
#include "adv_night.h"
#include "adv_ui_internal.h"

#define GY ADV_NIGHT_GROUND
#define W 320
static const uint16_t SKY_TOP = 0x0844, SKY_LOW = 0x218D, PINE_FAR = 0x10C7, PINE_NEAR = 0x0866, GROUND = 0x08C3, GRASS = 0x1185;
static const uint16_t FLY = 0xC7EF, GOLD = 0xFE47, MOTH = 0x8C34, WARM = 0xFEAD, ROOT = 0x7A65, OWL_EYE = 0xFE69, PALE = 0xD71F;

static uint32_t hash(uint32_t n) { n = (n ^ 0x9e3779b9u) * 0x85ebca6bu; n ^= n >> 13; n *= 0xc2b2ae35u; return n ^ (n >> 16); }
static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{ ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color); }
static int sx_of(const adv_night_t *p, int world_px) { return world_px - (adv_night_cam(p) >> 8); }

// ---------- darkness: brightness falls off in six rings around the jar, then 1/8 outside ----------
typedef struct { int jx, jy, r; } dark_t;
static dark_t s_dark;
static int isqrt_(int v) { int r = 0, b = 1 << 14; while (b > v) b >>= 2; while (b) { if (v >= r + b) { v -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; } return r; }
static int span(int r, int dy2) { return dy2 < r * r ? isqrt_(r * r - dy2) : -1; }
static const uint8_t RING_PCT[6] = {50, 64, 77, 89, 100, 116}, RING_K[7] = {16, 13, 10, 8, 6, 4, 2};   // k/16 brightness
static void dark_span(uint16_t *row,int x0,int x1,int first,int last,unsigned k)
{
    if(first<x0)first=x0;
    if(last>x1)last=x1;
    if(first>=last)return;
    uint16_t *p=row+first-x0,*end=row+last-x0;
    // Power-of-two factors can shift all channels at once after masking the
    // cross-channel bits. Other factors retain the original exact rounding.
    if(k==2)while(p<end){*p=(uint16_t)((*p>>3)&0x18e3u);p++;}
    else if(k==4)while(p<end){*p=(uint16_t)((*p>>2)&0x39e7u);p++;}
    else if(k==8)while(p<end){*p=(uint16_t)((*p>>1)&0x7befu);p++;}
    else while(p<end){
        unsigned c=*p;
        *p++=(uint16_t)((((c>>11)*k>>4)<<11)|((((c>>5)&63)*k>>4)<<5)|((c&31)*k>>4));
    }
}
static void dark_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    const dark_t *d = ctx;
    int dy2 = (y - d->jy) * (y - d->jy), w[6];
    for (int i = 0; i < 6; i++) w[i] = span(d->r * RING_PCT[i] / 100, dy2);
    if(w[5]<0){dark_span(row,x0,x1,x0,x1,2);return;}
    int left=x0;
    for(int level=6;level>=1;level--){
        int end=d->jx-w[level-1];
        if(end>x1)end=x1;
        dark_span(row,x0,x1,left,end,RING_K[level]);
        if(end>left)left=end;
    }
    // Assign the centre pixel to the left half when the inner rings are absent.
    // This avoids applying darkness twice on tangent rows (width == -1).
    int right=d->jx+w[0]+1;
    if(right<d->jx+1)right=d->jx+1;
    if(right<x0)right=x0;
    for(int level=1;level<=6;level++){
        int end=level<6?d->jx+w[level]+1:x1;
        if(end>x1)end=x1;
        dark_span(row,x0,x1,right,end,RING_K[level]);
        if(end>right)right=end;
    }
}

static void pines(ag_t *g, int cam, int par256, int spacing, int base, int height, uint16_t color, uint32_t seed)
{
    int off = cam * par256 / 256, first = off / spacing - 1;
    for (int i = first; i < first + W / spacing + 3; i++) {
        uint32_t h = hash((uint32_t)i * 31u + seed);
        int x = i * spacing - off + (int)(h % (uint32_t)(spacing * 6 / 10)), s = height * (70 + (int)(h >> 8) % 60) / 100;
        ag_tri(g, x, base - s / 2, s > 250 ? 250 : s, true, color);
    }
}
static void scenery(ag_t *g, int cam)
{
    ag_band(g, 0, GY, SKY_TOP, SKY_LOW);
    pines(g, cam, 90, 38, 178, 62, PINE_FAR, 7);
    pines(g, cam, 154, 52, 198, 84, PINE_NEAR, 13);
    ag_rect(g, 0, GY - 4, W, 240 - GY + 4, 0, GROUND, 255, 0, 0);
    ag_rect(g, 0, GY - 4, W, 3, 0, GRASS, 255, 0, 0);
    int first = cam / 41 - 1;
    for (int i = first; i < first + W / 41 + 2; i++) {
        uint32_t h = hash((uint32_t)i * 7u);
        ag_rect(g, i * 41 - cam + (int)(h % 20), GY - 7 - (int)(h >> 9) % 4, 2, 5, 0, GRASS, 255, 0, 0);
    }
}
static void sky_after_dark(ag_t *g, int cam, uint32_t ms)
{
    for (int i = 0; i < 7; i++) {
        uint32_t h = hash((uint32_t)i + 99u);
        int x = (int)((h % 900u) + 900u - (uint32_t)(cam / 25) % 900u) % 900 - 290, y = (int)(h >> 12) % 110 + 4;
        if (x >= 0 && x < W && (ms / 400 + (uint32_t)i) % 5) ag_rect(g, x, y, 1, 1, 0, PALE, 255, 0, 0);
    }
    ag_glow(g, 232, 28, 24, 0x94B6);
    ag_circle(g, 232, 28, 11, 0xE75A, 255, 0, 0);
}

static void roots(ag_t *g, const adv_night_t *p)
{
    for (int i = 0; i < ADV_NIGHT_ROOTS; i++) {
        const adv_night_root_t *r = &p->roots[i];
        if (!r->state) continue;
        int x = sx_of(p, r->x);
        if (x < -30 || x > W + 30) continue;
        uint16_t c = r->state == 2 ? 0x5A04 : ROOT;
        ag_rect(g, x - r->w, GY - 4, r->w * 2, 4, 2, c, 255, 0, 0);
        ag_rect(g, x - r->w / 3, GY - 8, r->w / 2 + 2, 5, 2, c, 255, 0, 0);
    }
}

// Jar on a short pole; while swinging it sweeps the arc that really catches (net centre NET_DX/NET_DY).
static void nabo(ag_t *g, const adv_night_t *p, bool down_and_out, uint32_t ms)
{
    int x = p->screen >> 8, y = GY + 1, wx = p->x >> 8;
    const char *action = "travel/walk_right";
    unsigned frame = (unsigned)(wx / (p->gait == 2 ? 7 : 5)) % 8;
    if (down_and_out) { action = "travel/sad"; frame = ms / 133 > 5 ? 5 : ms / 133; }
    else if (p->stun > 0 && p->stun_kind == 1) { action = "travel/sad"; frame = 2; y += 2; }
    else if (p->stun > 0) { frame = 3; x += (p->stun / 2) % 2 ? 1 : -1; }
    int bob = !down_and_out && p->stun == 0 && p->gait == 2 && (wx / 5) % 2 ? -1 : 0;
    ag_rect(g, x - 10, y - 1, 22, 3, 1, 0x0000, 110, 0, 0);
    ui_art_frame_anchor(g, action, frame, x, y + bob);
    s_dark = (dark_t){x, y - 16, adv_night_radius(p)};
    if (down_and_out || (p->stun > 0 && p->stun_kind == 1)) return;
    int hx = x + 5, hy = y - 24 + bob, ang = -20 + adv_night_isin(wx * 5) * 5 / 4096, len = 18;
    if (p->swing > 0) {
        int age = ADV_NIGHT_SWING - p->swing;
        ang = age < ADV_NIGHT_SWING_ON ? -20 - age * 18 : -77 + (age - ADV_NIGHT_SWING_ON > 9 ? 9 : age - ADV_NIGHT_SWING_ON) * 118 / 9;
        len = 26;
        if (age >= ADV_NIGHT_SWING_ON) {
            bool on = age <= ADV_NIGHT_SWING_OFF;
            for (int k = 0; k < 6; k++) {
                int a = ang - k * 11;
                if (a < -77) break;
                ag_rect(g, hx + adv_night_isin(a + 64) * 30 / 4096 - 1, hy + adv_night_isin(a) * 30 / 4096 - 1, 3, 3, 1, 0xFF99, on ? 220 - k * 30 : 70, 0, 0);
            }
        }
    }
    int c = adv_night_isin(ang + 64), s = adv_night_isin(ang);
    for (int k = 1; k <= 3; k++) ag_rect(g, hx + c * len * k / 16384, hy + s * len * k / 16384, 2, 2, 0, 0x8B49, 255, 0, 0);
    int jx = hx + c * len / 4096, jy = hy + s * len / 4096;
    ag_rect(g, jx - 4, jy - 1, 8, 10, 2, 0xD75F, 120, 0xDF7F, 1);
    ag_rect(g, jx - 2, jy + 3, 4, 4, 0, WARM, (uint8_t)(110 + p->light / 7000), 0, 0);
    s_dark.jx = jx; s_dark.jy = jy + 4;
}

static void owls(ag_t *g, const adv_night_t *p, uint32_t ms)
{
    for (int i = 0; i < ADV_NIGHT_OWLS; i++) {
        const adv_night_owl_t *o = &p->owls[i];
        if (!o->live) continue;
        int tx = sx_of(p, o->tx >> 8), ox, oy;
        if (o->t > 0) {
            int k = 256 - o->t * 256 / ADV_NIGHT_OWL_WARN, rx = 24 - k * 8 / 256;
            bool pulse = (ms / (k > 170 ? 80 : 160)) % 2;
            ag_rect(g, tx - rx, GY + 1, rx * 2, 5, 2, 0, 0, pulse ? 0xFC4B : 0xC2A8, 2);
            if (o->t < 70) text(g, "!", tx, GY - 26 - (pulse ? 3 : 0), 16, NT_ALIGN_CENTER, 0xFC4B);
        }
        if (o->t > 60) continue;
        if (o->t > 30) { int k = 60 - o->t; ox = tx + 160 - k * 100 / 30; oy = -20 + k * 70 / 30; }
        else if (o->t > 0) { int k = 30 - o->t; ox = tx + 60 - k * 2; oy = 50 + k * k * (GY - 72) / 900; }
        else { ox = tx + o->t * 4; oy = GY - 22 + o->t * 4; }
        int wing = (ms / 90) % 2 ? 4 : -2;
        ag_tri(g, ox - 13, oy - 2 + wing, 12, false, 0x0021);
        ag_tri(g, ox + 13, oy - 2 + wing, 12, false, 0x0021);
        ag_circle(g, ox, oy, 9, 0x0021, 255, 0, 0);
        ag_rect(g, ox - 5, oy - 5, 3, 3, 0, OWL_EYE, 255, 0, 0);
        ag_rect(g, ox + 2, oy - 5, 3, 3, 0, OWL_EYE, 255, 0, 0);
    }
}

static void bugs(ag_t *g, const adv_night_t *p, uint32_t ms)
{
    int drawn = 0;
    for (int i = 0; i < ADV_NIGHT_FLIES && drawn < 22; i++) {
        const adv_night_fly_t *f = &p->flies[i];
        if (!f->type) continue;
        int x = sx_of(p, f->x >> 8), y = adv_night_fly_y(f, p->tick);
        if (x < -10 || x > W + 10) continue;
        drawn++;
        bool tw = (ms / 140 + (uint32_t)i) % 3 != 0;
        if (f->type == 2) { ag_glow(g, x, y, tw ? 13 : 11, GOLD); ag_rect(g, x - 2, y - 2, 4, 4, 1, 0xFFF6, 255, 0, 0); }
        else ag_glow(g, x, y, tw ? 7 : 6, FLY);
    }
    for (int i = 0; i < ADV_NIGHT_MOTHS; i++) {
        const adv_night_moth_t *m = &p->moths[i];
        if (!m->rr) continue;
        int x = sx_of(p, m->x >> 8), y = m->y >> 8;
        if (x < -8 || x > W + 8) continue;
        bool flap = (ms / 60 + (uint32_t)i) % 2;
        ag_rect(g, x - (flap ? 5 : 3), y - (flap ? 3 : 0), flap ? 10 : 6, 3, 1, MOTH, 255, 0, 0);
    }
}

static void effects(ag_t *g, const adv_night_t *p)
{
    static const char *const EVENT_NAME[] = {"", "萤火虫潮！", "猫头鹰出没", "起风了"};
    static const char *const EVENT_HINT[] = {"", "快跑起来多抓", "看地上的光圈，变速躲开", "虫群往回飘"};
    char s[32];
    for (int i = 0; i < ADV_NIGHT_FX; i++) {
        const adv_night_fx_t *e = &p->fx[i];
        if (!e->kind) continue;
        int x = sx_of(p, e->x), rise = e->t / 2;
        switch (e->kind) {
        case NIGHT_FX_FLY: case NIGHT_FX_GOLD:
            snprintf(s, sizeof(s), "+%d", (int)e->val);
            text(g, s, x, e->y - 14 - rise, 12, NT_ALIGN_CENTER, e->kind == NIGHT_FX_GOLD ? GOLD : 0xE7F8); break;
        case NIGHT_FX_MULTI: snprintf(s, sizeof(s), "一网 %d 只！", (int)e->val); text(g, s, x, e->y - rise, 16, NT_ALIGN_CENTER, 0xFF0F); break;
        case NIGHT_FX_MOTH: text(g, "飞蛾！罐子暗了", x, e->y - 20 - rise / 2, 12, NT_ALIGN_CENTER, 0xCDDF); break;
        case NIGHT_FX_TRIP: text(g, "绊倒！", x, e->y - rise / 2, 16, NT_ALIGN_CENTER, 0xFCCD); break;
        case NIGHT_FX_OWL: text(g, "被猫头鹰吓到！", x, e->y, 12, NT_ALIGN_CENTER, 0xFCCD); break;
        case NIGHT_FX_NEAR: text(g, "好险！", x, e->y - rise / 2, 16, NT_ALIGN_CENTER, 0x9F5F); break;
        case NIGHT_FX_BURST: if (e->t < 24) ag_rect(g, 0, 0, W, 240, 0, 0xFFDB, (uint8_t)(180 - e->t * 7), 0, 0); break;
        case NIGHT_FX_EVENT:
            if (e->val < 1 || e->val > 3) break;
            ag_rect(g, 0, 76, W, 44, 0, UI_INK, 170, 0, 0);
            text(g, EVENT_NAME[e->val], 160 + (e->t < 10 ? (10 - e->t) * 20 : 0), 80, 18, NT_ALIGN_CENTER, 0xFF0F);
            text(g, EVENT_HINT[e->val], 160, 102, 12, NT_ALIGN_CENTER, 0xD71F); break;
        default: break;
        }
    }
}

static void hud(ag_t *g, const adv_night_t *p, uint32_t ms)
{
    int pct = p->light / 10000, need = adv_night_meter_full(p), m = p->meter >= need ? 76 : p->meter * 76 / need;
    uint16_t col = pct > 45 ? 0xFF0F : pct > 20 ? 0xFD68 : 0xFB49;
    bool blink = pct < 20 && (ms / 170) % 2;
    ag_rect(g, 6, 6, 108, 28, 6, UI_INK, 150, 0, 0);
    ag_rect(g, 13, 11, 12, 17, 3, 0, 0, 0xCF1F, 1);
    ag_rect(g, 15, 27 - 14 * pct / 100, 8, 14 * pct / 100, 0, col, blink ? 90 : 255, 0, 0);
    ag_rect(g, 31, 13, 76, 7, 0, 0x3186, 255, 0, 0);
    if (pct) ag_rect(g, 31, 13, 76 * pct / 100, 7, 0, col, 255, 0, 0);
    ag_rect(g, 31, 23, 76, 5, 0, 0x2124, 255, 0, 0);
    if (m) ag_rect(g, 31, 23, m, 5, 0, p->meter >= need && (ms / 130) % 2 ? 0xFFFF : 0x7E5F, 255, 0, 0);
    if (p->meter >= need) text(g, "双击中键放光", 60, 38, 12, NT_ALIGN_CENTER, 0xBF9F);
    char s[24];
    snprintf(s, sizeof(s), "%u", (unsigned)p->score);
    text(g, s, 312, 4, 18, NT_ALIGN_RIGHT, 0xFFB9);
    if (p->combo >= 2) {
        int mu = adv_night_mult(p);
        if (mu > 1) snprintf(s, sizeof(s), "%d连 ×%d", (int)p->combo, mu); else snprintf(s, sizeof(s), "%d连", (int)p->combo);
        text(g, s, 312, 28, 12, NT_ALIGN_RIGHT, mu > 1 ? GOLD : 0xD71F);
    }
}

static void world(ag_t *g, const adv_night_t *p, bool out, uint32_t ms)
{
    int cam = adv_night_cam(p) >> 8;
    scenery(g, cam); roots(g, p); nabo(g, p, out, ms);
    ag_rows(g, dark_row, &s_dark, (uint32_t)(s_dark.jx * 977 + s_dark.jy * 31 + s_dark.r));
    sky_after_dark(g, cam, ms);
    ag_glow(g, s_dark.jx, s_dark.jy, 18 + p->light / 40000, WARM);
    owls(g, p, ms); bugs(g, p, ms);
}

static void panel(ag_t *g, int y, int h) { ag_rect(g, 56, y, 208, h, 8, UI_INK, 235, UI_GOLD, 1); }

static void title(ag_t *g, const adv_model_t *m, uint32_t ms)
{
    int cam = (int)(ms * 36 / 1000);
    scenery(g, cam);
    ui_art_frame_anchor(g, "travel/walk_right", ms / 83 % 8, 70, GY + 1);
    s_dark = (dark_t){80, GY - 22, 120};
    ag_rows(g, dark_row, &s_dark, 1);
    sky_after_dark(g, cam, ms);
    ag_glow(g, 80, GY - 22, 26, WARM);
    for (int i = 0; i < 9; i++) {
        uint32_t h = hash((uint32_t)i * 3u + 5u);
        int x = (int)((uint32_t)(i * 47) + ms * (20 + h % 25) / 1000) % (W + 20) - 10, y = 60 + (int)(h >> 10) % 90 + adv_night_isin((int)(ms / 30) + i * 40) * 10 / 4096;
        ag_glow(g, x, y, 6, FLY);
    }
    char best[32];
    snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[4]);
    text(g, best, 312, 6, 12, NT_ALIGN_RIGHT, GOLD);
    text(g, "萤火虫之夜", 196, 34, 18, NT_ALIGN_CENTER, 0xFF97);
    text(g, "左键 慢走 · 中键 挥罐 · 右键 小跑", 196, 66, 12, NT_ALIGN_CENTER, UI_WHITE);
    text(g, "光会越来越暗，抓萤火虫补光", 196, 88, 12, NT_ALIGN_CENTER, 0xD71F);
    text(g, "金色值5倍 · 别网飞蛾 · 跑时当心树根", 196, 108, 12, NT_ALIGN_CENTER, 0xD71F);
    text(g, "能量满了双击中键放光", 196, 128, 12, NT_ALIGN_CENTER, 0xD71F);
    if ((ms / 500) % 3) text(g, "中键开始", 196, 160, 16, NT_ALIGN_CENTER, UI_WHITE);
    text(g, "长按中键暂停 · 双击上键回地图", 160, 222, 12, NT_ALIGN_CENTER, 0x9CF3);
}

static void result(ag_t *g, const adv_model_t *m, const adv_night_t *p, uint32_t since)
{
    static const char *const CAUSE[] = {"罐子的光慢慢熄了", "一路狂奔，光晃没了", "挥空太多，光洒光了", "飞蛾扑灭了罐子", "绊了一跤，光灭了", "被猫头鹰吓灭了光"};
    world(g, p, true, since);
    ag_rect(g, 0, 0, W, 240, 0, 0x0001, 190, 0, 0);
    text(g, CAUSE[p->last_loss >= 0 && p->last_loss < NIGHT_LOSS_N ? p->last_loss : 0], 160, 18, 12, NT_ALIGN_CENTER, 0x9DBD);
    char s[64];
    snprintf(s, sizeof(s), "%u", (unsigned)p->score);
    ui_number_tint(g, s, 36, 160, 40, NT_ALIGN_CENTER, 0xFF97);
    if (m->record) text(g, m->test ? "测试不保存" : "新纪录！", 250, 46, 12, NT_ALIGN_CENTER, GOLD);
    snprintf(s, sizeof(s), "抓到 %d 只 · 最长 %d 连 · 放光 %d 次", (int)p->caught, (int)p->max_combo, (int)p->bursts);
    text(g, s, 160, 92, 12, NT_ALIGN_CENTER, 0xD71F);
    unsigned frame = since / 83 > 7 ? 7 : since / 83;
    ui_art_frame_anchor(g, "travel/cheer", frame, 160, 196);
    snprintf(s, sizeof(s), "最佳 %u", (unsigned)m->best[4]);
    text(g, s, 160, 200, 12, NT_ALIGN_CENTER, UI_WHITE);
    text(g, "中键重玩 · 双击上键回地图", 160, 222, 12, NT_ALIGN_CENTER, 0x9CF3);
}

void ui_draw_night_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    uint32_t ms = ui_millis();
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ms; }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m, ms); return; }
    const adv_night_t *p = m->game;
    if (m->phase == ADV_RESULT) { result(g, m, p, ms - phase_started); return; }
    world(g, p, m->phase == ADV_END, ms - phase_started);
    if (m->phase == ADV_PAUSE) {
        panel(g, 58, 124);
        text(g, "暂停", 160, 68, 18, NT_ALIGN_CENTER, UI_WHITE);
        text(g, "中键继续", 160, 100, 16, NT_ALIGN_CENTER, UI_GOLD);
        text(g, "左键重新开始", 160, 128, 12, NT_ALIGN_CENTER, UI_WHITE);
        text(g, "双击上键回地图", 160, 150, 12, NT_ALIGN_CENTER, UI_WHITE);
        return;
    }
    effects(g, p); hud(g, p, ms);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 160, 104, 34, UI_GOLD); ui_number(g, n, 36, 160, 86, NT_ALIGN_CENTER);
        text(g, "罐子的光会变暗，抓萤火虫补光", 160, 140, 12, NT_ALIGN_CENTER, 0xD71F);
    } else if (m->phase == ADV_END) { panel(g, 80, 44); text(g, "光灭了", 160, 90, 18, NT_ALIGN_CENTER, UI_WHITE); }
}
