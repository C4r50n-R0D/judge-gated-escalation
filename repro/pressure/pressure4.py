import sys; sys.argv=['x']
src=open('pressure.py').read().split("print('== 0 baseline")[0]
exec(src)
A=P['tev']>=TAU['tev']
print('== prompt vs generated token speed, medians (stored) ==')
for t in ('local3b','strong14b'):
    R=[d for d in rows if d['tier']==t and d['split']=='test' and d.get('prefill_tps') and d.get('decode_tps')]
    print(t,'prefill',round(np.median([d['prefill_tps'] for d in R])),'decode',round(np.median([d['decode_tps'] for d in R]),1),'tokens in',np.median([d['tokens_in'] for d in R]),'out',np.median([d['tokens_out'] for d in R]))
print('tev seconds per label',round(JS['tev'][test].mean(),2),'14B seconds per draw',round(ss[test].mean(),2),'ratio',round(JS['tev'][test].mean()/ss[test].mean(),3),'vs compute ratio',round(JT['tev'][test].mean()/st[test].mean(),3))
exec(open('pressure.py').read().split("print('\\n== 9 weak tests")[1].split("print('unmatched'")[0].split('\n',1)[1])
print('== thin tests plus judge: run tev only on drafts that pass k tests ==')
def stack(pass_k):
    ac=pass_k&A; a=ac.astype(float)
    acc_=(a*h+(1-a)*sh[:,None]).mean(1); cost=(gt+pass_k*JT['tev']+(1-a)*st[:,None]).mean(1); return acc_,cost
for k in (1,2,3):
    pk=ff>=k; a_,c_=stack(pk)
    print(f'k={k} stack acc',f(ci((a_-sh)[test]),100),'compute',f(ci((c_-st)[test]),1,0),'| HE',f(ci((a_-sh)[test&he]),100),f(ci((c_-st)[test&he]),1,0),'FA',round((pk&A)[test][h[test]==0].mean(),3))
    a0,c0,_=rr(pk); print('   vs tests alone acc',f(ci((a_-a0)[test]),100),'compute',f(ci((c_-c0)[test]),1,0))
