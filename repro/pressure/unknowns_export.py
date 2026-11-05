import json,ast
out=[]
for fn in ('s2_he','s2_mb'):
    for t,L in json.load(open(f'{fn}_eval_results.json'))['eval'].items():
        seen=set()
        for e in L:
            if e['solution'].startswith('def __placeholder__'): continue
            ft=e['base_fail_tests']; ft=ast.literal_eval(ft) if isinstance(ft,str) else ft
            if e['base_status']!='pass' and not ft and e['solution'] not in seen:
                seen.add(e['solution']); out.append(dict(task=t,ds='humaneval' if fn=='s2_he' else 'mbpp',solution=e['solution']))
json.dump(out,open('unknowns.json','w')); print(len(out))
