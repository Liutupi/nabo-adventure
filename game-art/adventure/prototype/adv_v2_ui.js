// Shared V2 landscape screens (G3 proposal): title, countdown, pause and result for every landscape game,
// so all six look and behave the same. Each game draws its own scene first, then calls these.
// Firmware target: one C module (adv_ui_cards.c) with the same layout; numbers here are the spec.
//   title : big name y=46, one-line pitch y=76, key chips y=176 (three, 88x22, centres 60/160/260), best + medal pips top right, blinking "按 ● 开始" y=214
//   result: cause y=30, score rolls 0→final over 40 frames at y=72, medal row y=108 (earned medals pop in), "距银章还差 N" y=130,
//           at most two stat lines y=150/166, "● 再来一局" y=214
(function (root) {
  'use strict';
  const W = 320, H = 240, MEDAL = ['#c9874a', '#c8d0dc', '#ffd34a'], MEDAL_NAME = ['铜章', '银章', '金章'];
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(20,24,40,.88)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  function medal(c, x, y, i, on, scale = 1) {
    const r = 7 * scale;
    c.fillStyle = on ? MEDAL[i] : 'rgba(255,255,255,.14)'; c.beginPath(); c.arc(x, y, r, 0, 7); c.fill();
    c.strokeStyle = on ? 'rgba(255,255,255,.75)' : 'rgba(255,255,255,.25)'; c.lineWidth = 1; c.stroke();
    if (on) { c.fillStyle = 'rgba(255,255,255,.55)'; c.fillRect(x - r / 3, y - r / 2, r / 3, r / 3); }
  }
  const earned = (score, th) => th.filter(t => score >= t).length;

  function title(c, t, vt) {
    c.fillStyle = `rgba(${t.ink},.58)`; c.fillRect(0, 150, W, 90);
    text(c, t.name, W / 2, 46, 26, '#ffffff', 'center');
    text(c, t.pitch, W / 2, 76, 11, '#f2f6ff', 'center', 700);
    t.keys.forEach(([k, s], i) => { const x = 60 + i * 100; c.fillStyle = 'rgba(255,255,255,.16)'; c.beginPath(); c.roundRect(x - 44, 165, 88, 22, 8); c.fill(); text(c, `${k} ${s}`, x, 176, 11, '#ffffff', 'center', 800, null); });
    const n = earned(t.best || 0, t.th);
    for (let i = 0; i < 3; i++) medal(c, W - 46 + i * 16, 12, i, i < n);
    if (t.best) text(c, '最佳 ' + t.best, W - 56, 12, 11, '#ffd34a', 'right');
    if (vt % 60 < 42) text(c, '按 ● 开始', W / 2, 214, 13, '#ffffff', 'center');
  }
  function ready(c, t, countdown) {
    const n = Math.ceil(countdown / 60);
    text(c, n > 0 ? String(n) : t.go, W / 2, 104, 32, '#ffffff', 'center');
    if (t.tip) text(c, t.tip, W / 2, 134, 11, '#ffffff', 'center', 700);
  }
  function pause(c, t) {
    c.fillStyle = `rgba(${t.ink},.78)`; c.fillRect(0, 0, W, H); text(c, '暂停', W / 2, 66, 24, '#ffffff', 'center');
    [['●', '继续'], ['◀', '重来'], ['▶▶', '双击回地图']].forEach(([k, s], i) => { const y = 108 + i * 26; c.fillStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.roundRect(W / 2 - 64, y - 11, 128, 22, 8); c.fill(); text(c, `${k}  ${s}`, W / 2, y, 12, '#ffffff', 'center', 800, null); });
  }
  // r = { cause, score, best (before this run), th, lines: [line1, line2], retry }
  function result(c, t, r, phaseT, vt) {
    const k = Math.min(1, phaseT / 30); c.fillStyle = `rgba(${t.ink},${.76 * k})`; c.fillRect(0, 0, W, H);
    if (phaseT <= 20) return;
    const roll = Math.min(1, (phaseT - 20) / 40), shown = Math.round(r.score * roll * (2 - roll));       // ease-out count-up
    text(c, r.cause, W / 2, 30, 12, '#e6ecff', 'center', 700, null);
    text(c, String(shown), W / 2, 72, 40, '#ffffff', 'center');
    const isRecord = r.score > (r.best || 0) && r.score > 0;
    if (isRecord && roll >= 1) text(c, '新纪录!', W / 2 + 84, 54, 12, '#ffd34a', 'center');
    const before = earned(r.best || 0, r.th), now = earned(shown, r.th);
    for (let i = 0; i < 3; i++) {
      const fresh = i >= before && i < now, pop = fresh ? 1 + .35 * Math.max(0, 1 - ((phaseT - 60) % 999) / 20) : 1;
      medal(c, W / 2 - 24 + i * 24, 108, i, i < Math.max(before, now), fresh && roll >= 1 ? pop : 1);
    }
    if (roll >= 1) {
      const all = earned(Math.max(r.score, r.best || 0), r.th);
      if (now > before) text(c, `拿到${MEDAL_NAME[now - 1]}!`, W / 2, 130, 11, MEDAL[now - 1], 'center', 900);
      else if (all < 3) text(c, `距${MEDAL_NAME[all]}还差 ${r.th[all] - r.score}`, W / 2, 130, 10, '#c9d3ee', 'center', 700, null);
      else text(c, '三枚章都拿到了', W / 2, 130, 10, '#ffd34a', 'center', 700, null);
    }
    (r.lines || []).slice(0, 2).forEach((s, i) => text(c, s, W / 2, 152 + i * 16, 10, i ? '#b9c4e2' : '#e6ecff', 'center', 700, null));
    if (phaseT > 60 && vt % 60 < 42) text(c, r.retry || '● 再来一局', W / 2, 214, 13, '#ffffff', 'center');
  }
  root.AdvV2UI = { title, ready, pause, result, medal, earned, text };
})(typeof window !== 'undefined' ? window : globalThis);
