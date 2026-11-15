import json, math, glob
exec(open('/home/hatch/workspace/makefun-btc-forecast/dev/tune.py').read().split("# pseudo-checkpoints")[0])

ckpts = []
for px in series:
    for idx in range(1440, 4040, 240):
        ckpts.append((px, idx))

def f_model(logp, beta=0.5, mode='fixed'):
    last = logp[-1]
    e = ema_last(logp, 1440)
    r24 = logp[-1] - logp[-1441]
    if mode == 'fixed':
        b = beta
    elif mode == 'trend_gate':   # revert less when trending hard
        b = beta * max(0.0, 1.0 - abs(r24)/0.04)
    elif mode == 'trend_gate2':
        b = beta * max(0.0, 1.0 - abs(r24)/0.02)
    move = -b*(last-e)
    move = max(-0.02, min(0.02, move))
    return math.exp(last+move)

def pseudo(fn):
    errs = [100*abs(fn([math.log(p) for p in px[:idx+1]])-px[idx+240]) for px, idx in ckpts]
    return sum(errs)/len(errs)

def real(fn):
    errs = []
    for k in range(5):
        px = series[k]; actual = series[k+1][-1]
        g = fn([math.log(p) for p in px])
        errs.append(100*abs(g-actual))
    return sum(errs)/len(errs)

for mode, beta in [('fixed',0.2),('fixed',0.3),('fixed',0.4),('fixed',0.5),
                   ('trend_gate',0.5),('trend_gate',0.7),('trend_gate2',0.5),('trend_gate2',0.7)]:
    print(f'{mode:12s} beta={beta}: pseudo {pseudo(lambda lp,m=mode,b=beta: f_model(lp,b,m)):8.0f}  real-practice {real(lambda lp,m=mode,b=beta: f_model(lp,b,m)):8.0f}')
print('persistence: pseudo 40950  real-practice 47055')
