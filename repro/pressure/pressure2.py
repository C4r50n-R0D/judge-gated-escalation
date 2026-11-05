import sys; sys.argv=['x']
src=open('pressure.py').read().split("print('== 0 baseline")[0]
exec(src)
A={j:P[j]>=TAU[j] for j in J}; A['visible']=v>0
print('== a input-token discount: all prompt tokens weighted w (generators and judges) ==')
for w in (1,.75,.5,.25,.1):
    G=arr(LOC,lambda d:d['params_b']*(w*d['tokens_in']+d['tokens_out']),8); S_=np.nanmean(arr('strong14b',lambda d:d['params_b']*(w*d['tokens_in']+d['tokens_out']),5),1)
    h2(A['tev'],test,JT['tev']*w,0,f'tev, prompt tokens x {w}',S=S_,G=G); 
print('== b judge price: exact point where tev stops failing ==')
for w in (.95,.9,.875,.85,.825,.8):
    h2(A['tev'],test,JT['tev']*w,0,f'tev price x {w}')
print('mean tokens per tev label',round((JT['tev'][test]/4.2).mean(),0),'token-compute',round(JT['tev'][test].mean()))
print('== c decomposition (compute vs 14B) ==')
h2(A['tev'],test,JT['tev'],0,'tev'); h2(A['tev'],test,0,0,'tev, free labels'); h2(h>0,test,JT['tev'],0,'perfect judge, tev price'); h2(h>0,test,0,0,'perfect judge, free labels')
print('== d per-suite thresholds, frozen rule on suite calibration tasks ==')
def fit(j,cidx,rule='lb',B=1000,seed=1,dl=DELTA/2):
    c=np.unique(P[j][cidx]); bi=np.random.default_rng(seed).integers(0,cidx.sum(),(B,cidx.sum())); best=None
    for t in c:
        ac=P[j][cidx]>=t; a=(ac*h[cidx]+(~ac)*sh[cidx,None]).mean(1)-sh[cidx]
        cost=(gt[cidx]+JT[j][cidx]+(~ac)*st[cidx,None]).mean()
        if np.percentile(a[bi].mean(1),2.5)>=-dl and (best is None or cost<best[0]): best=(cost,t)
    return best[1]
th=np.where(he,fit('tev',cal&he),fit('tev',cal&~he)); print('tau HE',round(fit('tev',cal&he),3),'MBPP',round(fit('tev',cal&~he),3), 'cal tasks',(cal&he).sum(),(cal&~he).sum())
acc=P['tev']>=th[:,None]
h2(acc,test,JT['tev'],0,'tev, per-suite thresholds'); h2(acc,test&he,JT['tev'],0,'   HumanEval+'); h2(acc,test&~he,JT['tev'],0,'   MBPP+')
print('== e same rule, different bootstrap seeds (20) ==')
out=[]
for s in range(20):
    t=fit('tev',cal,seed=100+s,B=1000); a,c,_=rr(P['tev']>=t,JT['tev'],0); out.append((t,(a-sh)[test].mean()*100,(c-st)[test].mean(),np.percentile((c-st)[test][np.random.default_rng(s).integers(0,371,(2000,371))].mean(1),97.5)))
O=np.array(out); print('tau values',np.round(sorted(set(O[:,0])),3)); print('acc',O[:,1].min().round(2),O[:,1].max().round(2),'compute',O[:,2].min().round(0),O[:,2].max().round(0),'upper bound <0 in',(O[:,3]<0).sum(),'of 20')
