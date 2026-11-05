import json,ast,collections,io,contextlib,re,sys
from evalplus.data import get_human_eval_plus,get_mbpp_plus,get_human_eval_plus_hash,get_mbpp_plus_hash
from evalplus.evaluate import get_groundtruth
from evalplus.eval import untrusted_check,PASS
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
he=get_human_eval_plus(); mb=get_mbpp_plus()
gh=get_groundtruth(he,get_human_eval_plus_hash(),[]); gm=get_groundtruth(mb,get_mbpp_plus_hash(),MBPP_OUTPUT_NOT_NONE_TASKS)
R=[r for r in json.load(open('/app/unknowns_out.json')) if not r['details']]
mods=collections.Counter(); out=[]; cls=collections.Counter()
for r in R:
    s=r['solution']
    for m in re.findall(r'^\s*(?:from|import)\s+([A-Za-z_][\w]*)',s,re.M): mods[m]+=1
    try:
        T=ast.parse(s)
    except SyntaxError:
        cls['syntax']+=1; out.append(dict(task=r['task'],solution=s,kind='syntax',stripped_hidden=False)); continue
    keep=[n for n in T.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Import,ast.ImportFrom)) or (isinstance(n,ast.Assign))]
    dropped=len(T.body)-len(keep)
    T.body=keep; s2=ast.unparse(T)
    ds='humaneval' if r['task'].startswith('HumanEval') else 'mbpp'
    D=he if ds=='humaneval' else mb; G=gh if ds=='humaneval' else gm; p=D[r['task']]; g=G[r['task']]
    st,_=untrusted_check(ds,s2,p['base_input'],p['entry_point'],expected=g['base'],atol=p['atol'],ref_time=g['base_time'],fast_check=True,min_time_limit=4.0,gt_time_limit_factor=4.0)
    h=False
    if st==PASS:
        st2,_=untrusted_check(ds,s2,p['plus_input'],p['entry_point'],expected=g['plus'],atol=p['atol'],ref_time=g['plus_time'],fast_check=True,min_time_limit=4.0,gt_time_limit_factor=4.0)
        h=st2==PASS
    cls[('dropped_stmts' if dropped else 'no_stmts',st,h)]+=1
    out.append(dict(task=r['task'],solution=r['solution'],kind='ok',base=st,stripped_hidden=bool(h),dropped=dropped))
print(cls); print(mods.most_common(25))
json.dump(out,open('/app/strip_out.json','w')); print('done')
