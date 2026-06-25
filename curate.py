"""
curate.py — Build the public-facing data subset for Compliance Atlas.

Reads the full internal feed (5,490 findings, 28 jurisdictions) and produces
a curated public subset (~200 findings, 5 jurisdictions, 2 sectors) for the
public Atlas showcase.

Usage:
    python curate.py

Reads from: data/regulatory-feed.jsonl (full internal feed)
Writes to:  data/public/{summary,findings,conflicts,arbitrage,sectors}.json
"""
import json
import os
from datetime import datetime
from collections import Counter

FEED = os.path.join(os.path.dirname(__file__), 'data', 'regulatory-feed.jsonl')
SAMPLE = os.path.join(os.path.dirname(__file__), 'data', 'sample-feed.jsonl')
# If the full feed isn't available, fall back to the sample (so the public demo works)
if not os.path.exists(FEED) and os.path.exists(SAMPLE):
    print(f'INFO: regulatory-feed.jsonl not found, using sample-feed.jsonl ({os.path.getsize(SAMPLE)//1024}KB)')
    FEED = SAMPLE
OUT = os.path.join(os.path.dirname(__file__), 'data', 'public')
os.makedirs(OUT, exist_ok=True)

# Normalize the 28-jurisdiction mess into canonical public IDs
JURISDICTION_MAP = {
    'us-federal': ['US_FED', 'US Federal', 'US-Federal', 'us_federal', 'us-federal', 'US_FEDERAL'],
    'eu': ['EU', 'eu'],
    'uk': ['UK', 'uk'],
    'sg': ['SG', 'sg', 'singapore', 'Singapore'],
    'japan': ['japan', 'Japan', 'JP', 'jp'],
}
JUR_TO_PUBLIC = {}
for pub_id, variants in JURISDICTION_MAP.items():
    for v in variants:
        JUR_TO_PUBLIC[v] = pub_id
# State-level → federal
JUR_TO_PUBLIC.update({
    'US_NY': 'us-federal', 'US_CA': 'us-federal', 'US_CO': 'us-federal',
    'US-NY': 'us-federal', 'US-CA': 'us-federal', 'US-CO': 'us-federal',
    'US': 'us-federal', 'global': 'us-federal',
})

# Sectors to keep publicly — roll-up map
SECTOR_ROLL = {
    'fintech': 'fintech',
    'crypto': 'crypto',
    'payments': 'fintech', 'banking': 'fintech',
    'securities': 'fintech', 'capital_markets': 'fintech',
    'derivatives': 'fintech', 'financial_services': 'fintech',
}

INTERNAL_TAGS = [
    'INTERNAL', 'INTERNAL NOTE', 'DRAFT', 'REVIEW', 'TODO',
    '[Internal]', 'CONFIDENTIAL', 'agent: A', 'agent: B',
]


def clean_text(s):
    if not s:
        return s
    out = s
    for tag in INTERNAL_TAGS:
        out = out.replace(tag, '').replace(tag.lower(), '')
    return ' '.join(out.split()).strip()


def curate():
    with open(FEED) as f:
        all_findings = [json.loads(line) for line in f if line.strip()]

    findings = []
    for f in all_findings:
        raw_jur = f.get('jurisdiction', '')
        pub_jur = JUR_TO_PUBLIC.get(raw_jur)
        if not pub_jur:
            continue
        pub_sectors = []
        for s in f.get('sectors') or []:
            mapped = SECTOR_ROLL.get(s)
            if mapped:
                pub_sectors.append(mapped)
        if not pub_sectors:
            continue
        pub_sectors = list(dict.fromkeys(pub_sectors))
        if 'ai' in (f.get('sectors') or []):
            pub_sectors.append('ai')
            pub_sectors = list(dict.fromkeys(pub_sectors))
        if f.get('severity') not in ('critical', 'high'):
            continue
        rec = {
            'id': f.get('id'),
            'jurisdiction': pub_jur,
            'regulator': clean_text(f.get('regulator')),
            'type': f.get('type'),
            'title': clean_text(f.get('title')),
            'summary': clean_text(f.get('summary')),
            'source_url': f.get('source_url'),
            'sectors': pub_sectors,
            'severity': f.get('severity'),
            'effective_date': f.get('effective_date'),
            'deadline': f.get('deadline'),
            'confidence': f.get('confidence'),
            'detected_at': f.get('detected_at'),
        }
        findings.append(rec)

    # Dedupe
    seen = set()
    deduped = []
    for f in findings:
        norm_title = (f['title'] or '').lower()[:60]
        key = (f['jurisdiction'], f['regulator'], norm_title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)

    # Sort: critical first, then by deadline
    severity_order = {'critical': 0, 'high': 1}
    deduped.sort(key=lambda r: (
        severity_order.get(r['severity'], 99),
        r.get('deadline') or '9999',
        r.get('detected_at') or '',
    ))

    # Cap at 200
    public_findings = deduped[:200]
    if len(public_findings) < 200:
        public_findings.extend(deduped[200:200 + (200 - len(public_findings))])

    # Stats
    jur_counter = Counter(f['jurisdiction'] for f in public_findings)
    sector_counter = Counter()
    for f in public_findings:
        for s in f['sectors']:
            sector_counter[s] += 1
    sev_counter = Counter(f['severity'] for f in public_findings)

    nearest_deadline = None
    for f in public_findings:
        d = f.get('deadline')
        if d and (nearest_deadline is None or d < nearest_deadline):
            nearest_deadline = d

    summary = {
        'name': 'Compliance Atlas',
        'version': '2.0.0',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'total_findings': len(public_findings),
        'total_unfiltered': len(all_findings),
        'critical_findings': sev_counter.get('critical', 0),
        'high_findings': sev_counter.get('high', 0),
        'jurisdictions': sorted(jur_counter.keys()),
        'jurisdiction_counts': dict(jur_counter),
        'sectors': sorted(sector_counter.keys()),
        'sector_counts': dict(sector_counter),
        'nearest_deadline': nearest_deadline,
        'next_refresh': 'daily 06:00 UTC',
    }

    # Conflicts
    conflict_patterns = [
        {'topic': 'AI Governance',
         'description': 'US (OSTP) requires pre-deployment impact assessments for frontier AI, while EU (AI Act) requires conformity assessments with different scope. Companies face parallel compliance regimes.',
         'jurisdictions': ['us-federal', 'eu']},
        {'topic': 'Crypto Market Structure',
         'description': 'US (Clarity Act proposed) would bifurcate SEC/CFTC oversight of digital assets. EU (MiCA) treats most crypto-assets as e-money or financial instruments. Cross-border listing rules diverge.',
         'jurisdictions': ['us-federal', 'eu', 'uk', 'sg']},
        {'topic': 'Data Residency',
         'description': 'EU (GDPR + Data Act) restricts cross-border data transfer without adequacy decision. UK has separate adequacy regime post-Brexit. Singapore PDPA is more permissive. Multi-region operations require layered controls.',
         'jurisdictions': ['eu', 'uk', 'sg']},
        {'topic': 'Stablecoin Reserves',
         'description': 'US (proposed GENIUS Act) requires 1:1 reserve in cash/T-bills with monthly attestations. EU (MiCA Title III) requires authorization and segregation of reserves. Japan allows trust-based reserves with FSA approval.',
         'jurisdictions': ['us-federal', 'eu', 'japan']},
        {'topic': 'Open Banking',
         'description': 'UK (CMA Order) mandates bank-to-TPP data sharing with standardized APIs. EU (PSD2 + PSR) extends this to include payments initiation. Singapore (MAS) has framework but no mandate. US has no federal equivalent; CFPB §1033 rule in progress.',
         'jurisdictions': ['uk', 'eu', 'sg', 'us-federal']},
    ]
    conflicts = []
    for i, p in enumerate(conflict_patterns, 1):
        anchor_ids = []
        for jur in p['jurisdictions']:
            for f in public_findings:
                if f['jurisdiction'] == jur and any(s in f['sectors'] for s in ['fintech', 'crypto', 'ai']):
                    anchor_ids.append({'id': f['id'], 'jurisdiction': jur, 'title': f['title'][:80]})
                    break
        conflicts.append({
            'id': f'conflict-{i:02d}',
            'topic': p['topic'],
            'description': p['description'],
            'jurisdictions': p['jurisdictions'],
            'severity': 'high',
            'anchor_findings': anchor_ids,
        })

    arbitrage = [
        {'id': 'arb-01', 'sector': 'fintech',
         'opportunity': 'Single AI governance submission',
         'description': 'Companies subject to both US (OSTP) and EU (AI Act) can pre-align documentation, avoiding 2x audit cost.',
         'jurisdictions': ['us-federal', 'eu'], 'magnitude': 'high'},
        {'id': 'arb-02', 'sector': 'crypto',
         'opportunity': 'Cross-jurisdiction stablecoin issuance',
         'description': 'A US-regulated reserve structure (GENIUS Act) plus EU MiCA authorization enables dual-jurisdiction issuance from a single entity.',
         'jurisdictions': ['us-federal', 'eu'], 'magnitude': 'high'},
        {'id': 'arb-03', 'sector': 'fintech',
         'opportunity': 'Open Banking API standardization',
         'description': 'Build to UK Open Banking standard first — extends to EU PSD2/PSR with minimal adaptation.',
         'jurisdictions': ['uk', 'eu', 'sg'], 'magnitude': 'medium'},
    ]

    sectors_data = [
        {'sector': s, 'count': sector_counter[s],
         'critical': sum(1 for f in public_findings if s in f['sectors'] and f['severity'] == 'critical'),
         'share': round(sector_counter[s] / len(public_findings), 3) if public_findings else 0}
        for s in sorted(sector_counter.keys())
    ]

    # Write all files
    for name, data in [
        ('summary', summary),
        ('findings', {'findings': public_findings, 'count': len(public_findings),
                      'total_unfiltered': len(all_findings), 'generated_at': summary['generated_at']}),
        ('conflicts', {'conflicts': conflicts, 'count': len(conflicts), 'generated_at': summary['generated_at']}),
        ('arbitrage', {'opportunities': arbitrage, 'count': len(arbitrage), 'generated_at': summary['generated_at']}),
        ('sectors', {'sectors': sectors_data, 'count': len(sectors_data), 'generated_at': summary['generated_at']}),
    ]:
        with open(os.path.join(OUT, f'{name}.json'), 'w') as f:
            json.dump(data, f, indent=2)

    print(f'✅ Curated {len(public_findings)} findings from {len(all_findings)} '
          f'unfiltered → {OUT}/')
    print(f'   critical: {sev_counter.get("critical", 0)}')
    print(f'   high:     {sev_counter.get("high", 0)}')
    print(f'   jurisdictions: {sorted(jur_counter.keys())}')
    print(f'   sectors: {dict(sector_counter)}')


if __name__ == '__main__':
    curate()
