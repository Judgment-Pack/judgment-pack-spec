"""Structural Core profile admission reference; not an evaluator or a safety claim."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = Path(__file__).resolve().parents[1] / 'schema/judgment-pack-core.schema.json'


def select_profile(document, supported):
    if not isinstance(document, dict):
        return {'status': 'refused', 'code': 'malformed-input'}
    profile = document.get('profile', 'base')
    if profile not in ('base', 'extended'):
        return {'status': 'refused', 'code': 'malformed-input'}
    if profile not in supported:
        return {'status': 'refused', 'code': 'profile-unsupported', 'profile': profile}
    return profile


def core_schema(profile):
    """Apply Core §4.1's Core rows for `profile`, without mutating the base schema.

    The published schema carries the base maxima; each is checked before the extended value
    replaces it, so a schema edit that moved one is refused instead of patched over.
    """
    if profile not in ('base', 'extended'):
        raise ValueError('unknown ceiling profile')
    schema = json.loads(SCHEMA.read_text())
    if profile == 'extended':
        defs = schema['$defs']
        rows = (
            (defs['escalation']['properties']['routes'], 'maxItems', 8, 16),
            (defs['disposition']['properties']['handoff']['properties']['routes'], 'maxItems', 8, 16),
            (defs['annotations'], 'maxProperties', 16, 32),
            (defs['annotations']['additionalProperties']['else'], 'maxItems', 16, 32),
            (defs['annotations']['propertyNames'], 'maxLength', 64, 128),
            (defs['annotationString'], 'maxLength', 256, 512),
            (schema['properties']['valueSets'], 'maxItems', 64, 128),
            (defs['valueSet']['properties']['entries'], 'maxItems', 512, 1024),
        )
        for holder, keyword, base, extended in rows:
            if holder[keyword] != base:
                raise ValueError(f'base ceiling {keyword} is {holder[keyword]}, not {base}')
            holder[keyword] = extended
    return schema


def validate_core(document, supported=('base',)):
    profile = select_profile(document, supported)
    if isinstance(profile, dict):
        return profile
    validator = Draft202012Validator(core_schema(profile), format_checker=FormatChecker())
    if not validator.is_valid(document):
        return {'status': 'refused', 'code': 'malformed-input'}
    return {'status': 'valid'}
