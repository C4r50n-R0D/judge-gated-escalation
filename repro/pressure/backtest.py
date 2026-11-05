"""Back-test written without the pipeline: rebuild the main results from raw rows, then cut them in ways the paper's analysis did not.
Run by `repro/run.sh pressure`. Exact expectations over stored draws; task-cluster bootstrap."""
import json,collections,numpy as np,datetime as dt
rows=[];meta=0
for l in open('confirmatory.labeled.jsonl'):
    r=json.loads(l)
    if '_meta' in r: meta+=1
    else: rows.append(r)
tau=json.load(open('thresholds.json'))['taus']
power={tuple(k.split('|')[:2])+(int(k.split('|')[2]),):v for k,v in json.load(open('test_power.json')).items()}
print('rows',len(rows),'errors',sum(1 for r in rows if r.get('error')),'by split',collections.Counter(r['split'] for r in rows))
print('by tier/split',sorted(collections.Counter((r['tier'],r['split']) for r in rows).items()))
J=lambda r,j:r['judges'][j]
def build(rs,split):
    T={}
    for r in rs:
        if r['split']!=split: continue
        d=T.setdefault(r['task'],dict(L=[],S=[],suite=r['suite'],block=r.get('block')))
        if r['tier']=='local3b': d['L'].append(r)
        elif r['tier']=='strong14b': d['S'].append(r)
    return {k:v for k,v in T.items() if v['L'] and v['S']}
cost=lambda r:r['params_b']*(r['tokens_in']+r['tokens_out'])
def jc(r,j):
    if j in('selfconf','visible'): return 0.0
    q=J(r,j); return q['params_b']*q.get('tokens',0)
def per(T,gate):
    a=[];c=[];s=[];ra=[];rc=[];rs=[]
    for t,d in T.items():
        L,Sd=d['L'],d['S']
        sh=np.mean([r['hidden_passed'] for r in Sd]); sc=np.mean([cost(r) for r in Sd]); ss=np.mean([r['wall_s_net'] for r in Sd])
        if gate=='visible': A=[bool(r['visible_passed']) for r in L]
        else: A=[J(r,gate)['p']>=tau[gate] for r in L]
        h=[bool(r['hidden_passed']) for r in L]
        acc=np.mean([ (x if g else sh) for x,g in zip(h,A)])
        co=np.mean([cost(r)+jc(r,gate)+(0 if g else sc) for r,g in zip(L,A)])
        se=np.mean([r['wall_s_net']+(0 if gate in('visible','selfconf') else J(r,gate).get('wall',0))+(0 if g else ss) for r,g in zip(L,A)])
        a.append(acc-sh);c.append(co-sc);s.append(se-ss)
    return map(np.array,(a,c,s))
def verdict(T,gate,B=2000,seed=7):
    a,c,s=per(T,gate); n=len(a); rng=np.random.default_rng(seed); ix=rng.integers(0,n,(B,n))
    A=a[ix].mean(1);C=c[ix].mean(1)
    lo,hi=np.percentile(A,[2.5,97.5]);cl,ch=np.percentile(C,[2.5,97.5])
    ok=lo>-.03 and ch<0
    return f'n={n:3d} acc {a.mean()*100:+5.1f} [{lo*100:+5.1f},{hi*100:+5.1f}] cost {c.mean():+7.0f} [{cl:+7.0f},{ch:+7.0f}] sec {s.mean():+5.1f}  H2 {"PASS" if ok else "fail"+("-acc" if lo<=-.03 else "")+("-cost" if ch>=0 else "")}'
T=build(rows,'test'); C=build(rows,'cal')
print('\n== A reproduce main numbers (exact expectations)')
for g in ('tev','llama','selfconf','visible'): print(f'{g:9s}',verdict(T,g))
L=[r for d in T.values() for r in d['L']]; Sd=[r for d in T.values() for r in d['S']]
tl=np.mean([np.mean([r['hidden_passed'] for r in d['L']]) for d in T.values()]); ts=np.mean([np.mean([r['hidden_passed'] for r in d['S']]) for d in T.values()])
lc=np.mean([np.mean([cost(r) for r in d['L']]) for d in T.values()]); sc=np.mean([np.mean([cost(r) for r in d['S']]) for d in T.values()])
print(f'local acc {tl:.3f} strong {ts:.3f} gap {100*(ts-tl):.1f}; local cost {lc:.0f} strong {sc:.0f}')
tj=np.mean([np.mean([jc(r,"tev") for r in d['L']]) for d in T.values()]); tk=np.mean([J(r,'tev')['tokens'] for r in L])
print(f'tev label cost {tj:.0f} = {100*tj/sc:.1f}% of 14B; tokens {tk:.0f}; breakeven {100*(1-(lc+tj)/sc):.1f}%; 14B sec {np.mean([r["wall_s_net"] for r in Sd]):.2f} tev sec {np.mean([J(r,"tev")["wall"] for r in L]):.2f}')
def rate(R,f): return 100*np.mean([f(r) for r in R])
acc=lambda r:J(r,'tev')['p']>=tau['tev']
print(f'tev reject {100-rate(L,acc):.1f}%; rejected correct {rate([r for r in L if not acc(r)],lambda r:r["hidden_passed"]):.1f}%; accepted correct {rate([r for r in L if acc(r)],lambda r:r["hidden_passed"]):.1f}%')
print(f'visible reject {100-rate(L,lambda r:r["visible_passed"]):.1f}%; fail-visible correct {rate([r for r in L if not r["visible_passed"]],lambda r:r["hidden_passed"]):.1f}%; pass-visible correct {rate([r for r in L if r["visible_passed"]],lambda r:r["hidden_passed"]):.1f}%')
print(f'selfconf accept {rate(L,lambda r:J(r,"selfconf")["p"]>=tau["selfconf"]):.1f}%')
for s in ('humaneval+','mbpp+'):
    R=[r for r in L if r['suite']==s]; print(f'{s} tev reject {100-rate(R,acc):.1f}%')
print('prefill/decode medians',{t:(round(np.median([r['prefill_tps'] for r in Q if r.get('prefill_tps')])),float(round(np.median([r['decode_tps'] for r in Q if r.get('decode_tps')]),1))) for t,Q in (('3B',L),('14B',Sd))})
print('power of test draws',sorted(collections.Counter(power.values()).items()))
t0=sorted(r['ts'] for r in rows if r['split']=='test')
print('first test draw',t0[0],'last',t0[-1])
print('\n== B disjoint draws (never pooled)')
def sub(T,lr,sr):
    o={}
    for t,d in T.items():
        L2=[r for r in d['L'] if r['rep'] in lr]; S2=[r for r in d['S'] if r['rep'] in sr]
        if L2 and S2: o[t]=dict(d,L=L2,S=S2)
    return o
for nm,lr,sr in (('half1 L0-3 S0-1',{0,1,2,3},{0,1}),('half2 L4-7 S2-4',{4,5,6,7},{2,3,4})):
    H=sub(T,lr,sr)
    for g in ('tev','visible'): print(f'{nm} {g:8s}',verdict(H,g))
print('\n== C calibration split at frozen thresholds')
for g in ('tev','llama','selfconf','visible'): print(f'cal {g:9s}',verdict(C,g))
print('\n== D collection order, test blocks in quartiles')
bl=sorted({d['block'] for d in T.values() if d['block'] is not None}); print('blocks',len(bl),bl[:3],bl[-3:])
tasks=sorted(T,key=lambda t:(min(r['ts'] for r in T[t]['L']),t))
for q,ch in enumerate(np.array_split(tasks,4)):
    H={t:T[t] for t in ch}
    for g in ('tev','visible'): print(f'Q{q+1} {g:8s}',verdict(H,g))
jk=[]
for t_ in np.array_split(tasks,19):
    H={t:T[t] for t in tasks if t not in set(t_)}; a,c,_=per(H,'tev'); jk.append((a.mean()*100,c.mean()))
jk=np.array(jk); print(f'jackknife 19 blocks tev acc {jk[:,0].min():+.2f}..{jk[:,0].max():+.2f} cost {jk[:,1].min():+.0f}..{jk[:,1].max():+.0f}')
print('\n== E conditions: battery and draws near a model load')
R=[r for r in rows if r['split']=='test']
hwk=lambda r:power.get((r['tier'],r['task'],r['rep']),'')
print('test rows matched',sum(1 for r in R if (r['tier'],r['task'],r['rep']) in power),'battery',sum('Battery' in hwk(r) for r in R))
keep=[r for r in rows if 'Battery' not in hwk(r)]; H=build(keep,'test')
for g in ('tev','visible'): print('no battery',g,verdict(H,g))
for th in (0.1,0.5):
    n=sum((r.get('load_s') or 0)>th for r in R); keep=[r for r in rows if (r.get('load_s') or 0)<=th]; H=build(keep,'test'); print(f'load_s>{th}: {n} test draws of {len(R)}; removed:'); 
    for g in ('tev','visible'): print('  ',g,verdict(H,g))
print('\n== F placebo: random gate at the same accept rate, 200 runs')
ar=rate(L,acc)/100; rng=np.random.default_rng(3); res=[]
for _ in range(200):
    a=[];c=[]
    for d in T.values():
        sh=np.mean([r['hidden_passed'] for r in d['S']]); sc_=np.mean([cost(r) for r in d['S']]); A=rng.random(len(d['L']))<ar
        a.append(np.mean([(r['hidden_passed'] if g else sh) for r,g in zip(d['L'],A)])-sh); c.append(np.mean([cost(r)+(jc(r,'tev'))+(0 if g else sc_) for r,g in zip(d['L'],A)])-sc_)
    res.append((np.mean(a)*100,np.mean(c)))
res=np.array(res); print(f'random gate at {ar:.3f} acc {res[:,0].mean():+.1f} (sd {res[:,0].std():.2f}) cost {res[:,1].mean():+.0f}; tev beat it in {100*np.mean(res[:,0]<-0.4):.0f}% of runs')
