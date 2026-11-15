import json, math, glob
exec(open('/home/hatch/workspace/makefun-btc-forecast/dev/tune.py').read().split("# pseudo-checkpoints")[0])

ckpts = []
for px in series:
    for idx in range(1440, 4040, 240):
        ckpts.append((px, idx))

def score(params):
    errs = []
    for px, idx in ckpts:
        logp = [math.log(p) for p in px[:idx+1]]
        g = forecast(logp, params)
        errs.append(100*abs(g-px[idx+240]))
    return sum(errs)/len(errs)

best = []
for span in (720, 1080, 1440, 2160, 2880, 4320):
    for beta in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        m = score((beta, 0.0, 0.0, span, 0.02))
        best.append((m, span, beta))
best.sort()
for m, span, beta in best[:12]:
    print(f'ema{span} beta={beta}: mean {m:.0f}')
