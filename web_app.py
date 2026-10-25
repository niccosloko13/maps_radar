"""ASGI transport around the existing, tested Relas API handlers.

No socket, server thread, HTTPServer or filesystem request emulation is used.
Only API dispatch is shared; static responses are handled by Starlette.
"""
import io
import json
from email.message import Message
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from runtime_config import hosted
import runtime_jobs
import db

JOB_PATHS = {
    '/api/admin/sync/der':'der', '/api/admin/sync/municipalities':'municipalities',
    '/api/admin/sync/antt':'antt', '/api/admin/sync/santo-andre':'santo-andre',
    '/api/admin/sync/santos':'santos', '/api/admin/sync/praia-grande':'praia-grande',
    '/api/admin/sync/osm-city':'osm-city', '/api/admin/batch-scan':'city-batch',
    '/api/admin/update-city':'city', '/api/admin/assistant-pack/run':'assistant',
    '/api/admin/apply-updates':'apply-updates', '/api/admin/community/import':'community-import',
    '/api/admin/georef/der':'georef',
    '/api/sync/der/start':'der','/api/georef/der/start':'georef',
    '/api/sync/santo-andre':'santo-andre','/api/sync/santos':'santos','/api/sync/praia-grande':'praia-grande',
}


def create_app(server):
    app = FastAPI(title='Relas', version='2.2.0', docs_url=None, redoc_url=None, openapi_url=None)

    class ApiTransport(server.H):
        def __init__(self, request, body):
            self.path = request.url.path+('?' + request.url.query if request.url.query else '')
            self.headers = Message()
            for key,value in request.headers.items(): self.headers[key] = value
            self.headers.replace_header('content-length',str(len(body))) if 'content-length' in self.headers else self.headers.__setitem__('content-length',str(len(body)))
            self.client_address = (request.client.host if request.client else 'unknown',0)
            self.rfile = io.BytesIO(body); self.response = None
        def js(self, obj, status=200, extra_headers=None):
            self.response = JSONResponse(obj, status_code=status, headers={'Cache-Control':'no-store', **(extra_headers or {})})
            return obj

    @app.api_route('/api/{path:path}', methods=['GET','POST'])
    async def api(request: Request, path: str):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>2097152: return JSONResponse({'error':'request too large'},413)
        handler = ApiTransport(request, bytes(body))
        def dispatch():
            with db.request_scope():
                return handler.do_POST() if request.method=='POST' else handler.do_GET()
        if hosted() and request.method=='GET' and request.url.path in server.LEGACY_MUTATIONS:
            return JSONResponse({'error':'Use the authenticated Admin POST operation'},405)
        # Cookies are same-site; reject cross-origin mutation requests as well.
        origin = request.headers.get('origin')
        if request.method=='POST' and origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            return JSONResponse({'error':'Cross-origin writes are not allowed'},403)
        if request.url.path in JOB_PATHS and hosted():
            if not server._admin_authed_v15(handler): return JSONResponse({'error':'Admin authentication required'},401)
            try: data=json.loads(body or b'{}')
            except ValueError: return JSONResponse({'error':'Invalid JSON'},400)
            if len(data.get('municipalities', []))>1 or len(data.get('decisions', []))>1:
                return JSONResponse({'error':'Hosted jobs accept one city/update per request'},400)
            def work():
                result = dispatch()
                if handler.response is None: raise ValueError('Unknown operation')
                if handler.response.status_code>=400: raise ValueError('Operation rejected')
                return result
            result = await run_in_threadpool(runtime_jobs.run,server,JOB_PATHS[request.url.path],work)
            # Keep established Admin response fields at the top level.
            payload=dict(result.get('result') or {}) if isinstance(result.get('result'),dict) else {}
            payload.update({k:v for k,v in result.items() if k!='result'})
            return JSONResponse(payload,status_code=200 if result['ok'] else 409,headers={'Cache-Control':'no-store'})
        try:
            await run_in_threadpool(dispatch)
            return handler.response or JSONResponse({'error':'Endpoint not found'},404)
        except Exception:
            # No raw database exceptions or connection strings in responses.
            return JSONResponse({'error':'Request failed; check application/database configuration'},503,headers={'Cache-Control':'no-store'})

    @app.middleware('http')
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        if request.url.path.startswith(('/api/','/admin')) or request.url.path in ('/','/index.html','/sw.js','/boot.js'):
            response.headers['Cache-Control']='no-store, max-age=0'
        return response

    @app.get('/admin')
    def admin(): return FileResponse(server.APP_DIR/'admin.html')
    @app.get('/favicon.ico')
    def favicon(): return FileResponse(server.APP_DIR/'icon.svg')

    app.mount('/',StaticFiles(directory=str(server.APP_DIR),html=True),name='frontend')
    return app
