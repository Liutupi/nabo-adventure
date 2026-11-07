// 双人对战（八款游戏通用）：选游戏、大厅、邀请、同种子倒数、比分与胜负。纯C，不依赖ESP-IDF，宿主可测。
// 无线只负责搬运44字节定长包（adv_link）；本模型决定发什么、何时判胜负。
// 规则：两台用同一种子，赛道完全相同，各跳各的。双方都掉下去后比分高者胜；
// 一方先掉下去，另一方只要分数超过他就立即获胜（不用陪着一直跳）。同分为平局。
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "nabo_jump_model.h"

enum { ADV_VS_PACKET = 44, ADV_VS_PEERS = 4, ADV_VS_OUTBOX = 6, ADV_VS_VERSION = 1 };
// 按键编号与 adv_model.h 一致：上/下/OK；事件：按下/单击/双击/长按/松开。
enum { ADV_VS_UP, ADV_VS_DOWN, ADV_VS_OK };
enum { ADV_VS_PRESS, ADV_VS_CLICK, ADV_VS_DOUBLE, ADV_VS_LONG, ADV_VS_RELEASE };

// VS_PICK 放在最后，前面的编号与旧版一致（串口状态与测试沿用）。
typedef enum { VS_LOBBY, VS_WAIT, VS_INVITED, VS_COUNTDOWN, VS_PLAY, VS_RESULT, VS_NOTICE, VS_PICK } adv_vs_page_t;
typedef enum { VS_PENDING, VS_WIN, VS_LOSE, VS_DRAW } adv_vs_outcome_t;
typedef enum {
    VS_NOTE_NONE, VS_NOTE_NO_ANSWER, VS_NOTE_DECLINED, VS_NOTE_BUSY, VS_NOTE_CANCELLED, VS_NOTE_LOST, VS_NOTE_LEFT
} adv_vs_note_t;
enum {
    VS_FX_REDRAW = 1,
    VS_FX_START = 2,     // 用 vs->seed 重置双方跳一跳（倒数开始时）
    VS_FX_GO = 4,        // 倒数结束，开跳
    VS_FX_END = 8,       // 本局出结果
};
// 包类型
enum { VS_MSG_HELLO = 1, VS_MSG_INVITE, VS_MSG_CANCEL, VS_MSG_ACCEPT, VS_MSG_DECLINE, VS_MSG_START, VS_MSG_STATE,
       VS_MSG_AGAIN, VS_MSG_BYE };

typedef struct { uint32_t score; uint16_t steps; bool over; } adv_vs_side_t;
typedef struct { uint8_t mac[6]; uint32_t seen; bool busy; uint8_t game; } adv_vs_peer_t;
typedef struct { uint8_t to[6]; uint8_t data[ADV_VS_PACKET]; } adv_vs_out_t;

typedef struct adv_vs_t {
    adv_vs_page_t page;
    adv_vs_note_t note;
    bool radio, bot, host, accepted, want_again, they_again, opp_gone, start_acked;
    uint8_t me[6], opp[6];
    adv_vs_peer_t peers[ADV_VS_PEERS];
    int npeers, cursor;              // cursor 0 = 和 NABO 练习，1..npeers = 附近工牌
    uint8_t game;                    // 站点编号 1..8（1 = 跳一跳）
    int pick;                        // 选游戏页光标 0..7
    uint32_t session, seed, rng;
    uint32_t page_at, hello_at, state_at, heard_at, go_at, resend_at;
    adv_vs_side_t mine, theirs, sent;
    adv_vs_outcome_t outcome;
    uint16_t seq;
    uint16_t wins, losses, draws;    // 本次进入对战以来
    adv_vs_out_t out[ADV_VS_OUTBOX];
    int nout;
} adv_vs_t;

// game = 0 先进选游戏页；1..8 直接进该游戏的大厅。
void adv_vs_init(adv_vs_t *vs, const uint8_t me[6], bool radio, uint32_t rng, uint32_t now, int game);
int adv_vs_key(adv_vs_t *vs, int button, int event, uint32_t now);
int adv_vs_packet(adv_vs_t *vs, const uint8_t mac[6], const uint8_t *data, int len, uint32_t now);
// 每帧调用；mine 为本机跳一跳当前状态（倒数前传全0）。
int adv_vs_tick(adv_vs_t *vs, uint32_t now, adv_vs_side_t mine);
// 陪练模式下由 NABO 机器人提供对手状态。
void adv_vs_opponent(adv_vs_t *vs, adv_vs_side_t theirs, uint32_t now);
bool adv_vs_pop(adv_vs_t *vs, adv_vs_out_t *out);
void adv_vs_leave(adv_vs_t *vs);   // 离开对战：排队一个 BYE
// 3/2/1，开跳后为0
int adv_vs_countdown(const adv_vs_t *vs, uint32_t now);
void adv_vs_name(const uint8_t mac[6], char out[12]);   // "NABO-A958"
// 宿主测试用：构包/校验
void adv_vs_encode(uint8_t out[ADV_VS_PACKET], int type, const uint8_t to[6], uint32_t session, uint32_t seed,
                   adv_vs_side_t side, bool busy, uint16_t delay, uint16_t seq, uint8_t game);
bool adv_vs_valid(const uint8_t *data, int len);

// ---------- NABO 陪练机器人：用同一种子真跑一局跳一跳 ----------
typedef struct {
    nabo_jump_t game;
    uint32_t rng, act_at;
    int state;
} adv_vs_bot_t;
void adv_vs_bot_start(adv_vs_bot_t *bot, uint32_t seed, uint32_t now);
adv_vs_side_t adv_vs_bot_tick(adv_vs_bot_t *bot, uint32_t now);
// 本机跳一跳 → 对战状态
adv_vs_side_t adv_vs_side_of(const nabo_jump_t *game);

// ---------- NABO 陪练“影子”：其他游戏没有机器人，按本关铜到金之间的分数和随机时长推进 ----------
typedef struct { uint32_t start, duration, target; } adv_vs_ghost_t;
void adv_vs_ghost_start(adv_vs_ghost_t *ghost, uint32_t seed, uint32_t bronze, uint32_t gold, uint32_t now);
adv_vs_side_t adv_vs_ghost_tick(const adv_vs_ghost_t *ghost, uint32_t now);
