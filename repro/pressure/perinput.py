"""Inside the network-less evalplus container: for drafts that failed with no recorded test, find the first failing base test."""
import json,sys,inspect
from evalplus.data import get_human_eval_plus, get_mbpp_plus, get_human_eval_plus_hash, get_mbpp_plus_hash
from evalplus.evaluate import get_groundtruth
from evalplus.eval import untrusted_check, PASS
from evalplus.gen.util import trusted_exec
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
print(inspect.signature(untrusted_check)); print(inspect.signature(get_groundtruth))
U=json.load(open('/app/unknowns.json'))
he=get_human_eval_plus(); mb=get_mbpp_plus()
gh=get_groundtruth(he,get_human_eval_plus_hash(),[]); gm=get_groundtruth(mb,get_mbpp_plus_hash(),MBPP_OUTPUT_NOT_NONE_TASKS)
res=[]
for i,u in enumerate(U):
    ds=he if u['ds']=='humaneval' else mb; gt=gh if u['ds']=='humaneval' else gm
    p=ds[u['task']]; g=gt[u['task']]
    st,det=untrusted_check(u['ds'],u['solution'],p['base_input'],p['entry_point'],expected=g['base'],atol=p['atol'],ref_time=g['base_time'],fast_check=False,min_time_limit=4.0,gt_time_limit_factor=4.0)
    det=[bool(x) for x in (det if det is not None else [])]
    res.append(dict(task=u['task'],solution=u['solution'],status=st,details=det,n=len(p['base_input'])))
    if i%25==0: print(i,st,det[:6],flush=True)
json.dump(res,open('/app/unknowns_out.json','w'))
print('done',len(res))
