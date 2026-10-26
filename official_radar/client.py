"""Bounded official-source fetches; validated content-addressed last-good cache."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PSIE_URL='https://servicos.rbmlq.gov.br/dados-abertos/SP/medidores.json'


def now():
    return datetime.now(timezone.utc).isoformat()


class SourceClient:
    def __init__(self, cache, ttl=86400, opener=urllib.request.urlopen):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.ttl=ttl;self.opener=opener

    def fetch(self,url,validate,force=False):
        host=urlparse(url).hostname or ''
        if host not in {'servicos.rbmlq.gov.br','psie.inmetro.gov.br','www.praiagrande.sp.gov.br','www2.praiagrande.sp.gov.br'} or urlparse(url).scheme!='https':
            raise ValueError('Only explicitly supported official HTTPS sources are allowed')
        manifest=self.cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        previous=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else None
        def cached(stale=False,error=None):
            raw=(self.cache/previous['blob']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=previous['sha256']:
                raise ValueError('Corrupt source cache')
            validate(raw)
            return raw,dict(previous,cached=True,stale=stale,error=error)
        if previous and not force and time.time()-previous['checked_at']<self.ttl:
            return cached()
        headers={'User-Agent':'RelasOfficialRadarPilot/1.0 (public nonprofit research)','Accept':'application/json, application/xml, text/html'}
        if previous and previous.get('etag'):
            headers['If-None-Match']=previous['etag']
        try:
            with self.opener(urllib.request.Request(url,headers=headers),timeout=45) as r:
                if (urlparse(r.url).hostname or '') not in {'servicos.rbmlq.gov.br','psie.inmetro.gov.br','www.praiagrande.sp.gov.br','www2.praiagrande.sp.gov.br'}:
                    raise ValueError('Unexpected redirect destination')
                raw=r.read(64*1024*1024+1)
                if len(raw)>64*1024*1024:
                    raise ValueError('Official dataset exceeds 64 MiB cap')
                validate(raw)
                sha=hashlib.sha256(raw).hexdigest();blob=sha+'.raw'
                meta=dict(source_url=url,retrieved_at=now(),last_successful_fetch=now(),source_updated_at=r.headers.get('Last-Modified'),etag=r.headers.get('ETag'),sha256=sha,blob=blob,checked_at=time.time(),cached=False,stale=False,error=None)
                destination=self.cache/blob
                if not destination.exists():
                    destination.write_bytes(raw)
                temp=manifest.with_suffix('.tmp');temp.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,manifest)
                return raw,meta
        except urllib.error.HTTPError as e:
            if e.code==304 and previous:
                previous['checked_at']=time.time();previous['last_successful_fetch']=now()
                temp=manifest.with_suffix('.tmp');temp.write_text(json.dumps(previous),encoding='utf-8');os.replace(temp,manifest)
                return cached()
            if previous:
                return cached(True,f'HTTP {e.code}')
            raise
        except (OSError,ValueError) as e:
            if previous:
                return cached(True,f'{type(e).__name__}: {e}')
            raise
