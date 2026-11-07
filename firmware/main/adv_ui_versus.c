// Versus room pages (lobby, invitations, countdown, result, notices) in the kiosk's paper style.
// The race itself is drawn by adv_ui_jump.c with the opponent overlay.
#include <stdio.h>
#include "adv_ui_internal.h"
#include "adv_vs.h"
#include "adv_stations.h"

#define SCENE_VERSUS 100

static void opp_name(const adv_vs_t *vs, char *out)
{
    if (vs->bot) snprintf(out, 12, "NABO");
    else adv_vs_name(vs->opp, out);
}

static const char *game_name(int s) { return s >= 1 && s <= 8 ? adv_station[s].cn : ""; }

// One line per game on the lobby: what "same course" means there.
static const char *const PITCH[9] = {"", "同一条路比谁跳得远", "同一片海比谁潜得深", "同一张时刻表比谁送得多",
                                     "同一片夜林比谁抓得多", "同一面岩壁比谁爬得高", "同一条雪道比谁滑得远",
                                     "同一片云层比谁飞得远", "同一次发射比谁飞得远"};

static void pick(ag_t *g, const adv_vs_t *vs)
{
    ui_header(g, "双人对战", "选游戏");
    for (int i = 0; i < 8; i++) {
        bool on = i == vs->pick;
        int y = 46 + i * 29;
        ui_card(g, 22, y, 196, 25, on, false);
        ag_text_top(g, &collection_font_16, game_name(i + 1), 120, y + 4, NT_ALIGN_CENTER, on ? UI_WHITE : UI_INK);
    }
    ui_footer(g, "上/下选择 · OK确认 · 双击上返回");
}

static void lobby(ag_t *g, const adv_vs_t *vs)
{
    char me[12], title[24];
    adv_vs_name(vs->me, me);
    snprintf(title, sizeof(title), "对战 · %s", game_name(vs->game));
    ui_header(g, title, me);
    ag_text(g, &collection_font_16, PITCH[vs->game], 120, 62, NT_ALIGN_CENTER, UI_INK);
    for (int i = 0; i <= vs->npeers; i++) {
        bool on = i == vs->cursor;
        int y = 76 + i * 40;
        ui_card(g, 22, y, 196, 34, on, false);
        uint16_t ink = on ? UI_WHITE : UI_INK;
        if (i == 0) {
            ag_text_top(g, &collection_font_16, "和 NABO 练习", 34, y + 8, NT_ALIGN_LEFT, ink);
            ag_text_top(g, &collection_font_12, "一块工牌", 206, y + 11, NT_ALIGN_RIGHT, ink);
        } else {
            char name[12];
            adv_vs_name(vs->peers[i - 1].mac, name);
            ag_text_top(g, &collection_font_16, name, 34, y + 8, NT_ALIGN_LEFT, ink);
            const adv_vs_peer_t *peer = &vs->peers[i - 1];
            char where[24];
            if (peer->busy) snprintf(where, sizeof(where), "对战中");
            else if (peer->game != vs->game) snprintf(where, sizeof(where), "在看%s", game_name(peer->game));
            else snprintf(where, sizeof(where), "可邀请");
            ag_text_top(g, &collection_font_12, where, 206, y + 11, NT_ALIGN_RIGHT, ink);
        }
    }
    int y = 76 + (vs->npeers + 1) * 40 + 22;
    if (!vs->radio) {
        ag_text(g, &collection_font_12, "无线没打开，只能和 NABO 练习", 120, y, NT_ALIGN_CENTER, UI_RED);
    } else if (!vs->npeers) {
        ag_text(g, &collection_font_12, "正在找附近的工牌…", 120, y, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_12, "对方也打开双人对战就能看到", 120, y + 18, NT_ALIGN_CENTER, UI_INK);
    }
    ui_footer(g, "OK确认 · 长按上换游戏 · 双击上返回");
}

static void card_page(ag_t *g, const char *title, const char *name, const char *line1, const char *line2, const char *footer)
{
    ui_header(g, "双人对战", NULL);
    ui_popup(g, 16, 70, 208, 190);
    ag_text(g, &collection_font_18, title, 120, 112, NT_ALIGN_CENTER, UI_INK);
    if (name) ag_text(g, &nabo_poster_font_28, name, 120, 158, NT_ALIGN_CENTER, UI_RED);
    if (line1) ag_text(g, &collection_font_16, line1, 120, 202, NT_ALIGN_CENTER, UI_INK);
    if (line2) ag_text(g, &collection_font_12, line2, 120, 230, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, footer);
}

static void countdown(ag_t *g, const adv_vs_t *vs, uint32_t ms)
{
    char name[12], num[4];
    opp_name(vs, name);
    snprintf(num, sizeof(num), "%d", adv_vs_countdown(vs, ms));
    char head[24], line[32];
    snprintf(head, sizeof(head), "%s对战", game_name(vs->game));
    ui_header(g, head, NULL);
    snprintf(line, sizeof(line), "你  VS  %s", name);
    ag_text(g, &collection_font_18, line, 120, 86, NT_ALIGN_CENTER, UI_INK);
    ag_circle(g, 120, 156, 44, UI_RED, 255, UI_INK, 2);
    ag_text(g, &nabo_poster_font_48, num, 120, 174, NT_ALIGN_CENTER, UI_WHITE);
    ag_text(g, &collection_font_16, PITCH[vs->game], 120, 230, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_12, "对手先结束，你超过他的分就赢", 120, 254, NT_ALIGN_CENTER, UI_INK);
    // Landscape games use UP as a play key, so double UP cannot mean "leave" there.
    ui_footer(g, vs->game == 1 ? "按住OK蓄力，松开起跳 · 双击上退出" : "横屏开局 · 长按下键退出对战");
}

static void result(ag_t *g, const adv_vs_t *vs)
{
    char name[12], a[12], b[12], tally[40];
    opp_name(vs, name);
    snprintf(a, sizeof(a), "%lu", (unsigned long)vs->mine.score);
    snprintf(b, sizeof(b), "%lu", (unsigned long)vs->theirs.score);
    snprintf(tally, sizeof(tally), "本次 %u胜 %u负 %u平", vs->wins, vs->losses, vs->draws);
    char head[24];
    snprintf(head, sizeof(head), "%s对战", game_name(vs->game));
    ui_header(g, head, NULL);
    ui_popup(g, 16, 46, 208, 230);
    const char *title = vs->outcome == VS_WIN ? "你赢了！" : vs->outcome == VS_LOSE ? "你输了" : "平局";
    ag_text(g, &collection_font_18, title, 120, 86, NT_ALIGN_CENTER, vs->outcome == VS_WIN ? UI_RED : UI_INK);
    ag_text(g, &collection_font_16, "你", 70, 122, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_16, name, 170, 122, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &nabo_poster_font_28, a, 70, 164, NT_ALIGN_CENTER, vs->outcome == VS_WIN ? UI_RED : UI_INK);
    ag_text(g, &nabo_poster_font_28, b, 170, 164, NT_ALIGN_CENTER, vs->outcome == VS_LOSE ? UI_RED : UI_INK);
    ag_text(g, &collection_font_16, ":", 120, 158, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_12, tally, 120, 200, NT_ALIGN_CENTER, UI_INK);
    const char *state = vs->bot ? "NABO 随时奉陪" : vs->opp_gone ? "对手已离开" : vs->want_again ? "等对手按 OK…" :
                        vs->they_again ? "对手想再来一局！" : "按 OK 邀请再来一局";
    ag_text(g, &collection_font_16, state, 120, 240, NT_ALIGN_CENTER, vs->they_again && !vs->want_again ? UI_RED : UI_INK);
    ui_footer(g, vs->opp_gone ? "下 回大厅" : "OK 再来一局 · 下 回大厅");
}

static void notice(ag_t *g, const adv_vs_t *vs)
{
    static const char *const text[] = {"", "对方没有回应", "对方拒绝了邀请", "对方正在对战", "对方取消了邀请",
                                       "连接断了", "对手退出了"};
    const char *sub = vs->note == VS_NOTE_LOST || vs->note == VS_NOTE_LEFT ? "本局不算胜负" : "可以再找别人试试";
    card_page(g, text[vs->note], NULL, sub, NULL, "OK 回大厅");
}

void ui_draw_versus(ag_t *g, const adv_vs_t *vs, uint32_t ms)
{
    ag_begin(g, SCENE_VERSUS + vs->page);
    ui_paper(g);
    char name[12];
    opp_name(vs, name);
    switch (vs->page) {
    case VS_LOBBY: lobby(g, vs); break;
    case VS_WAIT: card_page(g, "已发出邀请", name, "等对方按 OK 接受", "最多等 15 秒", "OK 取消邀请"); break;
    case VS_INVITED:
        if (vs->accepted) card_page(g, "接受了邀请", name, "马上开始…", NULL, "请稍候");
        else {
            char title[32];
            snprintf(title, sizeof(title), "邀请你玩%s", game_name(vs->game));
            card_page(g, title, name, PITCH[vs->game], NULL, "OK 接受 · 下 拒绝");
        }
        break;
    case VS_COUNTDOWN: countdown(g, vs, ms); break;
    case VS_RESULT: result(g, vs); break;
    case VS_NOTICE: notice(g, vs); break;
    case VS_PICK: pick(g, vs); break;
    default: break;
    }
}
