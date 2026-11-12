"""Prédiction du GLM exporté et paramètres de personnalisation calibrés."""
import json,math
from pathlib import Path
DEFAULT_MODEL=Path(__file__).resolve().parents[1]/'artifacts/model.json'
def load_model(path=DEFAULT_MODEL):return json.loads(Path(path).read_text())
def feature_values(profile,model):
 values={}
 for name,edges in model['bins'].items():
  value=profile.get(name)
  if not isinstance(value,(int,float)) or not math.isfinite(value) or int(value)!=value or value<edges[0] or value>=edges[-1]:raise ValueError(f'{name} hors domaine : {edges[0]}–{edges[-1]-1}')
  values[name+'Band']=next(f'{a}-{b-1}' for a,b in zip(edges[:-1],edges[1:]) if a<=value<b)
 for name in ['VehGas','Area','Region']:
  value=profile.get(name)
  if value not in model['frequency']['coefficients'][name]:raise ValueError(f'{name} inconnu')
  values[name]=value
 return values
def predict(profile,model=None,cost_index=1.):
 model=model or load_model()
 if not isinstance(cost_index,(int,float)) or not math.isfinite(cost_index) or not 0.1<=cost_index<=10:raise ValueError('Indice de coût hors domaine : 0,1–10')
 values=feature_values(profile,model)
 def glm(which):
  m=model[which]
  return math.exp(m['intercept']+sum(m['coefficients'][key][value] for key,value in values.items()))
 frequency=glm('frequency');severity=(glm('severity')+model['severity_tail'])*cost_index
 beta=model['frailty_shape_r']/frequency
 k=beta*model['severity_second_moment_factor']
 return dict(frequency=frequency,severity=severity,beta=beta,k=k,prior=frequency*severity,version=model['version'],cost_index=cost_index)
