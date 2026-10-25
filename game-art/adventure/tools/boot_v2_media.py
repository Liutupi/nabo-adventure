"""Encode the exact pose exposure table and unchanged 1.4s-delayed voice as MP4."""
import json
import subprocess
from PIL import Image
from boot_v2_sources import ART,BASE,OUT,PREVIEW,sha

FFMPEG=r'C:\Users\pc\Documents\Codex\2026-10-10\h\work\packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'


def main():
 manifest=json.loads((ART/'boot-v2-manifest.json').read_text('utf-8'));entry=manifest['animations'][0];timeline=manifest['timeline']
 folder=ART/entry['masters'][0];folder=folder.parent.parent
 frames=[]
 for i,ticks in enumerate(timeline['duration_ticks']):
  data=Image.open(folder/'screens'/f'{i:03d}.png').convert('RGB').tobytes()
  frames.extend([data]*ticks)
 assert len(frames)==53 and sum(timeline['duration_ms'])==4417
 variant='v2a' if folder.name=='v2a' else 'v2'
 voice=BASE/'audio/boot-welcome.wav';before=sha(voice);path=PREVIEW/f'welcome-{variant}-production-ui-voice.mp4'
 command=[FFMPEG,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','240x320',
  '-framerate','12','-i','pipe:0','-i',str(voice),'-filter_complex','[1:a]adelay=1400,apad[a]',
  '-map','0:v','-map','[a]','-t',str(53/12),'-c:v','libx264','-crf','12','-pix_fmt','yuv420p',
  '-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart',str(path)]
 subprocess.run(command,input=b''.join(frames),capture_output=True,check=True)
 assert sha(voice)==before
 report=dict(path=path.relative_to(ART).as_posix(),sha256=sha(path),native_canvas=[240,320],fps=12,video_frames=53,
  exact_video_seconds=53/12,declared_timeline_ms=4417,voice_start_ms=1400,voice_end_ms=4090.625,
  voice_source_sha256=before,voice_unchanged=True,source_manifest_sha256=sha(ART/'boot-v2-manifest.json'),
  presentation=f"Identical {timeline['logical_pose_count']}-event / {timeline['unique_frame_count']}-unique-image timeline and screen anchor120,266; no preview-only movement",
  ffmpeg_path=FFMPEG,ffmpeg_sha256=sha(FFMPEG),codec_note='Lossy H264/AAC preview only; PNG/C decoder checks remain the pixel authority')
 (PREVIEW/f'media-{variant}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
