import json, math, glob

def load(path):
    d = json.load(open(path))
    return d['markets'][0]['prices']

series = [load(f) for f in sorted(glob.glob('/home/hatch/workspace/makefun-btc-forecast/kit/btc-cent-forecast-01-kit/input/p*.in'))]

def ema_last(logp, span):
    a = 2.0/(span+1)
    e = logp[0]
    for x in logp[1:]:
        e = a*x + (1-a)*e
    return e

def ema_series(logp, span):
    a = 2.0/(span+1)
    out = [logp[0]]
    for x in logp[1:]:
        out.append(a*x + (1-a)*out[-1])
    return out

def forecast(logp, params):
    beta, gamma, delta, ema_span, cap = params
    n = len(logp)
    last = logp[-1]
    e = ema_last(logp, ema_span)
    r4h = logp[-1] - logp[-241] if n > 241 else 0.0
    r24h = logp[-1] - logp[-1441] if n > 1441 else 0.0
    # mean reversion toward EMA + momentum on 4h return + small trend from 24h
    move = -beta*(last - e) + gamma*r4h + delta*r24h
    move = max(-cap, min(cap, move))
    return math.exp(last + move)

def score_model(params, checkpoints):
    errs = []
    for px, idx in checkpoints:
        logp = [math.log(p) for p in px[:idx+1]]
        g = forecast(logp, params)
        actual = px[idx+240]
        errs.append(100*abs(g-actual))
    return sum(errs)/len(errs), max(errs)

# pseudo-checkpoints: every 4h from minute 1440 to 4080 within each series
ckpts = []
for px in series:
    for idx in range(1440, 4040, 240):
        ckpts.append((px, idx))
print('pseudo cases:', len(ckpts))

# persistence baseline
def persist(px, idx):
    return px[idx]
errs = [100*abs(persist(px, idx)-px[idx+240]) for px, idx in ckpts]
print('persistence: mean %.0f  worst %.0f' % (sum(errs)/len(errs), max(errs)))

cands = {
 'ema-rev b=0.3 ema1440': (0.3, 0.0, 0.0, 1440, 0.02),
 'ema-rev b=0.5 ema1440': (0.5, 0.0, 0.0, 1440, 0.02),
 'ema-rev b=0.5 ema720':  (0.5, 0.0, 0.0, 720, 0.02),
 'ema-rev b=0.8 ema1440': (0.8, 0.0, 0.0, 1440, 0.02),
 'mom g=0.2':            (0.0, 0.2, 0.0, 1440, 0.02),
 'mom g=0.4':            (0.0, 0.4, 0.0, 1440, 0.02),
 'mom g=-0.2 (rev4h)':   (0.0,-0.2, 0.0, 1440, 0.02),
 'rev+mom b.5 g.2':      (0.5, 0.2, 0.0, 1440, 0.02),
 'rev+mom b.5 g.2 d.05': (0.5, 0.2, 0.05, 1440, 0.02),
 'rev+mom b.3 g.3 d.1':  (0.3, 0.3, 0.10, 1440, 0.02),
 'trend d=0.15':         (0.0, 0.0, 0.15, 1440, 0.02),
 'trend d=0.3':          (0.0, 0.0, 0.30, 1440, 0.02),
 'rev b.5 + trend d.1':  (0.5, 0.0, 0.10, 1440, 0.02),
}
for name, p in cands.items():
    m, w = score_model(p, ckpts)
    print(f'{name:28s} mean {m:8.0f}  worst {w:8.0f}')
