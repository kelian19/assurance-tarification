"""Récupération de la source originale CASdatasets, version Git figée."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
def download():
 RAW.mkdir(parents=True,exist_ok=True)
 manifest=RAW/'manifest.json'
 if manifest.exists():
  m=json.loads(manifest.read_text())
  for entry in m['files']:
   p=RAW/entry['name']
   if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Empreinte de données invalide : '+str(p))
  return m
 sha='227fb56b8734bdb7c0327a41180e01d2ddaeaf26'
 m={'repository':'https://github.com/dutangc/CASdatasets','commit':sha,'files':[]}
 for name in ['freMTPL2freq.rda','freMTPL2sev.rda']:
  url=f'https://raw.githubusercontent.com/dutangc/CASdatasets/{sha}/data/{name}'
  payload=urllib.request.urlopen(url,timeout=90).read();(RAW/name).write_bytes(payload)
  m['files'].append({'name':name,'url':url,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
 manifest.write_text(json.dumps(m,indent=2))
 return m
if __name__=='__main__':print(json.dumps(download(),indent=2))
