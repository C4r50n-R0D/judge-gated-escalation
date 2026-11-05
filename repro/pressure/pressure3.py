import sys; sys.argv=['x']
src=open('pressure.py').read().split("print('== 0 baseline")[0]
exec(src)
fx={}
for r in json.load(open('strip_out.json')):
    if r.get('stripped_hidden'): fx[(r['task'],r['solution'])]=1
for r in json.load(open('mods_out.json')):
    if r['hidden']: fx[(r['task'],r['solution'])]=1
print('corrected distinct',len(fx))
ev={}
for fn in ('s2_he','s2_mb'):
    for t,L in json.load(open(f'{fn}_eval_results.json'))['eval'].items():
        for e in L:
            if (t,e['solution']) in fx: ev.setdefault(t,set()).add(e['solution'])
def cor(tier):
    n=0
    for t in tasks:
        for d in by[t][tier]:
            if d['split']=='test' and not d['hidden_passed'] and t in ev and any(s.endswith(d['code'] or '@@') for s in ev[t]):
                d['hidden_passed']=True; d['visible_passed']=True; n+=1
    return n
print('rows flipped',{t:cor(t) for t in ('local3b','strong14b','local7b','local1p5b')})
h2_=arr(LOC,lambda d:float(d['hidden_passed']),8); v2=arr(LOC,lambda d:float(d['visible_passed']),8); sh2=np.nanmean(arr('strong14b',lambda d:float(d['hidden_passed']),5),1)
print('3B acc',h[test].mean().round(4),'->',h2_[test].mean().round(4),'14B',sh[test].mean().round(4),'->',sh2[test].mean().round(4))
h=h2_; sh=sh2; v=v2
for j in J: h2(P[j]>=TAU[j],test,JT[j],0,j+' (corrected labels)')
h2(v>0,test,label='visible (corrected labels)')
