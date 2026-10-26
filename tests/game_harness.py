"""Shared JS/C golden replay for games whose state is 3 uint32 + int32 words (SKI, SKY, SPACE)."""
import ctypes
from pathlib import Path
import subprocess
from host_tools import CC, SHARED_EXPORT

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'


class Input(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint8) for n in ('ok_down', 'ok_up', 'up_down', 'down_down', 'down_up', 'ok_held', 'down_held', 'up_held')]


def build(folder, game, words, events=(), mutation=None):
    """Compiles adv_<game>.c; returns (lib, State) where State is `words` int32 words."""
    folder = Path(folder)
    for name in (f'adv_{game}.c', f'adv_{game}.h'):
        source = (BOARD/name).read_text('utf-8')
        if mutation and mutation[0] == name:
            assert mutation[1] in source, mutation
            source = source.replace(mutation[1], mutation[2], 1)
        (folder/name).write_text(source, 'utf-8')
    target = folder/f'{game}.dll'
    subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror', '-I', str(folder),
                    '-I', str(BOARD), str(folder/f'adv_{game}.c'), '-o', str(target)], check=True)
    lib = ctypes.CDLL(str(target))

    class State(ctypes.Structure):
        _fields_ = [('w', ctypes.c_int32*words)]
    getattr(lib, f'adv_{game}_start').argtypes = [ctypes.POINTER(State), ctypes.c_uint32]
    getattr(lib, f'adv_{game}_step').argtypes = [ctypes.POINTER(State), ctypes.POINTER(Input)]
    for name in events: getattr(lib, f'adv_{game}_{name}_event').argtypes = [ctypes.POINTER(State), ctypes.c_bool]
    return lib, State


def view(g):
    return [v & 0xffffffff if i < 3 else v for i, v in enumerate(g.w)]


def replay(lib, State, game, trace, extra=lambda g: []):
    g = State()
    start, step = getattr(lib, f'adv_{game}_start'), getattr(lib, f'adv_{game}_step')
    start(ctypes.byref(g), trace['seed'])
    for i, (action, expected) in enumerate(zip(trace['actions'], trace['states'])):
        if action[0] == 'reset': start(ctypes.byref(g), action[1])
        elif action[0] in ('up', 'down'): getattr(lib, f'adv_{game}_{action[0]}_event')(ctypes.byref(g), bool(action[1]))
        else: step(ctypes.byref(g), ctypes.byref(Input(*action)))
        actual = view(g) + extra(g)
        if actual != expected:
            return i, [(j, a, e) for j, (a, e) in enumerate(zip(actual, expected)) if a != e][:6]
    return None


def fnv(words):
    """FNV-1a over the little-endian bytes of each 32-bit word (tests/*_golden hashed traces)."""
    h = 0x811c9dc5
    for w in words:
        u = w & 0xffffffff
        for k in (0, 8, 16, 24):
            h ^= (u >> k) & 255
            h = (h * 0x01000193) & 0xffffffff
    return h


def replay_hashed(lib, State, game, trace):
    """Replays a hashed trace; returns None or (first differing step, checkpoint hint)."""
    g = State()
    start, step = getattr(lib, f'adv_{game}_start'), getattr(lib, f'adv_{game}_step')
    start(ctypes.byref(g), trace['seed'])
    for i, action in enumerate(trace['actions']):
        if action[0] == 'reset': start(ctypes.byref(g), action[1])
        else: step(ctypes.byref(g), ctypes.byref(Input(*action)))
        actual = view(g)
        if fnv(actual) != trace['hashes'][i]:
            return i, min((int(k) for k in trace['states'] if int(k) >= i), default=None)
        if str(i) in trace['states'] and actual != trace['states'][str(i)]: return i, 'checkpoint'
    return None
