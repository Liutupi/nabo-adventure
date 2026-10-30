// G3 title/countdown/pause/results. The rules and scores remain in the model.
#include "adv_ui_cards.h"
#include <stdio.h>
LV_FONT_DECLARE(collection_font_26)
static const uint16_t INK = 0x18c5, GOLD = 0xfec9, PALE = 0xce7d;
static const char *const NAME[] = {"",         "",         "",         "邮政快车", "萤火虫之夜",
                                   "双线攀岩", "雪崩速降", "风层邮差", "火箭登月"};
static const char *const PITCH[] = {"",
                                    "",
                                    "",
                                    "不停车收发邮袋，快车分高，红灯要刹住",
                                    "挥罐抓萤火虫补光，别让罐子熄灭",
                                    "左右手交替抓点，断路和落石就换线",
                                    "过旗门做转体，别让雪崩追上",
                                    "乘对风层，把信投进邮筒",
                                    "点火、分离、奔月、着陆，关键时刻按中键"};
static const char *const KEYS[][3] = {{"", "", ""},
                                      {"", "", ""},
                                      {"", "", ""},
                                      {"◀ 刹车", "● 扔/抓邮袋", "▶ 加速"},
                                      {"◀ 慢走", "● 挥罐", "▶ 小跑"},
                                      {"◀ 左手", "● 换线", "▶ 右手"},
                                      {"◀ 左转", "● 跳/转体", "▶ 右转"},
                                      {"◀ 放气↓", "● 投信", "▶ 加热↑"},
                                      {"◀ 左移", "● 加速/时机", "▶ 右移"}};
static const char *const TIP[] = {"",
                                  "",
                                  "",
                                  "邮袋进了车门两边的括号就按中键",
                                  "抓萤火虫补光",
                                  "跟着黄圈里的箭头按左右",
                                  "雪崩从后面追来了",
                                  "右边箭头越长，那一层风越快",
                                  "准备发射"};
static const char *const MEDAL[] = {"铜章", "银章", "金章"};
void ui_v2_text(ag_t *g, const char *s, int x, int cy, int size, nt_align_t align, uint16_t color)
{
    const lv_font_t *font = size == 26   ? &collection_font_26
                            : size == 18 ? &collection_font_18
                            : size == 16 ? &collection_font_16
                                         : &collection_font_12;
    ag_text_top(g, font, s, x + 1, cy - size / 2 + 1, align, INK);
    ag_text_top(g, font, s, x, cy - size / 2, align, color);
}
static unsigned tier_mask(uint32_t score, int station)
{
    unsigned mask = 0;
    for (int i = 0; i < 3; i++)
        if (score >= adv_threshold(station, i))
            mask |= 1u << i;
    return mask;
}
static unsigned previous(const adv_model_t *m)
{
    return ((m->seen >> ((m->station - 1) * 3)) & 7u) | tier_mask(m->best_before, m->station);
}
static void medal(ag_t *g, int x, int y, int i, bool on, int radius)
{
    ag_circle(g, x, y, radius, on ? ui_tier_color(i) : 0x73ae, on ? 255 : 70, on ? 0xffff : PALE, 1);
    if (on)
        ag_rect(g, x - 2, y - 3, 2, 2, 0, 0xffff, 160, 0, 0);
}
void ui_v2_title(ag_t *g, const adv_model_t *m)
{
    int s = m->station;
    ag_rect(g, 0, 150, 320, 90, 0, INK, 148, 0, 0);
    ui_v2_text(g, NAME[s], 160, 46, 26, NT_ALIGN_CENTER, 0xffff);
    ui_v2_text(g, PITCH[s], 160, 76, 12, NT_ALIGN_CENTER, 0xffff);
    for (int i = 0; i < 3; i++) {
        int x = 60 + i * 100;
        ag_rect(g, x - 44, 165, 88, 22, 8, 0xffff, 40, 0, 0);
        ui_v2_text(g, KEYS[s][i], x, 176, 12, NT_ALIGN_CENTER, 0xffff);
    }
    unsigned mask = ((adv_earned(m) >> ((s - 1) * 3)) & 7u);
    for (int i = 0; i < 3; i++)
        medal(g, 274 + i * 16, 12, i, mask & (1u << i), 6);
    if (m->best[s]) {
        char str[32];
        snprintf(str, sizeof(str), "最佳 %u", (unsigned)m->best[s]);
        ui_v2_text(g, str, 264, 12, 12, NT_ALIGN_RIGHT, GOLD);
    }
    if (ui_millis() % 1000 < 700)
        ui_v2_text(g, "按 ● 开始", 160, 214, 12, NT_ALIGN_CENTER, 0xffff);
}
void ui_v2_ready(ag_t *g, const adv_model_t *m)
{
    char str[12];
    snprintf(str, sizeof(str), "%d", (m->t + 59) / 60);
    ui_number_tint(g, str, 36, 160, 86, NT_ALIGN_CENTER, 0xffff);
    ui_v2_text(g, TIP[m->station], 160, 134, 12, NT_ALIGN_CENTER, 0xffff);
}
void ui_v2_pause(ag_t *g)
{
    ag_rect(g, 0, 0, 320, 240, 0, INK, 200, 0, 0);
    ui_v2_text(g, "暂停", 160, 66, 26, NT_ALIGN_CENTER, 0xffff);
    static const char *const text[] = {"● 继续", "◀ 重来", "▶▶ 双击回地图"};
    for (int i = 0; i < 3; i++) {
        int y = 108 + i * 26;
        ag_rect(g, 96, y - 11, 128, 22, 8, 0xffff, 31, 0, 0);
        ui_v2_text(g, text[i], 160, y, 12, NT_ALIGN_CENTER, 0xffff);
    }
}
void ui_v2_result(ag_t *g, const adv_model_t *m, uint32_t ms, const char *cause, const char *line1,
                  const char *line2)
{
    unsigned frames = ms * 60 / 1000;
    unsigned alpha = frames < 30 ? frames * 194 / 30 : 194;
    ag_rect(g, 0, 0, 320, 240, 0, INK, (uint8_t)alpha, 0, 0);
    if (frames <= 20)
        return;
    unsigned t = frames - 20;
    if (t > 40)
        t = 40;
    uint32_t score = adv_game_status(m).score;
    // 64-bit intermediates bound the count-up even for long-lived records.
    uint32_t shown = (uint32_t)(((uint64_t)score * t * (80 - t) + 800) / 1600);
    ui_v2_text(g, cause, 160, 30, 12, NT_ALIGN_CENTER, PALE);
    char str[80];
    snprintf(str, sizeof(str), "%u", (unsigned)shown);
    ui_number_tint(g, str, 36, 160, 54, NT_ALIGN_CENTER, 0xffff);
    if (m->record && t == 40)
        ui_v2_text(g, m->test ? "测试不保存" : "新纪录!", 252, 54, 12, NT_ALIGN_CENTER, GOLD);
    unsigned before = previous(m), now = tier_mask(shown, m->station);
    for (int i = 0; i < 3; i++) {
        bool fresh = !(before & (1u << i)) && (now & (1u << i));
        int r = 7;
        if (fresh && frames >= 60 && frames < 80)
            r += (80 - frames) * 3 / 20;
        medal(g, 136 + i * 24, 108, i, (before | now) & (1u << i), r);
    }
    if (t == 40) {
        unsigned final = tier_mask(score, m->station), fresh = final & ~before;
        int target = -1;
        if (fresh) {
            for (int i = 0; i < 3; i++)
                if (fresh & (1u << i))
                    target = i;
            snprintf(str, sizeof(str), "拿到%s!", MEDAL[target]);
        } else {
            for (int i = 0; i < 3; i++)
                if (!((before | final) & (1u << i))) {
                    target = i;
                    break;
                }
            if (target >= 0)
                snprintf(str, sizeof(str), "离%s %u 分", MEDAL[target],
                         (unsigned)(adv_threshold(m->station, target) - score));
            else
                snprintf(str, sizeof(str), "三枚章都拿到了");
        }
        ui_v2_text(g, str, 160, 130, 12, NT_ALIGN_CENTER, fresh ? GOLD : PALE);
    }
    if (line1)
        ui_v2_text(g, line1, 160, 152, 12, NT_ALIGN_CENTER, 0xffff);
    if (line2)
        ui_v2_text(g, line2, 160, 168, 12, NT_ALIGN_CENTER, PALE);
    if (frames > 60 && ui_millis() % 1000 < 700)
        ui_v2_text(g, "● 再来一局", 160, 214, 12, NT_ALIGN_CENTER, 0xffff);
}

void ui_v2_hud(ag_t *g, const char *label, int res, uint32_t score, int combo, int mult)
{
    ag_rect(g, 0, 0, 320, 20, 0, INK, 190, 0, 0);
    ui_v2_text(g, label, 5, 10, 12, NT_ALIGN_LEFT, 0xffff);
    ag_rect(g, 42, 6, 66, 8, 0, 0xffff, 50, 0, 0);
    if (res > 0)
        ag_rect(g, 42, 6, 66 * res / 1000, 8, 0, res < 250 ? 0xfbaa : 0xfca9, 255, 0, 0);
    char line[40];
    if (combo >= 2) {
        snprintf(line, sizeof(line), "%d连 ×%d", combo, mult);
        ui_v2_text(g, line, 168, 10, 12, NT_ALIGN_CENTER, GOLD);
    }
    snprintf(line, sizeof(line), "%u", (unsigned)score);
    ui_v2_text(g, line, 314, 10, 16, NT_ALIGN_RIGHT, 0xffff);
}
