"""Historical evidence evaluation, without legal inferences from missing data."""
from .normalize import fold, iso, text
from .resolver import resolve


def status_at(instrument, listing, association, query_date, evidence=()):
    at=iso(query_date)
    if not at:
        raise ValueError('Use a valid ISO or Brazilian calendar date')
    history=instrument.get('verifications',[]) if instrument else []
    applicable=[v for v in history if v.get('verification_date') and v['verification_date']<=at]
    latest_date=max((v['verification_date'] for v in applicable),default=None)
    latest=[v for v in applicable if v['verification_date']==latest_date]
    results={fold(v.get('result')) for v in latest}
    contradiction=len(results)>1
    approved=True if results=={'APROVADO'} else False if results=={'REPROVADO'} else None
    valid=None
    # A subsequent rejection supersedes an earlier still-dated approval.
    if approved is True and all(v.get('valid_until') for v in latest):
        valid=all(v['verification_date']<=at<=v['valid_until'] for v in latest)
    elif approved is False:
        valid=False
    official=None
    observed_until=(listing or {}).get('effective_until') or ((listing or {}).get('retrieved_at') or '')[:10] or None
    if listing and listing.get('effective_from') and listing['effective_from']<=at and (not observed_until or at<=observed_until):
        official=True
    relevant_ids={(instrument or {}).get('equipment_id'),(listing or {}).get('equipment_id')}-{None}
    scoped=[e for e in evidence if e.get('equipment_id') in relevant_ids]
    active_notices=[e for e in scoped if e.get('claim')=='ACTIVATION_NOTICE' and e.get('confidence') in {'EXACT','HIGH'} and e.get('effective_from') and e['effective_from']<=at and (not e.get('effective_until') or at<=e['effective_until'])]
    deactivations=[e for e in scoped if e.get('claim')=='DEACTIVATION_NOTICE' and e.get('confidence') in {'EXACT','HIGH'} and e.get('effective_from') and e['effective_from']<=at]
    if active_notices:
        official=True
    resolved=association in {'EXACT','HIGH'}
    conflict=association=='CONFLICT' or contradiction
    result='OFFICIAL_CONFLICT' if conflict else 'DEACTIVATED' if deactivations else 'OFFICIAL_VERIFIED' if official and resolved and valid is True else 'HISTORICALLY_ACTIVE' if active_notices and at<(listing or {}).get('effective_from',at) else 'OFFICIAL_METROLOGY_PENDING' if official else 'DISCOVERED_UNVERIFIED'
    # validity of the municipal point requires both identity and temporal listing evidence.
    point_valid=(False if deactivations else valid) if resolved and official and not conflict else None
    return dict(equipment_id=instrument.get('equipment_id') if instrument else None,query_date=at,status=result,
                official_listing=official,metrology_required=listing.get('metrology_required',True) if listing else True,
                metrology_record_found=bool(history),approved=approved,instrument_valid_at_date=valid,
                valid_at_date=point_valid,verification_date=latest_date,
                valid_until=min((v['valid_until'] for v in latest if v.get('valid_until')),default=None),
                match_confidence=association,evidence=list(evidence)+latest,
                interpretation='UNKNOWN' if point_valid is None else 'VALID' if point_valid else 'NOT_COVERED_BY_AVAILABLE_RECORD',
                warnings=['Current listing does not prove historical activation; no legal conclusion follows from absent data.'])


def getEquipmentStatusAt(equipmentId,date,repository):
    instrument=repository.instrument(equipmentId)
    if instrument is None:
        return status_at(None,None,'UNMATCHED',date)
    return status_at(instrument,None,'UNMATCHED',date,repository.evidence(equipmentId))


def findEnforcementAt(query,municipal_records,instruments):
    at=iso(query.get('date'))
    if not at or not query.get('municipality') or not (query.get('street') or query.get('serial_number') or query.get('inmetro_number')):
        raise ValueError('municipality, date and street or serial/Inmetro ID are required')
    results=[]
    for listing in municipal_records:
        if fold(listing['municipality'])!=fold(query['municipality']):
            continue
        # Query identity/address must agree with the actual municipal listing too.
        from .normalize import street_address,direction
        qa=street_address(query.get('street'));la=street_address(listing['address_raw'])
        if query.get('street') and (qa['street']!=la['street'] or (qa['number'] is not None and qa['number']!=la['number'])):
            continue
        if query.get('direction') and direction(query['direction'])!=direction(listing['direction_raw']):
            continue
        if query.get('speed_limit') and float(query['speed_limit'])!=listing['speed_limit']:
            continue
        instruments_for_query=instruments
        if query.get('serial_number') or query.get('inmetro_number'):
            instruments_for_query=[r for r in instruments if any((not query.get('serial_number') or text(l['serial_number'])==text(query['serial_number'])) and (not query.get('inmetro_number') or text(l['inmetro_number'])==text(query['inmetro_number'])) for l in r['lanes'])]
        match=resolve(listing,instruments_for_query,at)
        for c in match['candidates']:
            confidence=match['match_confidence'] if match['selected'] is not None and c['equipment_id']==match['selected']['equipment_id'] else c['match_confidence']
            status=status_at(c['instrument'],listing,confidence,at)
            results.append(dict(municipal_equipment_id=listing['equipment_id'],equipment_id=c['equipment_id'],match_score=c['match_score'],official=status['official_listing'],valid_at_date=status['valid_at_date'],status=status['status'],match_confidence=confidence,why=c['why'],conflicts=c['conflicts'],metrology=status))
    return dict(query_date=at,candidates=sorted(results,key=lambda r:r['match_score'],reverse=True),warnings=['Candidates are evidence matches, not a decision on a traffic fine.'])


class OfficialRadarFinder:
    """Injected snapshots: no network, global state, HTTP handler or app DB access."""
    def __init__(self,municipal_records,instruments,evidence=()):
        self.municipal_records=municipal_records
        self.instruments=instruments
        self.evidence=evidence

    def getEquipmentStatusAt(self,equipmentId,date):
        listing=next((r for r in self.municipal_records if r['equipment_id']==equipmentId),None)
        if listing:
            match=resolve(listing,self.instruments,iso(date))
            candidate=match['selected']
            return status_at(candidate['instrument'] if candidate else None,listing,match['match_confidence'],date,self.evidence)
        instrument=next((r for r in self.instruments if r['equipment_id']==equipmentId),None)
        return status_at(instrument,None,'UNMATCHED',date,self.evidence)

    def findEnforcementAt(self,query):
        return findEnforcementAt(query,self.municipal_records,self.instruments)
