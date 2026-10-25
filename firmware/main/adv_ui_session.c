// Shell game sessions: title, the resource bar and score over the game, countdown, pause, end
// and result. Every shell game shares this frame; the game draws only its play field.
#include <stdio.h>
#include "adv_demo.h"
#include "adv_post.h"
#include "adv_ui_internal.h"
void ui_draw_post(ag_t *g,const adv_post_t *p);

static void draw_backdrop(ag_t *g, const adv_station_t *st)
{
    (void)st;
    ui_paper(g);
}

// Placeholder play field (adv_demo.c): the track, the zone and the marker.
static void draw_demo(ag_t *g, const adv_demo_t *d, const adv_station_t *st)
{
    ag_text(g, &collection_font_16, "占位关卡", 120, 108, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_12, "正式玩法和美术完成后替换", 120, 128, NT_ALIGN_CENTER, UI_DIM);
    int zx = 20 + (d->zc - d->zh) * 200 / 1000, zw = d->zh * 2 * 200 / 1000, mx = 20 + d->p * 200 / 1000;
    ag_rect(g, 16, 180, 208, 20, 10, UI_INK, 200, d->miss ? UI_RED : UI_PAPER, d->miss ? 2 : 1);
    ag_rect(g, zx, 182, zw, 16, 8, st->color, 230, 0, 0);
    if (d->hit) ag_glow(g, mx, 190, 26, UI_GOLD);
    ag_rect(g, mx - 3, 174, 6, 32, 3, UI_WHITE, 255, UI_INK, 1);
    ag_tri(g, mx, 214, 10, true, UI_WHITE);
    ag_text(g, &collection_font_12, "色块里按 OK 得分 · 按错扣四分之一", 120, 248, NT_ALIGN_CENTER, UI_INK);
}

static void draw_hud(ag_t *g, const adv_model_t *m)
{
    adv_status_t status = adv_game_status(m);
    const adv_post_t *post=m->station==3?m->game:NULL;
    ui_art(g, "ui/bars/top", 0, 0, 0);
    static const char *const icons[] = {"", "stamina", "oxygen", "steam", "spirit", "stamina", "temperature", "hot-air", "fuel"};
    char icon[64]; snprintf(icon, sizeof(icon), "ui/resources/icons/%s", icons[m->station]);
    if(!post||!post->practice)ui_art(g, icon, 0, 10, 8);
    ui_art(g, "ui/resources/bar-frame", 0, 36, 11);
    int w = status.resource * 124 / ADV_RESOURCE_MAX;
    if (w > 0) ag_rect(g, 38, 13, w, 6, 0, status.resource < ADV_RESOURCE_MAX / 4 ? UI_RED : ADV_ASSETS_UI_TEAL, 255, 0, 0);
    if(post&&post->practice) {
        ag_text_top(g,&collection_font_12,"练习",8,8,NT_ALIGN_LEFT,UI_WHITE);
        ag_text_top(g,&collection_font_16,post->lesson<2?"1/3":post->lesson<3?"2/3":"3/3",230,7,NT_ALIGN_RIGHT,UI_WHITE);
        return;
    }
    char score[16];
    if (status.score > 9999) snprintf(score, sizeof(score), "9999+");
    else snprintf(score, sizeof(score), "%u", (unsigned)status.score);
    ui_number_tint(g, score, 20, 230, 6, NT_ALIGN_RIGHT, UI_WHITE);
}

static void draw_title(ag_t *g, const adv_model_t *m, const adv_station_t *st, int s)
{
    ui_header(g, st->world, NULL);
    char wordmark[64];
    snprintf(wordmark, sizeof(wordmark), "ui/wordmarks/%s", st->id);
    ui_art(g, wordmark, 0, 20, 42);
    if (st->placeholder) {
        ui_art(g, "ui/labels/placeholder", 0, 76, 128);
    }
    if(s==3) {
        ag_text_top(g,&collection_font_12,"先看待送的第一封信",120,118,NT_ALIGN_CENTER,UI_INK);
        ag_text_top(g,&collection_font_12,"同色站前点OK送信",120,135,NT_ALIGN_CENTER,UI_INK);
        ag_text_top(g,&collection_font_12,"上下选轨 按住OK鸣笛",120,152,NT_ALIGN_CENTER,UI_INK);
        ag_text_top(g,&collection_font_12,"蒸汽空了结束 煤堆补汽",120,169,NT_ALIGN_CENTER,UI_INK);
        ag_rect(g,40,190,160,28,5,UI_INK,255,0,0);
        ag_text_top(g,&collection_font_16,"下键 分步练习",120,195,NT_ALIGN_CENTER,UI_WHITE);
    }
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(s, tier);
        ag_circle(g, x, s==3?236:182, s==3?9:18, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%u", (unsigned)adv_threshold(s, tier));
        ag_text(g, &nabo_mono_font_12, th, x, s==3?258:218, NT_ALIGN_CENTER, UI_INK);
    }
    char best[32];
    snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[s]);
    ag_text(g, s==3?&collection_font_16:&collection_font_18, best, 120, s==3?282:254, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, s==3?"OK直接开始 · 双击上回地图":"OK 开始 · 双击上 回地图");
}

static void draw_card(ag_t *g, int y, int h)
{
    ag_rect(g, 0, 34, 240, 286, 0, UI_INK, 150, 0, 0);
    ui_popup(g, 24, y, 192, h);
}

static void draw_result(ag_t *g, const adv_model_t *m, int s)
{
    adv_status_t status = adv_game_status(m);
    draw_card(g, 60, 200);
    ag_text(g, &collection_font_16, "本局成绩", 120, 88, NT_ALIGN_CENTER, UI_INK);
    char line[32];
    if (status.score > 9999) snprintf(line, sizeof(line), "9999+");
    else snprintf(line, sizeof(line), "%u", (unsigned)status.score);
    ui_number(g, line, 36, 120, 106, NT_ALIGN_CENTER);
    if (m->record) {
        ui_art(g, m->test ? "ui/labels/test-no-record" : "ui/labels/new-record", 0, m->test ? 72 : 84, 150);
    }
    snprintf(line, sizeof(line), "最佳 %u", (unsigned)m->best[s]);
    ag_text(g, &collection_font_16, line, 120, 194, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, s, 92, 226, 9, 28);
    ui_footer(g, "OK 再来一局 · 双击上 回地图");
}

void ui_draw_session(ag_t *g, const adv_model_t *m)
{
    if(m->station==4){ui_draw_night_session(g,m);return;}
    int s = m->station;
    if(s==3){ui_draw_post_session(g,m);return;}
    const adv_station_t *st = &adv_station[s];
    if (m->phase == ADV_TITLE) {
        ag_begin(g, UI_SCENE_TITLE);
        draw_backdrop(g, st);
        draw_title(g, m, st, s);
        return;
    }
    ag_begin(g, m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    draw_backdrop(g, st);
    if (st->game == &adv_demo_game) draw_demo(g, m->game, st);
    else if(st->game==&adv_post_game)ui_draw_post(g,m->game);
    draw_hud(g, m);
    if(m->phase==ADV_PLAY)ui_footer(g,"双击上回地图 · 长按上暂停");
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 120, 150, 50, UI_GOLD);
        ui_number(g, n, 36, 120, 132, NT_ALIGN_CENTER);
        ag_text(g, &collection_font_18, "准备", 120, 270, NT_ALIGN_CENTER, UI_INK);
    } else if (m->phase == ADV_END) {
        ag_rect(g, s==3?44:70, 136, s==3?152:100, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, s==3?"蒸汽耗尽":"结束", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
    } else if (m->phase == ADV_PAUSE) {
        draw_card(g, 80, 160);
        ag_text(g, &collection_font_18, "暂停", 120, 112, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "OK 继续", 120, 148, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "下 重新开始", 120, 178, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "双击上 回地图", 120, 208, NT_ALIGN_CENTER, UI_INK);
    } else if (m->phase == ADV_RESULT) draw_result(g, m, s);
}
