"""Phase B.1: evidence-based, source-specific readiness (no GPS/matcher changes)."""
import math
from datetime import datetime, timezone

APPROVED_QUALITIES={'OFFICIAL_COORDINATE','OFFICIAL_ROAD_KM','GEOCODED_HIGH'}
SOURCE_STATUSES={'HEALTHY','DEGRADED','STALE','AUTH_REQUIRED','BLOCKED_LICENSE',
                 'BLOCKED_ENDPOINT','BLOCKED_COORDINATES','DISABLED'}


def seconds(value):
    try:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return dt.replace(tzinfo=dt.tzinfo or timezone.utc).timestamp()
    except (ValueError,TypeError):return None


def station_freshness(raw, now, ingested_at, poll_interval=600, observed=True):
    """measurement_gap is the feed's nominal sampling interval in minutes.

    FRESH <=2 samples, AGING <=4; stale beyond that. This doesn't infer that
    an instrument died merely because OUR collector stopped. A daily station
    cannot establish current road rainfall, even if a daily sample just arrived.
    """
    reading=seconds(raw.get('max_date'));ingested=seconds(ingested_at)
    try:cadence=float(raw.get('measurement_gap'))*60
    except (ValueError,TypeError):cadence=None
    if cadence is None or not math.isfinite(cadence) or not 60<=cadence<=86400:
        return dict(state='UNKNOWN',reason='UNKNOWN_CADENCE',current=False,reading_age_seconds=None,cadence_seconds=None)
    age=now-reading if reading is not None else None
    if age is None or age < -300:
        return dict(state='UNKNOWN',reason='MISSING_OR_FUTURE_READING',current=False,reading_age_seconds=age,cadence_seconds=cadence)
    collection_age=now-ingested if ingested is not None else None
    if collection_age is None or collection_age>2*poll_interval:
        state='STALE';reason='COLLECTOR_CACHE_STALE'
    elif age>max(86400,12*cadence) and observed:
        state='DEAD_STATION';reason='PROVIDER_RETURNED_OLD_READING_IN_FRESH_COLLECTION'
    elif not observed:state='STALE';reason='NOT_OBSERVED_IN_LATEST_COLLECTION'
    elif age<=2*cadence:state='FRESH';reason='WITHIN_TWO_NOMINAL_SAMPLES'
    elif age<=4*cadence:state='AGING';reason='WITHIN_FOUR_NOMINAL_SAMPLES'
    else:state='STALE';reason='STATION_READING_OLD'
    return dict(state=state,reason=reason,current=state in ('FRESH','AGING') and cadence<=3600 and age<=3600,
                reading_age_seconds=max(0,age),collection_age_seconds=collection_age,
                cadence_seconds=cadence,expires_at_seconds=reading+4*cadence,
                freshness_kind='OBSERVATION_FRESHNESS')


def source_readiness(source, review, now, credential_configured, approved=0, blocked=0):
    review=review or {};last=seconds(source.get('last_success_at'))
    age=now-last if last is not None else None
    interval=source['poll_interval_seconds']
    collection='UNKNOWN' if age is None else 'FRESH' if age<=2*interval else 'AGING' if age<=4*interval else 'STALE'
    kind='INFRASTRUCTURE_FRESHNESS' if source['category']=='infrastructure' else 'EVENT_FRESHNESS' if source['category']=='events' else 'OBSERVATION_FRESHNESS'
    blockers=[]
    if source['auth_type']=='api-key' and not credential_configured:blockers.append('MISSING_API_KEY')
    if source.get('last_error')=='HTTP_401':blockers.append('AUTH_REJECTED')
    if source.get('last_error')=='HTTP_403':blockers.append('ACCESS_DENIED')
    if not review.get('license_verified'):blockers.append('LICENSE_NOT_VERIFIED')
    if not review.get('endpoint_verified'):blockers.append('ENDPOINT_NOT_VALIDATED')
    if source['source_id']=='prf-sp' and approved==0:blockers.append('NO_APPROVED_COORDINATES')
    if source.get('last_error'):blockers.append('LAST_FETCH_ERROR')
    if age is None:blockers.append('NO_VALID_SNAPSHOT')
    elif collection=='STALE':blockers.append('COLLECTOR_CACHE_STALE')
    if not source['enabled']:status='DISABLED'
    elif 'MISSING_API_KEY' in blockers or 'AUTH_REJECTED' in blockers:status='AUTH_REQUIRED'
    elif 'LICENSE_NOT_VERIFIED' in blockers:status='BLOCKED_LICENSE'
    elif 'ENDPOINT_NOT_VALIDATED' in blockers or 'ACCESS_DENIED' in blockers:status='BLOCKED_ENDPOINT'
    elif 'NO_APPROVED_COORDINATES' in blockers:status='BLOCKED_COORDINATES'
    elif source.get('last_error') or collection=='STALE':status='STALE' if last is not None else 'DEGRADED'
    elif last is None:status='DEGRADED'
    elif blocked:status='DEGRADED'
    else:status='HEALTHY'
    return dict(status=status,freshness_status='STALE' if source.get('last_error') and last else collection,
                freshness_kind=kind,collection_age_seconds=age,
                source_snapshot_age_seconds=(now-seconds(source.get('last_source_timestamp'))) if seconds(source.get('last_source_timestamp')) is not None else None,
                blocker='; '.join(blockers) or ('PARTIAL_COORDINATE_REVIEW' if blocked else None),blockers=blockers,
                next_action=review.get('next_action') or ('Resolve flagged coordinate records' if blocked else 'Continue scheduled collection within source limits'),
                coordinate_approved=approved,coordinate_blocked=blocked,
                license=review.get('license') or source.get('license'),terms_url=review.get('terms_url') or source.get('terms_url'),
                commercial_restrictions=review.get('commercial_restrictions') or 'NOT VERIFIED',
                attribution_required=bool(review.get('attribution_required')) if review.get('license_verified') else None,last_terms_check=review.get('last_terms_check'),
                license_verified=bool(review.get('license_verified')),endpoint_verified=bool(review.get('endpoint_verified')))
