import json, math, glob

def load(path):
    d = json.load(open(path))
    return d['case'], d['at'], d['markets'][0]['prices']

cases = {}
for f in sorted(glob.glob('/home/hatch/workspace/makefun-btc-forecast/kit/btc-cent-forecast-01-kit/input/p*.in')):
    cid, at, px = load(f)
    cases[cid] = (at, px)
    print(cid, at, 'n=', len(px), 'first=%.2f last=%.2f' % (px[0], px[-1]))

# Real practice targets: p0k target = last price of p0(k+1) (checkpoint +4h)
for k in range(5):
    a = cases[f'p0{k}'][1][-1]
    b = cases[f'p0{k+1}'][1][-1]
    print(f'p0{k}: checkpoint {a:.2f} -> actual {b:.2f}  move {(b/a-1)*100:+.3f}%  persist err {abs(b-a)*100:.0f} cents')
