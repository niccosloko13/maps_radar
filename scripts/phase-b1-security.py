"""Bounded local secret scan: emits names/counts, never values."""
import os,re,json,subprocess,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts/navigation-intelligence-v3-phase-b1'
secrets=set()
for k,v in os.environ.items():
 if re.search('KEY|TOKEN|SECRET|PASSWORD|DATABASE_URL',k) and len(v)>=12:secrets.add(v)
for p in ROOT.glob('.env*'):
 if p.name=='.env.example':continue
 for line in p.read_text(encoding='utf-8-sig').splitlines():
  if '=' not in line or line.lstrip().startswith('#'):continue
  k,v=line.split('=',1);v=v.strip().strip('\"').strip("'")
  if len(v)>=12 and re.search('KEY|TOKEN|SECRET|PASSWORD|DATABASE_URL',k):secrets.add(v)
temp=A/'private/neon-url.txt'
if temp.exists():secrets.add(temp.read_text(encoding='utf-8-sig').strip())
paths=[]
for base in ['app','artifacts']:
 for p in (ROOT/base).rglob('*'):
  if p.is_file() and 'private' not in p.parts and p.suffix.lower() in ('.js','.html','.css','.json','.md','.txt','.log') and p.stat().st_size<15_000_000:paths.append(p)
matches=[];private_matches=[]
for p in paths:
 text=p.read_text(encoding='utf-8',errors='replace')
 if any(s and s in text for s in secrets) or re.search(r'postgres(?:ql)?://[^\s:@]+:(?!PASSWORD)[^\s@]+@',text,re.I):
  n=p.relative_to(ROOT).as_posix()
  if subprocess.run(['git','check-ignore','-q',n],cwd=ROOT).returncode==0:private_matches.append(n)
  else:matches.append(n)
ignored={}
for n in ['.env','.env.local','artifacts/navigation-intelligence-v3-phase-b1/private/neon-url.txt']:
 ignored[n]=subprocess.run(['git','check-ignore','-q',n],cwd=ROOT).returncode==0
with sqlite3.connect(A/'private/validation.sqlite') as c:fixtures=c.execute("SELECT count(*) FROM road_event WHERE event_id LIKE '%TEST%' OR payload_json LIKE '%\"TEST\"%'").fetchone()[0]
result={'scanned_text_files':len(paths),'publishable_real_secret_matches':sorted(set(matches)),'existing_gitignored_private_backup_matches':private_matches,'gitignored':ignored,'real_db_fixture_rows':fixtures,'screenshots_review':'Map point details and Admin diagnostics inspected; no credential fields displayed','limits':'Exact known environment/.env values and credential URI pattern; not a forensic audit of all history or binary files'}
(A/'security-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert not matches, 'Potential secret in examined file: review paths without logging values'
assert all(ignored.values()) and fixtures==0
(A/'SECURITY_REVIEW.md').write_text(f'''# Security review - B.1
PASS for publishable files within examined scope. Scanned {len(paths)} frontend/artifact text files; publishable real-secret matches0. One pre-existing ignored private environment backup matched a real secret: artifacts/vercel-neon/backups/project-relink/env-before-relink.txt. It remains private/Git-ignored and was not copied, printed or deleted. Thus this is NOT a claim that every local artifact contains no secret. Compared actual secret-bearing environment/.env values without printing them, plus credential-URI checks. Secret values never included in this report or endpoint logs. ARTESP keys absent; no protected upstream requests issued. Existing .env files/configuration preserved; .env.example has placeholders only.

.env/.env.local and B.1/private are Git-ignored. Temporary Neon URL removed after isolated compatibility test. Branch explicitly guarded by endpoint, production unchanged. No push/deploy. Test-server session password/secret are marked local-only and not real credentials; no production auth changes.

Real validation database TEST rows0. Fixtures confined to unit tests/explicit TEST server and isolated Neon compatibility check; they are not source readiness evidence. TEST server requires RELAS_ENABLE_TEST_FIXTURES=1 and blocks upstream sync. PostgreSQL controlled test rows cleaned up. Prior fixture UI screenshots are not B.1 map proof.

Map screenshots/detail and Admin diagnostics inspected, no API credential fields displayed. Stored HTTP response metadata uses a rate-limit/terms allowlist; Authorization is not serialized. No absolute assertion about all historic/unexamined binary files. Machine evidence security-results.json.
''',encoding='utf-8')
print('Security:',len(paths),'files; publishable secret matches0; existing ignored private backup matches',len(private_matches),'; real database fixture rows0')
