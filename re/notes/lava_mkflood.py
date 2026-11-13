"""mkflood.py <in save> <out save> : lava (amount 7) over the Cave Farm and cook house floor of KrazJomsglind savegame32."""
import sys,struct,os
sys.path.insert(0,'/home/john-champaign/Claude Code/Hammerting/tools')
from save import Save
def off(x,y): return 16+4*(((y>>4)*68+(x>>4))<<8|(y&15)<<4|(x&15))
s=Save(sys.argv[1]); _,d=s.unpack('map/map.bin'); d=bytearray(d); n=0
for y,x0,x1 in ((970,504,509),(971,510,515),(972,516,518),(973,519,528)):
    for x in range(x0,x1+1):
        t=struct.unpack_from('<I',d,off(x,y))[0]
        assert not (t>>21)&1 and t>>24==0, (x,y,hex(t))
        struct.pack_into('<I',d,off(x,y),(t&0x00ffffff)|(2<<27)|(7<<24)); n+=1
s.repack('map/map.bin',bytes(d)); assert not os.path.exists(sys.argv[2]); s.write(sys.argv[2]); print('lava tiles',n)
