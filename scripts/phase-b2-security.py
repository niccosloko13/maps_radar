"""Read-only credential audit. No credential values are logged or serialized."""
import os,sys,json,re,subprocess,base64,time
from urllib.parse import urlsplit,unquote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts/navigation-intelligence-v3-phase-b2';A.mkdir(exist_ok=True)
p=ROOT/'artifacts/vercel-neon/backups/project-relink/env-before-relink.txt'
values={}
for line in p.read_text(encoding='utf-8-sig').splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);v=v.strip().strip('"').strip("'")
  if re.fullmatch('[A-Z][A-Z0-9_]*',k.strip()) and v:values[k.strip()]=v
secret_values=[v.encode() for k,v in values.items() if len(v)>12]
secret_values+=list({unquote(urlsplit(v).password).encode() for v in values.values() if v.startswith(('postgres://','postgresql://')) and urlsplit(v).password})
history=[];objects=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).splitlines()
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
blobs=0
for obj in objects:
 oid=obj.split(b' ',1)[0];proc.stdin.write(oid+b'\n');proc.stdin.flush();header=proc.stdout.readline().split()
 if len(header)<3:continue
 size=int(header[2]);is_blob=header[1]==b'blob';remaining=size;tail=b'';hit=False
 while remaining:
  chunk=proc.stdout.read(min(1024*1024,remaining));remaining-=len(chunk);data=tail+chunk
  if is_blob and any(v in data for v in secret_values):hit=True
  tail=data[-max([len(v) for v in secret_values] or [1]):]
 proc.stdout.read(1)
 if is_blob:blobs+=1
 if hit:history.append(oid.decode())
proc.stdin.close();proc.wait()
public_hits=[];ignored_hits=[];scanned=0
for base in ['app','artifacts']:
 for f in (ROOT/base).rglob('*'):
  if not f.is_file() or f.suffix not in ('.js','.html','.css','.txt','.log','.md','.json') or f.stat().st_size>15_000_000:continue
  data=f.read_bytes();scanned+=1
  if any(v in data for v in secret_values):
   n=f.relative_to(ROOT).as_posix();ignored=subprocess.run(['git','check-ignore','-q',n],cwd=ROOT).returncode==0
   (ignored_hits if ignored else public_hits).append(n)
validity={};tested={}
for k,v in values.items():
 if v.startswith(('postgres://','postgresql://')):
  if v in tested:validity[k]=tested[v];continue
  try:
   import psycopg
   with psycopg.connect(v,connect_timeout=8,options='-c default_transaction_read_only=on') as c:
    c.execute('SELECT 1').fetchone()
   state='VALID_READ_ONLY_SELECT_PASSED'
  except Exception as e:state='NOT_VALIDATED_'+type(e).__name__
  validity[k]=tested[v]=state
 elif k.endswith('OIDC_TOKEN'):
  try:
   payload=v.split('.')[1];claim=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
   validity[k]='EXPIRED_JWT_CLAIM_NOT_SIGNATURE_VALIDATED' if float(claim.get('exp',0))<time.time() else 'UNEXPIRED_JWT_NOT_SERVER_VALIDATED'
  except Exception:validity[k]='NOT_VALIDATED'
elsewhere=subprocess.run(['git','ls-files','--error-unmatch',str(p.relative_to(ROOT))],cwd=ROOT,capture_output=True).returncode==0
rotation=bool(history or public_hits or any(v=='VALID_READ_ONLY_SELECT_PASSED' for v in validity.values()) or values)
result={'CREDENTIAL_ROTATION_REQUIRED':'YES' if rotation else 'NO','backup_tracked':elsewhere,'backup_ignored':subprocess.run(['git','check-ignore','-q',str(p.relative_to(ROOT))],cwd=ROOT).returncode==0,'history_blobs_examined':blobs,'history_matching_blob_ids':history,'history_scope':'all locally reachable Git refs; cannot prove absence from deleted remote history','scanned_files':scanned,'public_matching_paths':public_hits,'private_ignored_matching_paths':ignored_hits,'validity_by_variable_name':validity,'external_credentials_changed':False}
(A/'security-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
keys={k:'CONFIGURED' if os.environ.get(k) else 'NOT_CONFIGURED' for k in ['ARTESP_OCCURRENCES_API_KEY','ARTESP_INTERVENTIONS_API_KEY']}
# Follow the existing local dotenv loader without emitting values.
try:
 from dotenv import dotenv_values
 for f in ['.env','.env.local']:
  for k,v in dotenv_values(ROOT/f).items():
   if k in keys and v:keys[k]='CONFIGURED'
except ImportError:pass
(A/'ARTESP_ENVIRONMENT.json').write_text(json.dumps(keys,indent=2),encoding='utf-8')
print(json.dumps({'rotation':result['CREDENTIAL_ROTATION_REQUIRED'],'history_hits':len(history),'public_hits':len(public_hits),'backup_ignored':result['backup_ignored'],'validity':validity,'ARTESP':keys}))
