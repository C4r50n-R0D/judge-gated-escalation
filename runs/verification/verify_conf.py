"""Independent recomputation of the confirmatory results. Shares no code with controllers.py.
Uses exact per-task expectations (no Monte Carlo) and its own bootstrap."""
import json, random, itertools, hashlib, math, collections
F='runs/confirmatory.labeled.jsonl'
T=json.load(open('thresholds.json'))['taus']
by=collections.defaultdict(lambda: collections.defaultdict(list)); split={}; n=0
for l in open(F):
    r=json.loads(l)
    if '_meta' in r: continue
    n+=1; by[r['task']][r['tier']].append(r); split[r['task']]=r['split']
    assert not r['error'] and r['hidden_passed'] is not None and r['visible_passed'] is not None
def tc(d): return d['params_b']*(d['tokens_in']+d['tokens_out'])
def sec(d): return d['wall_s_net'] if d.get('wall_s_net') is not None else d['wall_s']
def gt(d,j):
    x=d['judges'][j]; return (x.get('params_b') or 0)*(x.get('tokens') or 0)
def gs(d,j): return d['judges'][j].get('wall') or 0
def acc_gate(d,g):
    if g=='vis': return bool(d['visible_passed'])
    if g=='orc': return bool(d['hidden_passed'])
    return d['judges'][g]['p']>=T[g]
def score(d,g):
    if g=='vis': return float(bool(d['visible_passed']))
    if g=='orc': return float(bool(d['hidden_passed']))
    return d['judges'][g]['p']
def jcost(d,g): return (0,0) if g in('vis','orc') else (gt(d,g),gs(d,g))
M=lambda x: sum(x)/len(x)
def reroute(L,S,g):
    sa,st,ss=M([float(d['hidden_passed']) for d in S]),M([tc(d) for d in S]),M([sec(d) for d in S])
    a=t=s=0
    for d in L:
        c,w=jcost(d,g); t+=tc(d)+c; s+=sec(d)+w
        if acc_gate(d,g): a+=d['hidden_passed']
        else: a+=sa; t+=st; s+=ss
    k=len(L); return a/k,t/k,s/k
def resample(L,g,k=3):
    # exact over ordered k-subsets
    a=0;N=0
    for o in itertools.permutations(L,k):
        N+=1; best=None; res=None
        for d in o:
            if acc_gate(d,g): res=float(d['hidden_passed']); break
            if best is None or score(d,g)>best[0]: best=(score(d,g),d)
        a+= res if res is not None else float(best[1]['hidden_passed'])
    return a/N
def only(X): return M([float(d['hidden_passed']) for d in X]),M([tc(d) for d in X]),M([sec(d) for d in X])
names=sorted(t for t in by if split[t]=='test'); print('rows',n,'test tasks',len(names),'cal',sum(v=='cal' for v in split.values()))
rnd=random.Random(99173); B=2000
idx=[[rnd.randrange(len(names)) for _ in names] for _ in range(B)]
def ci(v):
    b=sorted(M([v[i] for i in ix]) for ix in idx); return M(v),b[int(.025*B)],b[int(.975*B)]
def show(lbl,v,s=1): m,l,h=ci(v); print(f'{lbl:46s} {m*s:9.3f} [{l*s:9.3f},{h*s:9.3f}]')
for loc in ['local3b','local7b','local1p5b']:
    print('=====',loc)
    L={t:by[t][loc] for t in names}; S={t:by[t]['strong14b'] for t in names}
    base=[only(L[t]) for t in names]; st=[only(S[t]) for t in names]
    print('local acc/tok/sec',[round(M([b[i] for b in base]),3) for i in range(3)]); print('strong',[round(M([b[i] for b in st]),3) for i in range(3)])
    if loc=='local3b': show('strong-local gap pts',[a[0]-b[0] for a,b in zip(st,base)],100)
    for g in ['tev','llama','selfconf','vis','orc']:
        R=[reroute(L[t],S[t],g) for t in names]
        print(g,'reroute',[round(M([r[i] for r in R]),3) for i in range(3)])
        show(g+' acc diff pts',[r[0]-s[0] for r,s in zip(R,st)],100)
        show(g+' tok diff',[r[1]-s[1] for r,s in zip(R,st)])
        show(g+' sec diff',[r[2]-s[2] for r,s in zip(R,st)])
        if g!='orc' :
            RS=[resample(L[t],g) for t in names]
            show(g+' H3 reroute-resample pts',[r[0]-s for r,s in zip(R,RS)],100)
    # H1
    def auc(j,sel):
        p=[];q=[]
        for t in sel:
            for d in L[t]: (p if d['hidden_passed'] else q).append(d['judges'][j]['p'])
        q.sort(); import bisect
        return sum(bisect.bisect_left(q,x)+(bisect.bisect_right(q,x)-bisect.bisect_left(q,x))/2 for x in p)/(len(p)*len(q))
    for j in ['tev','llama','selfconf']:
        v=auc(j,names); bs=sorted(auc(j,[names[i] for i in ix]) for ix in idx[:400]); print(j,'AUROC',round(v,3),'~CI',round(bs[10],3),round(bs[389],3))
    # mechanism
    D=[d for t in names for d in L[t]]
    for g in ['tev','llama','selfconf','vis']:
        rej=[d for d in D if not acc_gate(d,g)]; ac=[d for d in D if acc_gate(d,g)]
        print(g,f'reject {len(rej)/len(D):.3f} correct-among-rej {M([float(d["hidden_passed"]) for d in rej]):.3f} P(hidden|acc) {M([float(d["hidden_passed"]) for d in ac]):.3f}')
    print('hidden&!visible',sum(1 for d in D if d['hidden_passed'] and not d['visible_passed']))
    if loc=='local3b':
        g=M([gt(d,'tev') for d in D]); l=M([tc(d) for d in D]); s=M([tc(d) for t in names for d in S[t]])
        print('tev label',round(g,1),'frac14B',round(g/s,3),'l',round(l,1),'s',round(s,1),'breakeven r',round(1-(l+g)/s,3))
        # H4
        def far(t):
            w=[d for d in L[t] if not d['hidden_passed']]; return w
        hard=[t for t in names if M([float(d['hidden_passed']) for d in L[t]])<=1/3]
        f=lambda ts: M([float(acc_gate(d,'tev')) for t in ts for d in L[t] if not d['hidden_passed']])
        print('H4 hard n',len(hard),'FA hard',round(f(hard),3),'other',round(f([t for t in names if t not in hard]),3))
        R=[reroute(L[t],S[t],'tev') for t in names]; show('S1 tev-local pts',[r[0]-b[0] for r,b in zip(R,base)],100); print('S1 tok',round(M([r[1]-b[1] for r,b in zip(R,base)]),0))
        Rv=[reroute(L[t],S[t],'vis') for t in names]; show('tev-visible pts',[r[0]-v[0] for r,v in zip(R,Rv)],100)
# split
m=json.load(open('split_manifest.json'))
ok=all(split.get(i)==s for i,s in m['pairs']); print('split rows match manifest',ok)
SALT=m['salt']; chk=all((int(hashlib.sha256(f"{SALT}|{i}".encode()).hexdigest()[:8],16)/0x100000000<m['cal_fraction'])==(s=='cal') for i,s in m['pairs']); print('split hash recomputed',chk)
c=collections.Counter(t.split('/')[0] for t in split); print(c)
