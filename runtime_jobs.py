"""Request-bound jobs with durable status and cooperative time budgets.

No background thread is started in hosted mode. Expired leases are visible as
interrupted; retries are explicit Admin requests, never automatic duplicate work.
"""
import contextvars
import json
import time
import uuid
from datetime import datetime, timezone

deadline = contextvars.ContextVar('job_deadline', default=None)


def check():
    limit = deadline.get()
    if limit and time.time() >= limit: raise TimeoutError('Job budget exhausted; retry a smaller operation')


def run(server, kind, callback):
    job_id = uuid.uuid4().hex; stamp = datetime.now(timezone.utc).isoformat(); until = time.time()+45
    with server.db() as c:
        c.execute("UPDATE runtime_jobs SET status='interrupted',finished_at=?,error='Request lease expired; retry explicitly' WHERE status='running' AND deadline_at < ?", (stamp, time.time()))
        # Serialise claims in the database, not with a per-process Python lock.
        c.execute("SELECT pg_advisory_xact_lock(hashtext(?))", ('relas-job:'+kind,))
        active = c.execute("SELECT id FROM runtime_jobs WHERE kind=? AND status='running'", (kind,)).fetchone()
        if active: return {'ok':False, 'job_id':active[0], 'status':'running', 'error':'Operation already running'}
        c.execute('INSERT INTO runtime_jobs(id,kind,status,started_at,deadline_at) VALUES(?,?,?,?,?)', (job_id,kind,'running',stamp,until))
    token = deadline.set(until)
    try:
        result = callback(); check()
        if isinstance(result,dict) and (result.get('ok') is False or result.get('status') in ('error','failed','partial')):
            raise ValueError('Operation did not finish successfully; inspect persistent operation logs')
        with server.db() as c:
            c.execute('UPDATE runtime_jobs SET status=?,finished_at=?,result_json=? WHERE id=?', ('completed',datetime.now(timezone.utc).isoformat(),json.dumps(result,ensure_ascii=False,default=str),job_id))
        return {'ok':True, 'job_id':job_id, 'status':'completed', 'result':result}
    except Exception as error:
        deadline.set(None)  # Persist the failure even after the work budget expired.
        # Never persist driver exceptions that can include host/credentials.
        message = str(error) if isinstance(error, (TimeoutError, ValueError)) else type(error).__name__
        with server.db() as c:
            c.execute('UPDATE runtime_jobs SET status=?,finished_at=?,error=? WHERE id=?', ('failed',datetime.now(timezone.utc).isoformat(),message,job_id))
        return {'ok':False,'job_id':job_id,'status':'failed','error':message}
    finally: deadline.reset(token)


def state(server, kind):
    with server.db() as c:
        rows = [dict(r) for r in c.execute('SELECT * FROM runtime_jobs WHERE kind=? ORDER BY started_at DESC LIMIT 1', (kind,))]
    if not rows: return {'running':False, 'status':'idle'}
    item = rows[0]
    if item['status']=='running' and item['deadline_at'] < time.time(): item['status']='interrupted'
    item['running'] = item['status']=='running'
    return item
