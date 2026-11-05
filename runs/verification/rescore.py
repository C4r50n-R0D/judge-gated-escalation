"""Re-score a random sample of stored drafts with the official evaluator and compare with the stored verdicts."""
import json,random,sys,collections
sys.path.insert(0,'.')
import suites, evalplus_io as io
V='/tmp/verify/rescore'
rows=[r for r in map(json.loads,open('runs/confirmatory.labeled.jsonl')) if '_meta' not in r]
rnd=random.Random(551); samp=rnd.sample(rows,500)
ds={'humaneval+':('humaneval','he'),'mbpp+':('mbpp','mb')}
if sys.argv[1]=='export':
    for su,(d,tag) in ds.items():
        tasks={t['id']:t for t in suites.load(su)}; seen=set()
        with open(f'{V}/{tag}.jsonl','w') as f:
            for r in samp:
                if r['suite']==su:
                    f.write(json.dumps({'task_id':r['task'],'solution':io.solution_for(r,tasks[r['task']])})+'\n'); seen.add(r['task'])
            for t in tasks:
                if t not in seen: f.write(json.dumps({'task_id':t,'solution':io.PLACEHOLDER})+'\n')
else:
    agree=collections.Counter(); dis=[]
    for su,(d,tag) in ds.items():
        tasks={t['id']:t for t in suites.load(su)}
        res=json.load(open(f'{V}/{tag}_eval_results.json'))['eval']; pos=collections.Counter()
        for r in samp:
            if r['suite']!=su: continue
            k=pos[r['task']]; pos[r['task']]+=1; e=res[r['task']][k]
            assert e['solution']==io.solution_for(r,tasks[r['task']])
            v=e['base_status']=='pass'; h=v and e['plus_status']=='pass'
            agree['visible_ok' if v==r['visible_passed'] else 'visible_diff']+=1
            agree['hidden_ok' if h==r['hidden_passed'] else 'hidden_diff']+=1
            agree[('stored_pass' if r['hidden_passed'] else 'stored_fail')]+=1
            if h!=r['hidden_passed'] or v!=r['visible_passed']: dis.append((r['task'],r['tier'],r['rep'],r['visible_passed'],r['hidden_passed'],v,h,e['base_status'],e['plus_status']))
    print(dict(agree)); print(dis)
