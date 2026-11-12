"""Compare les moteurs Python et navigateur sur 36 situations métier."""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from python.pricing import calculate,Period
cases=[]
for method in ['prior','bayes','credibility']:
    for t,n,amount in [(0,0,0),(1,0,0),(.5,1,1000),(1,2,6000)]:
        for coverage in [.25,.5,1]:
            cases.append(dict(frequency=.08,severity=2500,beta=4,k=3,method=method,coverage=coverage,fixedFee=10,expenseRate=.12,marginRate=.08,history=[] if not t else [dict(exposure=t,claims=n,amount=amount)]))
root=Path(__file__).resolve().parents[1]
script="import {calculate} from './dist/engine.mjs'; let s=''; for await(const chunk of process.stdin)s+=chunk; console.log(JSON.stringify(JSON.parse(s).map(calculate)));"
js=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],input=json.dumps(cases).encode(),cwd=root))
for case,result in zip(cases,js):
    py=calculate(case['frequency'],case['severity'],[Period(**r) for r in case['history']],beta=case['beta'],k=case['k'],method=case['method'],coverage=case['coverage'],fixed_fee=case['fixedFee'],expense_rate=case['expenseRate'],margin_rate=case['marginRate'])
    for p,j in [('premium','premium'),('annual_pure','annualPure'),('bayes','bayes'),('credibility','credibility'),('z_bayes','zBayes')]:
        assert abs(py[p]-result[j])<1e-8,(case,p,py[p],result[j])
print('Parité Python / JavaScript : 36 situations validées.')
