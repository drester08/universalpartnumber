"""Audit supplier pipe table boundaries and internal dimensional arithmetic."""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'artifacts/mining-pressure-systems/technical-manual-20261001.pdf'
SHA = 'FE5731D47330DAD79637F05CC44E969100B62651852E23F64DBAE147794DED4B'
URL = 'https://www.miningpressure.co.za/uploads/1/2/4/2/124291661/mps_technical_manual_full.pdf'
PATTERN = re.compile(r'(?:(?P<dn>\d+) (?P<od>\d+,\d+) )?(?P<wall>\d+,\d+) (?P<inside>\d+,\d+) (?P<mass>\d+,\d+) (?:(?P<designation>\([A-Z]+\)|[A-Z]+) )?(?P<schedule>\d+|–|-)$')


def number(raw):
    return Decimal(raw.replace(',', '.'))


def half_unit(raw):
    return Decimal(1).scaleb(number(raw).as_tuple().exponent)/2


def extract():
    if hashlib.sha256(PATH.read_bytes()).hexdigest().upper() != SHA:
        raise ValueError('MPS original PDF revision changed')
    records = []
    with pdfplumber.open(PATH) as pdf:
        if len(pdf.pages) != 167:
            raise ValueError('MPS manual page count changed')
        for physical in (12,13,14):
            text = pdf.pages[physical-1].extract_text()
            lines = [' '.join(line.split()) for line in text.splitlines()]
            full = ' '.join(lines)
            for heading in ('ASTM A106 – GRADE B SEAMLESS','Nominal Outside Wall Internal Mass Schedule','bore diameter thickness diameter (approx.) number','mm mm mm mm kg/m','NB. ABOVE SIZES ALSO AVAILABLE IN THE FOLLOWING SPECS:','1)API5LX 42; 52; 62 seamless or welded'):
                if heading not in full:
                    raise ValueError('MPS table heading/footnote scope changed')
            if lines[-1] != str(physical):
                raise ValueError('MPS printed page changed')
            dn = od = None
            for ordinal,line in enumerate(lines,1):
                match = PATTERN.fullmatch(line)
                if match is None:
                    continue
                values = match.groupdict()
                if values['dn'] is not None:
                    dn,od = values['dn'],values['od']
                if dn is None:
                    raise ValueError('MPS orphan continuation row')
                records.append(dict(physical_page=physical, text_line=ordinal, nominal_bore=dn,
                                    od_mm_raw=od, wall_mm_raw=values['wall'], id_mm_raw=values['inside'],
                                    mass_approx_kg_m_raw=values['mass'], wall_designation_raw=values['designation'] or '',
                                    schedule_raw=values['schedule'], source_line=line))
    keys = [(r['nominal_bore'],r['wall_designation_raw'],r['schedule_raw']) for r in records]
    if len(set(keys)) != len(keys):
        raise ValueError('MPS duplicate full source key')
    if Counter(r['physical_page'] for r in records) != {12:50,13:46,14:48}:
        raise ValueError('MPS expected page row counts changed')
    return records


def audit(records):
    failures = []
    by_mass = defaultdict(list)
    for row in records:
        od,wall,inside = (number(row[k]) for k in ('od_mm_raw','wall_mm_raw','id_mm_raw'))
        residual = od-2*wall-inside
        printed_bound = half_unit(row['od_mm_raw'])+2*half_unit(row['wall_mm_raw'])+half_unit(row['id_mm_raw'])
        if abs(residual) > printed_bound:
            failures.append(dict(nominal_bore=row['nominal_bore'], schedule_raw=row['schedule_raw'],
                                 physical_page=row['physical_page'], id_mm_raw=row['id_mm_raw'],
                                 od_minus_two_wall_mm=str(od-2*wall), residual_mm=str(residual),
                                 printed_precision_bound_mm=str(printed_bound), source_line=row['source_line']))
        by_mass[(row['nominal_bore'],row['mass_approx_kg_m_raw'])].append(row)
    repeats = [dict(nominal_bore=key[0],mass_approx_kg_m_raw=key[1],
                    rows=[dict(schedule_raw=r['schedule_raw'],wall_mm_raw=r['wall_mm_raw'],source_line=r['source_line']) for r in group])
               for key,group in by_mass.items() if len({r['wall_mm_raw'] for r in group}) > 1]
    return dict(internal_diameter_precision_conflicts=failures, repeated_mass_different_wall=repeats)


def build_report():
    records = extract()
    return dict(policy_version='mps-pipe-table-research-0.1',publisher='Mining Pressure Systems',
                source_role='supplier/fabricator publication; not identified mill for supplied stock',
                source_url=URL,source_sha256=SHA,local_path='registry/artifacts/mining-pressure-systems/technical-manual-20261001.pdf',
                document_pages=167,reviewed_physical_pages=[12,13,14],source_rows=len(records),
                page_row_counts=dict(Counter(str(r['physical_page']) for r in records)),
                product_heading='ASTM A106 – GRADE B SEAMLESS',records=records,diagnostics=audit(records),
                identity_approved=False,registered_new_source=False,source_correction_obtained=False,
                independent_extraction_review='outstanding',
                limitations=['Only selected complete pipe-table pages reviewed; no full-manual visual review.',
                             'Blank group cells inherit nominal bore/OD within page only; wall designations and schedules retained separately.',
                             'Printed-precision arithmetic bound is not a manufacturing tolerance.',
                             'Calculated OD minus twice wall is diagnostic only, not a replacement source value.',
                             'Repeated approximate mass is a publication question, not proof of erroneous mass.',
                             'API5LX seamless/welded footnote is not A106 welded construction permission.',
                             'No supplied dataset rows corrected, no article/certificate verification or UPN.',
                             'Source reuse and independent extraction/applicability review outstanding.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT/'reports/mps-pipe-table-research.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('MPS pipe table research snapshot stale')
    print(f"MPS pipe research: {report['source_rows']} rows; {report['page_row_counts']}; diagnostics {report['diagnostics']}")
