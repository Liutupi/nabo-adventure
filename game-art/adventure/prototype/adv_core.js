// NABO 的冒险之旅 — shell rules (map, passport, stamps, sessions) and the placeholder game.
// This file is the reference for firmware/main/adv_model.c, adv_demo.c and collection_model.c's
// settings part: integer maths only, mulberry32 random numbers, one step = 1/60 s.
// Change rules here first, re-record tests/adv_golden, then port to C.
(function (root) {
  'use strict';
  const Post=typeof module!=='undefined'&&module.exports?require('./adv_post.js'):root.AdvPost;
  const Night=typeof module!=='undefined'&&module.exports?require('./adv_night.js'):root.AdvNight;
  const Climb=typeof module!=='undefined'&&module.exports?require('./adv_climb.js'):root.AdvClimb;

  // ---------- constants shared with adv_model.h ----------
  const BTN = { UP: 0, DOWN: 1, OK: 2 };
  const EV = { PRESS: 0, CLICK: 1, DOUBLE: 2, LONG: 3, RELEASE: 4 };   // = bsp_btn_ev_t
  const PAGE = { COVER: 0, MAP: 1, KIOSK: 2, PASSPORT: 3, SETTINGS: 4, STAMP: 5, LEGACY: 6, SESSION: 7 };
  const PHASE = { TITLE: 0, READY: 1, PLAY: 2, PAUSE: 3, END: 4, RESULT: 5 };
  const FX = { REDRAW: 1, OPEN_LEGACY: 2, SAVE_PROGRESS: 4, SAVE_BEST: 8, SAVE_SETTINGS: 16, APPLY_SETTINGS: 32, CUE: 64 };
  const CUE = { NONE: 0, MOVE: 1, ENTER: 2, DENY: 3, STAMP: 4, BACK: 5, HIT: 6, MISS: 7, OVER: 8, GO: 9, WHISTLE: 10 };
  const READY_STEPS = 180, END_STEPS = 120;
  const STATIONS = 9, KIOSK = 0;
  // Map path from the bottom (deep sea) to the top (space).
  const PATH = [2, 0, 1, 3, 4, 5, 6, 7, 8];
  const START_STATION = 1;
  const DEMO_THRESHOLDS = [3, 6, 10];

  // kind: 0 kiosk, 1 legacy game with its own UI, 2 shell session game.
  // placeholder: the session runs the demo game and uses DEMO_THRESHOLDS until the real game lands.
  const STATION = [
    { id: 'kiosk', cn: '护照亭', en: 'PASSPORT', world: '小镇', res: '', kind: 0, th: [0, 0, 0], placeholder: false },
    { id: 'jump', cn: '跳一跳', en: 'JUMP', world: '小镇', res: '体力', kind: 1, th: [10, 25, 50], placeholder: false },
    { id: 'dive', cn: '深潜', en: 'DIVE', world: '深海', res: '氧气', kind: 1, th: [100, 300, 600], placeholder: false },
    { id: 'post', cn: '小火车', en: 'POST', world: '铁路平原', res: '蒸汽', kind: 2, th: [5, 12, 25], placeholder: false },
    { id: 'night', cn: '萤火虫', en: 'NIGHT', world: '夜林', res: '精神', kind: 2, th: [15, 35, 60], placeholder: false },
    { id: 'climb', cn: '登山', en: 'CLIMB', world: '雪山', res: '体力', kind: 2, th: [50, 150, 300], placeholder: false },
    { id: 'ski', cn: '滑雪', en: 'SKI', world: '雪坡', res: '体温', kind: 2, th: [10, 25, 45], placeholder: true },
    { id: 'sky', cn: '热气球', en: 'SKY', world: '云端', res: '热气', kind: 2, th: [200, 500, 1000], placeholder: true },
    { id: 'space', cn: '太空', en: 'SPACE', world: '太空', res: '燃料', kind: 2, th: [300, 600, 900], placeholder: true },
  ];

  function threshold(s, tier) { return STATION[s].placeholder ? DEMO_THRESHOLDS[tier] : STATION[s].th[tier]; }

  // ---------- mulberry32 (identical in adv_rng.h) ----------
  function rand(holder) {
    holder.rng = (holder.rng + 0x6D2B79F5) >>> 0;
    let t = holder.rng;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (t ^ (t >>> 14)) >>> 0;
  }

  // ---------- placeholder game (adv_demo.c) ----------
  // A marker sweeps a track; OK inside the zone scores and refills, outside costs 25%.
  const Demo = {
    start(seed) {
      const g = { rng: seed >>> 0, p: 0, v: 12, zh: 180, zc: 0, score: 0, res: 1000, over: 0, hit: 0, miss: 0, cue: 0 };
      Demo.newZone(g);
      return g;
    },
    newZone(g) { g.zc = g.zh + rand(g) % (1000 - 2 * g.zh + 1); },
    step(g, input) {
      g.cue = 0;
      if (g.hit) g.hit--;
      if (g.miss) g.miss--;
      if (g.over) return;
      g.p += g.v;
      if (g.p >= 1000) { g.p = 1000; g.v = -g.v; }
      if (g.p <= 0) { g.p = 0; g.v = -g.v; }
      g.res -= 2;
      if (input.ok_down) {
        if (Math.abs(g.p - g.zc) <= g.zh) {
          g.score++;
          g.res = Math.min(1000, g.res + 150);
          g.zh = Math.max(60, g.zh - 10);
          const speed = Math.min(30, Math.abs(g.v) + 1);
          g.v = g.v < 0 ? -speed : speed;
          Demo.newZone(g);
          g.hit = 12; g.cue = CUE.HIT;
        } else {
          g.res -= 250;
          g.miss = 12; g.cue = CUE.MISS;
        }
      }
      if (g.res <= 0) { g.res = 0; g.over = 1; g.cue = CUE.OVER; }
    },
    status(g) { return { score: g.score, res: g.res, over: g.over }; },
  };

  // ---------- settings (collection_model.c, settings and status pages only) ----------
  const CG = { HOME: 0, SETTINGS: 4, STATUS: 5 };
  const CGK = { UP: 0, DOWN: 1, OK: 2, BACK: 3 };
  const CGR = { CHANGED: 1, SAVE: 2, PAGE: 4 };
  const SLEEP = [0, 30, 60, 120, 300, 600];
  const clamp = (n, lo, hi) => n < lo ? lo : n > hi ? hi : n;
  function cgSanitize(s) { s.volume = clamp(s.volume, 0, 100); s.brightness = clamp(s.brightness, 10, 100); s.sleep = clamp(s.sleep, 0, 600); }
  function cgKey(c, key) {
    const before = c.page;
    let r = CGR.CHANGED;
    if (key === CGK.BACK) {
      if (c.page === CG.SETTINGS && c.editing >= 0) { Object.assign(c.s, c.saved); c.editing = -1; }
      else c.page = c.page === CG.STATUS ? CG.SETTINGS : CG.HOME;
    } else if (c.page === CG.SETTINGS) {
      if (c.editing >= 0) {
        if (key === CGK.OK) { c.editing = -1; r |= CGR.SAVE; }
        else {
          const d = key === CGK.UP ? 1 : -1;
          if (c.editing === 0) c.s.volume += d * 5;
          if (c.editing === 1) c.s.brightness += d * 5;
          if (c.editing === 3) {
            let i = 0;
            while (i < 5 && SLEEP[i] < c.s.sleep) i++;
            c.s.sleep = SLEEP[clamp(i + d, 0, 5)];
          }
          cgSanitize(c.s);
        }
      } else if (key === CGK.UP || key === CGK.DOWN) c.cursor = (c.cursor + (key === CGK.UP ? 5 : 1)) % 6;
      else if (key === CGK.OK) {
        if (c.cursor === 5) c.page = CG.HOME;
        else if (c.cursor === 4) c.page = CG.STATUS;
        else if (c.cursor === 2) { c.s.speaker = !c.s.speaker; r |= CGR.SAVE; }
        else { c.saved = Object.assign({}, c.s); c.editing = c.cursor; }
      }
    } else if (c.page === CG.STATUS) c.page = CG.SETTINGS;
    else return 0;
    if (c.page !== before) r |= CGR.PAGE;
    return r;
  }

  // ---------- shell model (adv_model.c) ----------
  function bit(s, tier) { return 1 << ((s - 1) * 3 + tier); }

  function earned(m) {
    // Acknowledged awards survive later rule/threshold upgrades.
    let e = m.seen & 0xffffff;
    for (let s = 1; s < STATIONS; s++)
      for (let tier = 0; tier < 3; tier++)
        if (m.best[s] >= threshold(s, tier)) e |= bit(s, tier);
    return e >>> 0;
  }

  function unlocked(m, s) {
    if (s <= START_STATION) return true;
    if (m.seen & bit(s - 1, 0)) return true;
    return m.best[s - 1] >= threshold(s - 1, 0);
  }

  function create(seed, settings, best, seen) {
    return {
      page: PAGE.COVER, cursor: START_STATION, kiosk: 0, passport: 0, passportFrom: PAGE.MAP,
      cfg: { page: CG.SETTINGS, cursor: 0, editing: -1, s: Object.assign({}, settings), saved: Object.assign({}, settings) },
      best: best.slice(), seen: seen >>> 0, stamp: -1,
      rng: seed >>> 0, held: 0, input: { ok_down: 0, ok_up: 0, up_down: 0, down_down: 0, down_up: 0 },
      session: null, test: false, fx: 0, cue: 0,
    };
  }

  function cue(m, c) { m.cue = c; m.fx |= FX.CUE; }

  // Shows the lowest new stamp, or lands on the map.
  function toMap(m) {
    m.session = null;
    const pending = (earned(m) & ~m.seen) >>> 0;
    if (pending) {
      let b = 0;
      while (!((pending >>> b) & 1)) b++;
      m.stamp = b; m.page = PAGE.STAMP; cue(m, CUE.STAMP);
    } else { m.stamp = -1; m.page = PAGE.MAP; }
  }

  function clearInput(m) { m.input = { ok_down: 0, ok_up: 0, up_down: 0, down_down: 0, down_up: 0 }; }

  function startRun(m, practice=false) {
    const s = m.session;
    s.seed = rand(m);
    s.game = practice&&s.station===3?Post.startPractice(s.seed):engine(s.station).start(s.seed);
    s.phase = PHASE.READY; s.t = READY_STEPS; s.record = 0;
    clearInput(m);
    cue(m, CUE.ENTER);
  }

  function moveCursor(m, dir) {
    // NABO may step onto the first locked station to look at it, but never past it.
    const i = PATH.indexOf(m.cursor), j = i + dir;
    if (j < 0 || j >= PATH.length || (!unlocked(m, m.cursor) && !unlocked(m, PATH[j]))) { cue(m, CUE.DENY); return; }
    m.cursor = PATH[j]; cue(m, CUE.MOVE);
  }

  function enterStation(m) {
    const s = m.cursor;
    if (s === KIOSK) { m.page = PAGE.KIOSK; m.kiosk = 0; cue(m, CUE.ENTER); return; }
    if (!unlocked(m, s)) { cue(m, CUE.DENY); return; }
    if (STATION[s].kind === 1) { m.page = PAGE.LEGACY; m.fx |= FX.OPEN_LEGACY; cue(m, CUE.ENTER); return; }
    openSession(m,s);
  }

  function openSession(m,s) {
    m.page = PAGE.SESSION;
    m.session = { station: s, phase: PHASE.TITLE, t: 0, seed: 0, game: null, record: 0 };
    cue(m, CUE.ENTER);
  }

  function testOpen(m,s) {
    m.fx=0;m.cue=0;
    if(!m.test||m.page!==PAGE.MAP||m.session||!Number.isInteger(s)||s<3||s>=STATIONS)return 0;
    m.cursor=s;m.fx=FX.REDRAW;openSession(m,s);return m.fx;
  }

  function openPassport(m, from) { m.page = PAGE.PASSPORT; m.passport = 0; m.passportFrom = from; cue(m, CUE.ENTER); }

  function practiceOpen(m) {
    m.fx=0;m.cue=CUE.NONE;
    if((m.page!==PAGE.MAP&&m.page!==PAGE.COVER)||m.session)return 0;
    m.fx=FX.REDRAW;openSession(m,3);startRun(m,true);return m.fx;
  }

  function isBack(btn, ev) { return btn === BTN.UP && (ev === EV.LONG || ev === EV.DOUBLE); }
  function gameMapKey(btn, ev) { return btn === BTN.UP && ev === EV.DOUBLE; }
  function engine(station){return station===3?Post:station===4?Night:station===5?Climb:Demo;}

  function recordResult(m) {
    const s=m.session,score=engine(s.station).status(s.game).score;
    if(score>m.best[s.station]) {
      s.record=1;
      if(!m.test){m.best[s.station]=score;m.fx|=FX.SAVE_BEST;}
    }
  }

  function sessionEvent(m, btn, ev) {
    const s = m.session;
    const confirm=s.station===4?BTN.DOWN:BTN.OK,restart=s.station===4?BTN.OK:BTN.DOWN;
    if(gameMapKey(btn,ev)) {
      if(s.station===4&&s.phase===PHASE.PLAY&&s.game.shortTaps<2)return;
      if(s.phase===PHASE.END)recordResult(m);
      cue(m,CUE.BACK);toMap(m);return;
    }
    if (s.phase === PHASE.TITLE) {
      if (btn === confirm && ev === EV.CLICK) startRun(m);
      else if (s.station===3&&btn===BTN.DOWN&&ev===EV.CLICK) startRun(m,true);
    } else if (s.phase === PHASE.PLAY) {
      if(s.station===4&&btn===BTN.UP&&(ev===EV.PRESS||ev===EV.RELEASE))Night.upEvent(s.game,ev===EV.PRESS);
      if (btn === (s.station===4?BTN.DOWN:BTN.UP) && ev === EV.LONG) { s.phase = PHASE.PAUSE; cue(m, CUE.BACK); return; }
      if (ev === EV.PRESS) {
        if (btn === BTN.OK) m.input.ok_down = 1;
        if (btn === BTN.UP) m.input.up_down = 1;
        if (btn === BTN.DOWN) m.input.down_down = 1;
      } else if (ev === EV.RELEASE) {
        if (btn === BTN.OK) m.input.ok_up = 1;
        if (btn === BTN.DOWN) m.input.down_up = 1;
      } else return;
    } else if (s.phase === PHASE.PAUSE) {
      if (btn === confirm && ev === EV.CLICK) { s.phase = PHASE.PLAY; clearInput(m); cue(m, CUE.GO); }
      else if (btn === restart && ev === EV.CLICK) startRun(m,s.station===3&&s.game.practice);
    } else if (s.phase === PHASE.RESULT) {
      if (btn === confirm && ev === EV.CLICK) startRun(m);
      else if (s.station===3&&btn===BTN.DOWN&&ev===EV.CLICK) startRun(m,true);
    }
  }

  // Button event (bsp_btn_ev_t). Returns FX flags.
  function event(m, btn, ev) {
    m.fx = 0; m.cue = 0;
    if (ev === EV.PRESS) m.held |= 1 << btn;
    if (ev === EV.RELEASE) m.held &= ~(1 << btn);
    const before = JSON.stringify(view(m));
    const click = ev === EV.CLICK;
    switch (m.page) {
      case PAGE.COVER:
        if (btn === BTN.OK && click) { cue(m, CUE.ENTER); toMap(m); }
        break;
      case PAGE.MAP:
        if (click && btn === BTN.UP) moveCursor(m, 1);
        else if (click && btn === BTN.DOWN) moveCursor(m, -1);
        else if (click && btn === BTN.OK) enterStation(m);
        else if (btn === BTN.OK && ev === EV.LONG) openPassport(m, PAGE.MAP);
        else if (isBack(btn, ev)) { m.page = PAGE.COVER; cue(m, CUE.BACK); }
        break;
      case PAGE.KIOSK:
        if (click && (btn === BTN.UP || btn === BTN.DOWN)) { m.kiosk = (m.kiosk + (btn === BTN.UP ? 2 : 1)) % 3; cue(m, CUE.MOVE); }
        else if (click && btn === BTN.OK) {
          if (m.kiosk === 0) openPassport(m, PAGE.KIOSK);
          else if (m.kiosk === 1) {
            m.page = PAGE.SETTINGS; m.cfg.page = CG.SETTINGS; m.cfg.cursor = 0; m.cfg.editing = -1; cue(m, CUE.ENTER);
          } else { cue(m, CUE.BACK); toMap(m); }
        } else if (isBack(btn, ev)) { cue(m, CUE.BACK); toMap(m); }
        break;
      case PAGE.PASSPORT:
        if (click && (btn === BTN.UP || btn === BTN.DOWN)) { m.passport = (m.passport + (btn === BTN.UP ? 7 : 1)) % 8; cue(m, CUE.MOVE); }
        else if ((click && btn === BTN.OK) || isBack(btn, ev)) {
          cue(m, CUE.BACK);
          if (m.passportFrom === PAGE.KIOSK) m.page = PAGE.KIOSK; else toMap(m);
        }
        break;
      case PAGE.SETTINGS: {
        let key = -1;
        if (click) key = btn === BTN.UP ? CGK.UP : btn === BTN.DOWN ? CGK.DOWN : CGK.OK;
        else if (isBack(btn, ev)) key = CGK.BACK;
        if (key < 0) break;
        const r = cgKey(m.cfg, key);
        if (r & CGR.CHANGED) m.fx |= FX.APPLY_SETTINGS;
        if (r & CGR.SAVE) m.fx |= FX.SAVE_SETTINGS;
        if (m.cfg.page === CG.HOME) { m.page = PAGE.KIOSK; cue(m, CUE.BACK); } else cue(m, CUE.MOVE);
        break;
      }
      case PAGE.STAMP:
        if (btn === BTN.OK && click) {
          m.seen = (m.seen | (1 << m.stamp)) >>> 0;
          m.fx |= FX.SAVE_PROGRESS;
          toMap(m);
          if (m.page === PAGE.MAP) cue(m, CUE.ENTER);
        }
        break;
      case PAGE.SESSION: sessionEvent(m, btn, ev); break;
      case PAGE.LEGACY:
        if(gameMapKey(btn,ev)){cue(m,CUE.BACK);toMap(m);}
        break;
      default: break;   // LEGACY: the platform routes buttons to the legacy game
    }
    if (JSON.stringify(view(m)) !== before) m.fx |= FX.REDRAW;
    return m.fx;
  }

  // Legacy game closed; best is its best score in game units (jump: score, dive: metres).
  function legacyDone(m, best) {
    m.fx = 0; m.cue = 0;
    if (m.page !== PAGE.LEGACY) return 0;
    if (best > m.best[m.cursor]) m.best[m.cursor] = best >>> 0;
    toMap(m);
    m.fx |= FX.REDRAW;
    return m.fx;
  }

  // One 1/60 s step.
  function step(m) {
    m.fx = 0; m.cue = 0;
    const s = m.session;
    if (m.page !== PAGE.SESSION || !s) return 0;
    if (s.phase === PHASE.READY) {
      if (--s.t === 0) { s.phase = PHASE.PLAY; cue(m, CUE.GO); }
      m.fx |= FX.REDRAW;
    } else if (s.phase === PHASE.PLAY) {
      const input = Object.assign({ ok_held: (m.held >> BTN.OK) & 1, down_held: (m.held >> BTN.DOWN) & 1,up_held:(m.held>>BTN.UP)&1 }, m.input);
      clearInput(m);
      engine(s.station).step(s.game, input);
      if (s.game.cue) cue(m, s.game.cue);
      if (engine(s.station).status(s.game).over) {
        if(s.station===3&&s.game.practice){if(m.test||unlocked(m,3))startRun(m);else toMap(m);}
        else {s.phase = PHASE.END; s.t = END_STEPS;}
      }
      m.fx |= FX.REDRAW;
    } else if (s.phase === PHASE.END) {
      engine(s.station).step(s.game, { ok_down: 0, ok_up: 0, up_down: 0, down_down: 0, down_up: 0, ok_held: 0, down_held: 0 });
      if (--s.t === 0) {
        s.phase = PHASE.RESULT;
        recordResult(m);
      }
      m.fx |= FX.REDRAW;
    }
    return m.fx;
  }

  // Everything the golden traces compare (same keys and order as tests/adv_host/adv_snapshot.c).
  function view(m) {
    const s = m.session, g = s && s.game;
    return {
      page: m.page, cursor: m.cursor, kiosk: m.kiosk, passport: m.passport, from: m.passportFrom,
      cfg: [m.cfg.page, m.cfg.cursor, m.cfg.editing, m.cfg.s.volume, m.cfg.s.brightness, m.cfg.s.sleep, m.cfg.s.speaker ? 1 : 0],
      best: m.best.slice(), seen: m.seen, stamp: m.stamp, held: m.held,
      session: s ? [s.station, s.phase, s.t, s.seed, s.record] : null,
      game: g ? (s.station===3?Post.view(g):s.station===4?Night.view(g):s.station===5?Climb.view(g):[g.p, g.v, g.zc, g.zh, g.score, g.res, g.over, g.hit, g.miss]) : null,
    };
  }

  const api = {
    BTN, EV, PAGE, PHASE, FX, CUE, CG, STATION, PATH, START_STATION, DEMO_THRESHOLDS, READY_STEPS, END_STEPS,
    create, event, step, legacyDone, view, earned, unlocked, threshold, bit, rand, Demo, Post,Night,Climb, testOpen,practiceOpen,gameMapKey,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AdvCore = api;
})(this);
