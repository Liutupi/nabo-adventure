"""Lossless physical-frame ordering; presentation order remains explicitly mapped."""
import math
import random
import sys
from collections import deque
from boot_v2_sources import BASE

sys.path.insert(0,str(BASE.parents[1]/'tools'))
from generate_adv_sprites import index_frames,pack,rle,KEY_INTERVAL,INHERIT,decode


def optimal_keys_pack(width,height,frames):
 """Same v1 stream, globally cheapest <=8-frame key blocks for a fixed order."""
 baseline=pack(width,height,frames)  # Preserve production argument validation.
 if len(frames)==1:return baseline
 full=[[rle(f[y*width:(y+1)*width]) for y in range(height)] for f in frames]
 delta=[None]
 for previous,current in zip(frames,frames[1:]):
  pixels=bytes(INHERIT if a==b else b for a,b in zip(previous,current))
  delta.append([rle(pixels[y*width:(y+1)*width]) for y in range(height)])
 fcost=[sum(map(len,x)) for x in full];prefix=[0]
 for rows in delta[1:]:prefix.append(prefix[-1]+sum(map(len,rows)))
 dp=[];start=[]
 for end in range(len(frames)):
  choices=[((dp[key-1] if key else 0)+fcost[key]+prefix[end]-prefix[key],-key,key)
           for key in range(max(0,end-KEY_INTERVAL+1),end+1)]
  best,_,key=min(choices);dp.append(best);start.append(key)
 keys=[0]*len(frames);end=len(frames)-1
 while end>=0:
  key=start[end]
  for f in range(key,end+1):keys[f]=key
  end=key-1
 rows=[];data=bytearray()
 for f,key in enumerate(keys):
  for row in full[f] if f==key else delta[f]:rows.append(len(data));data.extend(row)
  rows.append(len(data))
 result=dict(width=width,height=height,keys=keys,rows=rows,data=bytes(data))
 assert len(data)==dp[-1] and len(data)<=len(baseline['data'])
 assert all(decode(result,i)==f for i,f in enumerate(frames))
 return result


def optimize(images,optimal_keys=False):
 palette,frames=index_frames(images);w,h=images[0].size;n=len(frames)
 full=[sum(len(rle(f[y*w:(y+1)*w])) for y in range(h)) for f in frames]
 diff={}
 for a in range(n):
  for b in range(n):
   if a==b:continue
   pixels=bytes(INHERIT if x==y else y for x,y in zip(frames[a],frames[b]))
   diff[a,b]=sum(len(rle(pixels[y*w:(y+1)*w])) for y in range(h))
 def cost(order):
  if optimal_keys:
   # Sliding minimum form of the <=8-frame key-block DP: linear per order.
   queue=deque();prefix=0;previous=0
   for i,frame in enumerate(order):
    if i:prefix+=diff[order[i-1],frame]
    value=previous+full[frame]-prefix
    while queue and queue[-1][0]>=value:queue.pop()
    queue.append((value,i))
    while queue[0][1]<=i-KEY_INTERVAL:queue.popleft()
    previous=prefix+queue[0][0]
   return previous
  total=full[order[0]];key=0
  for i in range(1,n):
   delta=diff[order[i-1],order[i]]
   if i-key>=KEY_INTERVAL or delta>=full[order[i]]:key=i;total+=full[order[i]]
   else:total+=delta
  return total
 baseline=list(range(n));greedy=[0];remaining=set(range(1,n))
 while remaining:
  item=min(remaining,key=lambda x:(min(diff[greedy[-1],x],full[x]),x));greedy.append(item);remaining.remove(item)
 rng=random.Random(20261025);seeds=[baseline,greedy]
 for _ in range(10 if optimal_keys else 6):
  rest=list(range(1,n));rng.shuffle(rest);seeds.append([0,*rest])
 best=baseline[:];best_cost=cost(best)
 for seed in seeds:
  current=seed[:];current_cost=cost(current)
  steps=70000 if optimal_keys else 9000
  for step in range(steps):
   a,b=sorted(rng.sample(range(1,n),2));trial=current[:]
   move=step%3 if optimal_keys else 0
   if move==0:trial[a],trial[b]=trial[b],trial[a]
   elif move==1:trial[a:b+1]=reversed(trial[a:b+1])
   else:trial.insert(b,trial.pop(a))
   candidate=cost(trial);temperature=max(1,1000*(1-step/steps))
   if candidate<current_cost or rng.random()<math.exp(min(0,(current_cost-candidate)/temperature)):
    current=trial;current_cost=candidate
    if candidate<best_cost:best=current[:];best_cost=candidate
 before=pack(w,h,frames);after=(optimal_keys_pack if optimal_keys else pack)(w,h,[frames[i] for i in best])
 assert (len(before['data'])==cost(baseline) if not optimal_keys else True) and len(after['data'])==best_cost
 assert all(decode(after,f)==frames[original] for f,original in enumerate(best))
 return best,dict(method='Deterministic physical-frame permutation minimizes existing row-RLE delta cost; timeline remaps logical events exactly',
  baseline_data_bytes=len(before['data']),optimized_data_bytes=len(after['data']),saved_bytes=len(before['data'])-len(after['data']),
  storage_order_original_indices=best,palette_unchanged=True,all_indexed_frames_exact=True,key_interval=KEY_INTERVAL,
  optimal_key_objective=optimal_keys,greedy_encoder_bytes_for_same_order=len(pack(w,h,[frames[i] for i in best])['data']))
