"""Adversarial reanalysis of the confirmatory data. Exact expectations, numpy, no model calls.
Everything here is post hoc. Usage: python pressure.py [--data DIR]"""
import json,gzip,sys,ast,collections
import numpy as np
D=sys.argv[sys.argv.index('--data')+1] if '--data' in sys.argv else '.'
TH=json.load(open(f'{D}/thresholds.json')); TAU=TH['taus']; DELTA=.03
rows=[r for r in map(json.loads,open(f'{D}/confirmatory.labeled.jsonl')) if '_meta' not in r]
J=['tev','llama','selfconf']
def tc(d): return d['params_b']*(d['tokens_in']+d['tokens_out'])
def sec(d): return d['wall_s_net'] if d.get('wall_s_net') is not None else d['wall_s']
by=collections.defaultdict(lambda:collections.defaultdict(list)); suite={}; split={}
for r in rows: by[r['task']][r['tier']].append(r); suite[r['task']]=r['suite']; split[r['task']]=r['split']
tasks=sorted(by); idx={t:i for i,t in enumerate(tasks)}; N=len(tasks)
def arr(tier,f,k): 
    A=np.full((N,k),np.nan)
    for t in tasks:
        for i,d in enumerate(sorted(by[t][tier],key=lambda r:r['rep'])): A[idx[t],i]=f(d)
    return A
LOC='local3b'
h=arr(LOC,lambda d:float(d['hidden_passed']),8); v=arr(LOC,lambda d:float(d['visible_passed']),8)
gt=arr(LOC,tc,8); gs=arr(LOC,sec,8)
P={j:arr(LOC,lambda d:d['judges'][j]['p'],8) for j in J}
JT={j:arr(LOC,lambda d:(d['judges'][j].get('params_b') or 0)*(d['judges'][j].get('tokens') or 0),8) for j in J}
JS={j:arr(LOC,lambda d:d['judges'][j].get('wall') or 0,8) for j in J}
sh=np.nanmean(arr('strong14b',lambda d:float(d['hidden_passed']),5),1); st=np.nanmean(arr('strong14b',tc,5),1); ss=np.nanmean(arr('strong14b',sec,5),1)
test=np.array([split[t]=='test' for t in tasks]); cal=~test
he=np.array([suite[t]=='humaneval+' for t in tasks])
def rr(acc,jt=0,js=0,gt_=None,st_=None):
    """Per-task (accuracy, token-compute, seconds) of gate->reroute given accept matrix acc."""
    a=acc.astype(float); G=gt if gt_ is None else gt_; S=st if st_ is None else st_
    return (a*h+(1-a)*sh[:,None]).mean(1),(G+jt+(1-a)*S[:,None]).mean(1),(gs+js+(1-a)*ss[:,None]).mean(1)
rng=np.random.default_rng(20261104)
def ci(x,B=4000):
    n=len(x); b=x[rng.integers(0,n,(B,n))].mean(1); return x.mean(),np.percentile(b,2.5),np.percentile(b,97.5)
def f(c,s=1,d=1): return f'{c[0]*s:+.{d}f} [{c[1]*s:+.{d}f}, {c[2]*s:+.{d}f}]'
def h2(acc,sel,jt=0,js=0,label='',S=None,G=None,cost_s=None):
    a,c,s=rr(acc,jt,js,G,S)
    ca=ci((a-sh)[sel],); cc=ci((c-(st if S is None else S))[sel])
    ok=ca[1]>-DELTA and cc[2]<0
    print(f'{label:44s} acc {f(ca,100)}  compute {f(cc,1,0)}  H2 {"PASS" if ok else "fail"}')
    return ca,cc,ok
print('== 0 baseline (test split, exact) ==')
A={j:P[j]>=TAU[j] for j in J}; A['visible']=v>0
for j in A: h2(A[j],test,JT.get(j,0),JS.get(j,0),j)
print('\n== 1 by suite ==')
for nm,m in (('HumanEval+',he&test),('MBPP+',(~he)&test)):
    print(nm,m.sum(),'tasks; reject tev',round(1-A['tev'][m].mean(),3),'break-even',round(1-(gt[m].mean()+JT['tev'][m].mean())/st[m].mean(),3))
    for j in ('tev','visible'): h2(A[j],m,JT.get(j,0),JS.get(j,0),'  '+j)
print('\n== 2 cost-metric sensitivity, tev gate ==')
Ot=arr(LOC,lambda d:d['params_b']*d['tokens_out'],8); So=np.nanmean(arr('strong14b',lambda d:d['params_b']*d['tokens_out'],5),1)
for w in (1,.75,.5,.25,0): h2(A['tev'],test,JT['tev']*w,JS['tev']*w,f'judge charged at {w:.0%}')
h2(A['tev'],test,JT['tev'],JS['tev'],'generated tokens only for generators',S=So,G=Ot)
for e in (.5,2):
    g=arr(LOC,lambda d:d['params_b']**e*(d['tokens_in']+d['tokens_out']),8); s_=np.nanmean(arr('strong14b',lambda d:d['params_b']**e*(d['tokens_in']+d['tokens_out']),5),1)
    jt=arr(LOC,lambda d:(d['judges']['tev']['params_b'])**e*d['judges']['tev']['tokens'],8)
    h2(A['tev'],test,jt,0,f'cost ~ params^{e}',S=s_,G=g)
a,c,s=rr(A['tev'],JT['tev'],JS['tev']); print('seconds tev-strong',f(ci((s-ss)[test]),1,2))
print('\n== 3 threshold-rule sensitivity: rule on calibration, gate on test ==')
def fit(j,cidx,rule,B=1000,grid=None):
    p=P[j][cidx]; c=np.unique(p) if grid is None else grid
    bi=np.random.default_rng(1).integers(0,cidx.sum(),(B,cidx.sum()))
    best=None
    for t in c:
        ac=P[j][cidx]>=t
        a=(ac*h[cidx]+(~ac)*sh[cidx,None]).mean(1)-sh[cidx]
        cost=(gt[cidx]+JT[j][cidx]+(~ac)*st[cidx,None]).mean()
        lb=np.percentile(a[bi].mean(1),2.5)
        val={'lb_half':lb>=-DELTA/2,'lb_full':lb>=-DELTA,'pt_half':a.mean()>=-DELTA/2,'pt_full':a.mean()>=-DELTA,'pt_zero':a.mean()>=0}[rule]
        if val and (best is None or cost<best[0]): best=(cost,t)
    return None if best is None else best[1]
for j in ('tev','llama'):
    for rule in ('lb_half','lb_full','pt_half','pt_full','pt_zero'):
        t=fit(j,cal,rule)
        print(f'{j} {rule:8s} tau {t:.3f} reject {1-(P[j][test]>=t).mean():.2f}',end='  ')
        h2(P[j]>=t,test,JT[j],JS[j],'')
print('\n== 4 descriptive sweep on test: does ANY tev tau pass H2? ==')
ps=np.unique(np.quantile(P['tev'][test],np.linspace(.005,.995,200))); ok=[]
for t in ps:
    a,c,_=rr(P['tev']>=t,JT['tev'],JS['tev']); ca=ci((a-sh)[test],1500); cc=ci((c-st)[test],1500)
    if ca[1]>-DELTA and cc[2]<0: ok.append((t,ca[0],cc[0]))
print(len(ok),'of',len(ps),'taus pass;', ('tau range %.3f-%.3f, acc %+.1f to %+.1f pts, compute %+.0f to %+.0f'%(ok[0][0],ok[-1][0],min(o[1] for o in ok)*100,max(o[1] for o in ok)*100,min(o[2] for o in ok),max(o[2] for o in ok))) if ok else '')
print('\n== 5 resplit stability: 200 random 171/371 splits, frozen rule (coarse) ==')
r2=np.random.default_rng(7); res=[];resv=[]
grid=np.unique(np.quantile(P['tev'],np.linspace(.01,.99,80)))
for i in range(200):
    pm=r2.permutation(N); c_=np.zeros(N,bool); c_[pm[:171]]=True; t_=~c_
    t=fit('tev',c_,'lb_half',B=300,grid=grid)
    if t is None: res.append((np.nan,)*5); continue
    a,c,_=rr(P['tev']>=t,JT['tev'],JS['tev'])
    bi=r2.integers(0,371,(800,371)); da=(a-sh)[t_][bi].mean(1); dc=(c-st)[t_][bi].mean(1)
    res.append((t,(a-sh)[t_].mean(),(c-st)[t_].mean(),np.percentile(da,2.5),np.percentile(dc,97.5)))
    va,vc,_=rr(v>0); dv=(va-sh)[t_][bi].mean(1); dvc=(vc-st)[t_][bi].mean(1); resv.append(np.percentile(dv,2.5)>-DELTA and np.percentile(dvc,97.5)<0)
R=np.array(res); print('tev tau median %.3f IQR %.3f-%.3f'%(np.nanmedian(R[:,0]),*np.nanpercentile(R[:,0],[25,75])))
print('tev acc diff pts median %+.2f, range %+.2f..%+.2f; compute median %+.0f range %+.0f..%+.0f'%(np.nanmedian(R[:,1])*100,np.nanmin(R[:,1])*100,np.nanmax(R[:,1])*100,np.nanmedian(R[:,2]),np.nanmin(R[:,2]),np.nanmax(R[:,2])))
print('tev H2 pass share %.3f; point estimate cheaper share %.3f; noninferior share %.3f'%(((R[:,3]>-DELTA)&(R[:,4]<0)).mean(),(R[:,2]<0).mean(),(R[:,3]>-DELTA).mean()));print('visible H2 pass share',np.mean(resv))
print('\n== 6 exclusions and influence ==')
drop=np.array([t in('HumanEval/32','Mbpp/255') for t in tasks]); h2(A['tev'],test&~drop,JT['tev'],JS['tev'],'tev, without 2 always-fail tasks'); h2(A['visible'],test&~drop,label='visible, without 2 always-fail tasks')
_,c,_=rr(A['tev'],JT['tev'],JS['tev']); d=(c-st)[test]; a,_,_=rr(A['tev'],JT['tev'],JS['tev']); 
o=np.argsort(d); 
for k in (1,5,10,18):
    print(f'drop {k} tasks where tev cost most: compute {f(ci(np.delete(d,o[-k:])),1,0)}; drop {k} where cheapest: {f(ci(np.delete(d,o[:k])),1,0)}')
print('per-replicate (draft rep r only, one 14B mean):')
for r_ in range(8):
    ac=(P['tev'][:,r_]>=TAU['tev']); aa=(ac*h[:,r_]+(~ac)*sh); cc=gt[:,r_]+JT['tev'][:,r_]+(~ac)*st
    print(f' rep{r_} acc {((aa-sh)[test]).mean()*100:+.1f} compute {((cc-st)[test]).mean():+.0f}',end=';')
print()
print('\n== 7 margin sensitivity ==')
for dl in (.01,.015,.02,.03):
    print(dl,{j:bool(ci((rr(A[j],JT.get(j,0))[0]-sh)[test])[1]>-dl) for j in A})
print('\n== 8 how expensive could tests be? ==')
a,c,s=rr(A['visible']); print('saving per task: compute',round(-(c-st)[test].mean()),'seconds',round(-(s-ss)[test].mean(),1), 'upper-bound-preserving compute charge',round(-ci((c-st)[test])[2]))
print('vs tev: visible wins compute until test charge',round((rr(A['tev'],JT['tev'])[1]-c)[test].mean()))
print('\n== 9 weak tests: gate on first k original tests only ==')
ev={}
for fn in ('s1_he','s1_mb','s2_he','s2_mb'):
    for t,L in json.load(open(f'{D}/{fn}_eval_results.json'))['eval'].items():
        for e in L: ev.setdefault(t,{})[e['solution']]=e
base={}
for fn in ('HumanEvalPlus-v0.1.10.jsonl.gz','MbppPlus-v0.2.0.jsonl.gz'):
    for l in gzip.open(f'{D}/{fn}','rt'):
        x=json.loads(l); base[x['task_id']]=(x['base_input'],x['prompt'])
def ctx(t,code):
    for s,e in ev[t].items():
        if s.endswith(code): return e
    return None
ff=np.full((N,8),9999.); unk=np.zeros((N,8),bool); miss=0
for t in tasks:
    for r_ in sorted(by[t][LOC],key=lambda r:r['rep']):
        i=idx[t]; k=r_['rep']; e=ctx(t,r_['code'] or '')
        if e is None: miss+=1; continue
        if e['base_status']=='pass': continue
        ft=e['base_fail_tests']; ft=ast.literal_eval(ft) if isinstance(ft,str) else ft
        if not ft: unk[i,k]=True; ff[i,k]=0; continue
        try: ff[i,k]=base[t][0].index(ft[0])
        except ValueError: unk[i,k]=True; ff[i,k]=0
print('unmatched',miss,'failed-without-a-recorded-test',int(unk[test].sum()),'of',int((v[test]==0).sum()),'failed drafts')
nb=np.array([len(base[t][0]) for t in tasks]); print('base tests per task median',np.median(nb[test]),'HE',np.median(nb[test&he]),'MBPP',np.median(nb[test&~he]))
for k in (1,2,3,5,10):
    acc=ff>=k
    h2(acc,test,label=f'first {k} test(s), unknown failures reject')
    acc2=(ff>=k)|unk
    h2(acc2,test,label=f'first {k} test(s), unknown failures accept')
acc=ff>=1
print('k=1 false accept among wrong drafts',round(acc[test][h[test]==0].mean(),3),'visible',round((v>0)[test][h[test]==0].mean(),3),'tev',round(A['tev'][test][h[test]==0].mean(),3),'reject',round(1-acc[test].mean(),3))
print('k=1 by suite');
for nm,m in (('HE',he&test),('MBPP',(~he)&test)): h2(ff>=1,m,label='  '+nm)
print('\n== 10 what judge skill would be needed? (synthetic judge, tev call price) ==')
for nm,th in (('oracle judge at tev price',0),):
    h2(h>0,test,JT['tev'],JS['tev'],nm)
