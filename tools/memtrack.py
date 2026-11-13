#!/usr/bin/env python3
"""Log dwarf and vehicle positions at 10 Hz from the running game's memory. Read-only.

Autosaves are too far apart to tell routes or rides. The entity position array (12 bytes per
entity: x, y, z 16.16) is found by searching for two bridges of the West Hirdness colony at known
positions. A dwarf riding a vehicle reads 0,0, because his transform is then relative to the cart.

usage: memtrack.py <seconds> <out file> [extra entity ids...]
"""
import sys,struct,subprocess,time,re
IDS=[2098,2139,2312,2316,2320,4112]+[int(a) for a in sys.argv[3:]]
pid=int(subprocess.check_output("ps -eo pid,comm --sort=-rss | awk '$2 ~ /boot/ {print $1; exit}'",shell=True).split()[0])
mem=open(f'/proc/{pid}/mem','rb',buffering=0)
pat=struct.pack('<iii',567<<16,1005<<16,0); chk=struct.pack('<iii',572<<16,1013<<16,0)
base=None
for l in open(f'/proc/{pid}/maps'):
    m=re.match(r'([0-9a-f]+)-([0-9a-f]+) (r.-.)',l)
    if not m or 'w' not in m.group(3): continue
    a,b=int(m.group(1),16),int(m.group(2),16)
    if b-a<12*4400: continue
    try:
        mem.seek(a); d=mem.read(b-a)
    except OSError: continue
    i=d.find(pat)
    while i>=0:
        bs=a+i-12*2875
        if bs>=a and d[bs-a+12*3544:bs-a+12*3544+12]==chk: base=bs; break
        i=d.find(pat,i+4)
    if base: break
print('base',hex(base) if base else None)
if not base: sys.exit(1)
out=open(sys.argv[2],'w'); end=time.time()+float(sys.argv[1]); t0=time.time()
while time.time()<end:
    r=[]
    for e in IDS:
        mem.seek(base+12*e); x,y,z=struct.unpack('<iii',mem.read(12)); r.append(f'{x/65536:.1f},{y/65536:.1f}')
    out.write(f'{time.time()-t0:.1f} '+' '.join(r)+'\n'); out.flush(); time.sleep(0.1)
