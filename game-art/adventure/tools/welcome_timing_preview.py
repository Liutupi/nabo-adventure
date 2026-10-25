"""Standalone host sound/visual timing preview; audio and firmware sources remain untouched."""
import base64
import json
import wave
from build_travel_rig import ART,digest


def build(entries):
    entry=next(e for e in entries if e['name']=='welcome')
    voice=ART.parent/'audio/boot-welcome.wav'
    with wave.open(str(voice)) as wav:
        audio={'samples':wav.getnframes(),'sample_rate':wav.getframerate(),'channels':wav.getnchannels(),
               'duration_s':wav.getnframes()/wav.getframerate(),'sha256':digest(voice)}
    assert audio['duration_s']==2.690625
    data={'frames':['data:image/png;base64,'+base64.b64encode((ART/p).read_bytes()).decode('ascii') for p in entry['runtime_frames']],
          'voice':'data:audio/wav;base64,'+base64.b64encode(voice.read_bytes()).decode('ascii'),
          'anchor':entry['runtime_anchor'],'fps':12,'voiceStart':1.4,'voiceEnd':4.090625}
    html='''<!doctype html><meta charset="utf-8"><title>NABO welcome host timing preview</title>
<style>body{font:16px system-ui;background:#eee6de;color:#182439;max-width:760px;margin:28px auto}canvas{width:480px;height:640px;image-rendering:pixelated;border:1px solid #ae9270}button{font:inherit;padding:10px 18px;margin:12px 0}small{display:block;max-width:600px}#status{white-space:pre-wrap}</style>
<h2>NABO welcome · host timing preview</h2><button id="play">Play voice + animation</button><div id="status">Ready</div><canvas width="240" height="320"></canvas>
<small>Original 120px runtime frames, no resizing in the canvas. Entry translation is simulated by the host, not baked into the sprites. Voice starts at 1.400s and ends at 4.090625s. The neutral original mouth is retained: this is a voiced invitation, not invented lip sync. This does not establish device timing.</small>
<script>const DATA=__DATA__;
const canvas=document.querySelector('canvas'), g=canvas.getContext('2d');g.imageSmoothingEnabled=false;
const status=document.querySelector('#status');let ctx,playing,source;const images=DATA.frames.map(p=>{const im=new Image();im.src=p;return im});
function draw(t){g.fillStyle='#f6e2b4';g.fillRect(0,0,240,320);g.fillStyle='#182439';g.font='12px sans-serif';g.fillText('NABO welcome / 120px',12,24);
 const p=Math.min(1,Math.max(0,t/1.4));const ease=p*p*(3-2*p);const x=Math.round(-58+(120+58)*ease);
 const index=t<1.4||t>=DATA.voiceEnd?0:Math.floor((t-1.4)*DATA.fps)%images.length;
 if(images[index].complete)g.drawImage(images[index],x-DATA.anchor[0],266-DATA.anchor[1]);
 g.fillStyle='#182439';g.fillText('t='+Math.max(0,t).toFixed(3)+'s / frame '+index,12,302);}
draw(0);Promise.all(images.map(im=>im.decode())).then(()=>draw(0));
document.querySelector('#play').onclick=async()=>{if(playing)return;ctx=ctx||new AudioContext();await ctx.resume();
 const bytes=await(await fetch(DATA.voice)).arrayBuffer();const audio=await ctx.decodeAudioData(bytes);source=ctx.createBufferSource();source.buffer=audio;source.connect(ctx.destination);
 const start=ctx.currentTime+.05;source.start(start+DATA.voiceStart);playing=true;status.textContent='WebAudio sample-clock schedule active: cue +1.400s';
 function tick(){const t=ctx.currentTime-start;draw(t);if(t<4.5){requestAnimationFrame(tick)}else{playing=false;status.textContent='Finished; voice '+audio.duration.toFixed(6)+'s. Device timing remains separate.'}}requestAnimationFrame(tick)};
</script>'''.replace('__DATA__',json.dumps(data,separators=(',',':')))
    path=ART/'preview/travel/welcome-voice-preview.html';path.write_text(html,'utf-8')
    audio.update({'voice_start_s':1.4,'voice_end_s':4.090625,'source_clip_frames':16,'fps':12,
                  'two_cycles_s':32/12,'post_cycles_hold_s':audio['duration_s']-32/12,
                  'preview':path.relative_to(ART).as_posix(),'schedule':'WebAudio sample clock; host entry ease-in/out; not device acceptance'})
    (ART/'preview/travel/welcome-timing.json').write_text(json.dumps(audio,indent=2)+'\n','utf-8')


if __name__=='__main__':
    build(json.loads((ART/'manifest.json').read_text('utf-8'))['animations'])
