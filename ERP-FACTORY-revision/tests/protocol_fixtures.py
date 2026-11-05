"""Synthetic responses for local contract tests, never a provider implementation."""
from reviewer.contract import Blocked, digest
from reviewer.packets import build_packets
from reviewer.validation import cross_request


def fixture_scope(material):
    return {'include': sorted(material['files']), 'exclude': {}}


def protocol_bundle(material, changes=None, limit=60_000):
    manifest, parts = build_packets(material, fixture_scope(material), limit)
    bundle = {'protocol_version': 2, 'source_sha': manifest['source_sha'],
              'factory_digest': manifest['factory_digest'], 'parts': [], 'cross': None}
    def report(names, cross=False):
        return {'source_sha': manifest['source_sha'], 'factory_digest': manifest['factory_digest'],
                'reviewed_files': list(names), 'coverage': 'complete', 'cross_component_review': cross,
                'verdict': 'PASS', 'summary_es': 'FICTICIO, no integra ningun servicio.',
                'findings': [], 'limitations_es': ['Prueba simulada, sin proveedor.']}
    for part in parts:
        body = report(part['files'])
        if part['part_id'] == 1:
            body.update(changes or {})
        bundle['parts'].append({'protocol_version': 2, 'phase': 'part', 'part_id': part['part_id'],
                                'artifact_digest': digest(part), 'report': body})
    try:
        cross = cross_request(manifest, bundle['parts'])
    except Blocked:
        return bundle
    body = report(manifest['files'], cross=True)
    if any(item['report']['verdict'] == 'BLOCK' for item in bundle['parts']):
        body['verdict'] = 'BLOCK'
    bundle['cross'] = {'protocol_version': 2, 'phase': 'cross', 'part_id': 0,
                       'artifact_digest': digest(cross), 'report': body}
    return bundle
