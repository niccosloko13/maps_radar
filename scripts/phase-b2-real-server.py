"""Real-data validation server, isolated SQLite. Legacy map reads are public/read-only."""
import os,sys,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0')
import server
private=root/'artifacts/navigation-intelligence-v3-phase-b2/private'
server.DATA_DIR=private;server.DB_PATH=private/'validation.sqlite';server.init_db();server.ensure_v18_tables();server.community.init(server)
os.environ.pop('ADMIN_PASSWORD_HASH',None);os.environ['ADMIN_USERNAME']='admin';os.environ['RELAS_ADMIN_PASSWORD']='B2-LOCAL-REVIEW';os.environ['SESSION_SECRET']='b2-local-review-only-not-production-secret';server.AUTH=server.AdminAuth(private);server.ADMIN_USER='admin'
class H(server.H):
    def log_message(self,*a):pass
    def do_GET(self):
        if self.path.startswith(('/api/map/features','/api/radars','/api/road-objects')):
            try:
                with urllib.request.urlopen('https://mapsradar-three.vercel.app'+self.path,timeout=25) as r:body=r.read();status=r.status
            except urllib.error.HTTPError as e:body=e.read();status=e.code
            except Exception:body=b'{"error":"Read-only legacy proxy unavailable"}';status=502
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        return super().do_GET()
    def do_POST(self):
        if self.path.startswith('/api/admin/road-sources/') and self.path.endswith(('/sync','/test','/catalogs')):return self.js({'error':'Use isolated collector, not browser-driven upstream requests'},409)
        return super().do_POST()
server.ThreadingHTTPServer(('127.0.0.1',8820),H).serve_forever()
