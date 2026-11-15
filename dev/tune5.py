import json, math, glob, statistics
exec(open('/home/hatch/workspace/makefun-btc-forecast/dev/tune.py').read().split("# pseudo-checkpoints")[0])

ckpts = []
for px in series:
    for idx in range(1440, 4040, 240):
        ckpts.append((px, idx))

def f_model(logp, beta=0.3, dead=0.0):
    last = logp[-1]
    e = ema_last(logp, 1440)
    d = last - e
    if dead and abs(d) > dead:
        d = math.copysign(abs(d)-dead, d)
    elif dead:
        d = 0.0
    move = -beta*d
    move = max(-0.02, min(0.02, move))
    return math.exp(last+move)

def eval_all(fn):
    pe, re_ = [], []
    for px, idx in ckpts:
        g = fn([math.log(p) for p in px[:idx+1]])
        pe.append(100*abs(g-px[idx+240]))
    for k in range(5):
        px = series[k]; actual = series[k+1][-1]
        g = fn([math.log(p) for p in px])
        re_.append(100*abs(g-actual))
    return sum(pe)/len(pe), sum(re_)/len(re_)

# paired diff stats for beta 0.3 vs persistence on pseudo
diffs = []
for px, idx in ckpts:
    lp = [math.log(p) for p in px[:idx+1]]
    e_m = 100*abs(f_model(lp, 0.3)-px[idx+240])
    e_p = 100*abs(px[idx]-px[idx+240])
    diffs.append(e_m - e_p)
print('beta0.3 vs persist pseudo: mean diff %.0f  se %.0f  wins %d/66' % (
    statistics.mean(diffs), statistics.stdev(diffs)/math.sqrt(len(diffs)), sum(1 for d in diffs if d<0)))

for beta, dead in [(0.25,0.0),(0.3,0.0),(0.35,0.0),(0.3,0.001),(0.3,0.002),(0.4,0.002),(0.5,0.002)]:
    p, r = eval_all(lambda lp,b=beta,d=dead: f_model(lp,b,d))
    print(f'beta={beta} dead={dead}: pseudo {p:8.0f}  real {r:8.0f}')
