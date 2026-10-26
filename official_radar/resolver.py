"""Explainable candidates, not an automatic approval mechanism."""
from .municipal import ALIASES
from .normalize import direction, fold, positive_speed, street_address, text


def compare(listing, instrument, at_date=None):
    if fold(listing.get('municipality'))!=fold(instrument.get('municipality')) or instrument.get('uf')!='SP':
        return None
    a=street_address(listing.get('address_raw'));b=street_address(instrument.get('location'))
    ids={text(x.get('inmetro_number')) for x in instrument['lanes'] if x.get('inmetro_number')}
    serials={text(x.get('serial_number')) for x in instrument['lanes'] if x.get('serial_number')}
    exact_id=bool((listing.get('inmetro_number') and text(listing['inmetro_number']) in ids) or (listing.get('serial_number') and text(listing['serial_number']) in serials))
    same_street=a['street']==b['street'] and bool(a['street'])
    if not same_street and not exact_id:
        return None
    score=.10;why=['same municipality'];conflicts=[];missing=[]
    if same_street:
        score+=.30;why.append('same normalized official street')
    else:
        conflicts.append('identifier found at a different official street')
    number_match=a['number'] is not None and a['number']==b['number']
    landmark_match=a['landmark'] is not None and a['landmark']==b['landmark']
    alias=any(x['street'] in a['street'] and a['number'] in x['numbers'] and b['number'] in x['numbers'] and a['number']!=b['number'] for x in ALIASES)
    if number_match or landmark_match:
        score+=.20;why.append('same address number' if number_match else 'same official landmark')
    elif alias:
        score+=.10;why.append('documented historical number alias (identity NOT established)');conflicts.append(f'official address numbers differ: {a["number"]} / {b["number"]}')
    elif a['number'] is not None and b['number'] is not None:
        if abs(a['number']-b['number'])<=80:
            score+=.04;why.append('nearby address number, not a coordinate distance')
        else:
            score-=.15
        conflicts.append(f'different address numbers: {a["number"]} / {b["number"]}')
    else:
        missing.append('address number/landmark incomplete')
    speeds={l['nominal_speed'] for l in instrument['lanes'] if l.get('nominal_speed') is not None}
    speed=positive_speed(listing.get('speed_limit'))
    speed_match=bool(speed and speed in speeds)
    if speed_match:
        score+=.10;why.append('same nominal speed')
        if len(speeds)>1:
            conflicts.append('multiple lane speed limits require lane resolution')
    elif speed and speeds:
        conflicts.append('official nominal speed differs')
    else:
        missing.append('nominal speed missing/zero in PSIE')
    target_direction=direction(listing.get('direction_raw'))
    directions={direction(l['direction']) for l in instrument['lanes'] if l.get('direction')}
    direction_match=bool(target_direction and target_direction in directions)
    if direction_match:
        score+=.15;why.append('same ordered direction labels')
    elif target_direction and directions:
        # Distinct labels can describe the same physical sense: flag review, not a legal conclusion.
        conflicts.append('official direction labels differ; geographic equivalence unproven')
    else:
        missing.append('direction incomplete')
    type_match=fold(instrument.get('type'))=='FIXO' and listing.get('type') in {'speed_camera','electronic_speed_reducer'}
    if type_match:
        score+=.07;why.append('compatible fixed speed-measuring equipment type')
    elif listing.get('type') and instrument.get('type'):
        conflicts.append('equipment types incompatible')
    for field,weight in [('responsible',.04),('brand',.02),('model',.02)]:
        if listing.get(field) and instrument.get(field):
            if fold(listing[field])==fold(instrument[field]):
                score+=weight;why.append('same '+field)
            else:
                conflicts.append(field+' differs')
    current=any(v.get('valid_from') and v.get('valid_until') and v['valid_from']<=at_date<=v['valid_until'] for v in instrument['verifications']) if at_date else None
    if exact_id:
        score=max(score,.97);why.append('direct serial/Inmetro identifier')
    strong_address=number_match or landmark_match
    confidence='EXACT' if exact_id and same_street and strong_address and not conflicts else 'HIGH' if same_street and strong_address and direction_match and speed_match and type_match and not conflicts else 'MEDIUM' if same_street and strong_address else 'LOW'
    if conflicts:
        confidence='CONFLICT'
    return dict(equipment_id=instrument['equipment_id'],match_score=round(min(.99,max(0,score)),3),match_confidence=confidence,
                why=why,conflicts=conflicts,missing=missing,certificate_covers_date=current,
                serial_number=sorted(serials),inmetro_number=sorted(ids),instrument=instrument)


def resolve(listing,instruments,at_date=None):
    candidates=[c for r in instruments if (c:=compare(listing,r,at_date)) is not None]
    candidates.sort(key=lambda c:(c['match_score'],bool(c['certificate_covers_date'])),reverse=True)
    if not candidates or candidates[0]['match_score']<.25:
        return dict(municipal=listing,match_confidence='UNMATCHED',selected=None,candidates=[])
    selected=candidates[0]
    plausible=[c for c in candidates[1:] if c['match_score']>=selected['match_score']-.08]
    confidence=selected['match_confidence']
    if plausible and confidence in {'EXACT','HIGH'}:
        confidence='MEDIUM';selected={**selected,'why':selected['why']+['competing physical instruments; no unique resolution']}
    return dict(municipal=listing,match_confidence=confidence,selected=selected,candidates=candidates,
                ambiguous=bool(plausible),resolved=confidence in {'EXACT','HIGH'})
