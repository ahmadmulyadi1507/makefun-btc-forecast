import json, math, glob, statistics
exec(open('/home/hatch/workspace/makefun-btc-forecast/dev/tune.py').read().split("# pseudo-checkpoints")[0])

ckpts = []
for px in series:
    for idx in range(1440, 4040, 240):
        ckpts.append((px, idx))

def forecast2(logp, b24=0.5, b6=0.0, cap=0.02, anchor='ema'):
    last = logp[-1]
    if anchor == 'ema':
        a24 = ema_last(logp, 1440)
        a6 = ema_last(logp, 360)
    elif anchor == 'sma':
        a24 = sum(logp[-1440:])/1440
        a6 = sum(logp[-360:])/360
    elif anchor == 'median':
        a24 = statistics.median(logp[-1440:])
        a6 = statistics.median(logp[-360:])
    move = -b24*(last-a24) - b6*(last-a6)
    move = max(-cap, min(cap, move))
    return math.exp(last+move)

def score(fn):
    errs = [100*abs(fn([math.log(p) for p in px[:idx+1]])-px[idx+240]) for px, idx in ckpts]
    return sum(errs)/len(errs)

print('base ema1440 b.5        :', round(score(lambda lp: forecast2(lp))))
print('b.5 + b6=0.2            :', round(score(lambda lp: forecast2(lp, b6=0.2))))
print('b.5 + b6=0.4            :', round(score(lambda lp: forecast2(lp, b6=0.4))))
print('b.4 + b6=0.2            :', round(score(lambda lp: forecast2(lp, b24=0.4, b6=0.2))))
print('b.5 cap 0.01            :', round(score(lambda lp: forecast2(lp, cap=0.01))))
print('b.5 cap 0.03            :', round(score(lambda lp: forecast2(lp, cap=0.03))))
print('sma b.5                 :', round(score(lambda lp: forecast2(lp, anchor='sma'))))
print('median b.5              :', round(score(lambda lp: forecast2(lp, anchor='median'))))
print('sma b.5 + b6 .2         :', round(score(lambda lp: forecast2(lp, b6=0.2, anchor='sma'))))

# real practice cases p00-p04 (targets = next case last price)
print()
print('REAL practice (p00-p04):')
for k in range(5):
    px = series[k]; actual = series[k+1][-1]
    logp = [math.log(p) for p in px]
    g = forecast2(logp)
    print(f"p0{k}: guess {g:.2f} actual {actual:.2f} err {100*abs(g-actual):.0f} vs persist {100*abs(px[-1]-actual):.0f}")
