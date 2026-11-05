import json,re
from evalplus.data import get_human_eval_plus,get_mbpp_plus,get_human_eval_plus_hash,get_mbpp_plus_hash
from evalplus.evaluate import get_groundtruth
from evalplus.eval import untrusted_check,PASS
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
he=get_human_eval_plus(); mb=get_mbpp_plus()
gh=get_groundtruth(he,get_human_eval_plus_hash(),[]); gm=get_groundtruth(mb,get_mbpp_plus_hash(),MBPP_OUTPUT_NOT_NONE_TASKS)
R=[r for r in json.load(open('/app/unknowns_out.json')) if not r['details'] and re.search(r'^\s*(from|import)\s+(sympy|scipy|pytest)',r['solution'],re.M)]
out=[]
for r in R:
    ds='humaneval' if r['task'].startswith('HumanEval') else 'mbpp'; D=he if ds=='humaneval' else mb; G=gh if ds=='humaneval' else gm; p=D[r['task']]; g=G[r['task']]
    st,_=untrusted_check(ds,r['solution'],p['base_input'],p['entry_point'],expected=g['base'],atol=p['atol'],ref_time=g['base_time'],fast_check=True,min_time_limit=4.0,gt_time_limit_factor=4.0)
    h=False
    if st==PASS:
        s2,_=untrusted_check(ds,r['solution'],p['plus_input'],p['entry_point'],expected=g['plus'],atol=p['atol'],ref_time=g['plus_time'],fast_check=True,min_time_limit=4.0,gt_time_limit_factor=4.0); h=s2==PASS
    out.append(dict(task=r['task'],solution=r['solution'],base=st,hidden=bool(h)))
json.dump(out,open('/app/mods_out.json','w'))
print(len(out),'base pass',sum(o['base']==PASS for o in out),'hidden pass',sum(o['hidden'] for o in out))
