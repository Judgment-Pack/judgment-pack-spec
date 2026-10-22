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
    """Apply only Core §4.1's route ceiling, without mutating the base schema."""
    if profile not in ('base', 'extended'):
        raise ValueError('unknown ceiling profile')
    schema = json.loads(SCHEMA.read_text())
    if profile == 'extended':
        schema['$defs']['escalation']['properties']['routes']['maxItems'] = 16
        schema['$defs']['disposition']['properties']['handoff']['properties']['routes']['maxItems'] = 16
    return schema


def validate_core(document, supported=('base',)):
    profile = select_profile(document, supported)
    if isinstance(profile, dict):
        return profile
    validator = Draft202012Validator(core_schema(profile), format_checker=FormatChecker())
    if not validator.is_valid(document):
        return {'status': 'refused', 'code': 'malformed-input'}
    return {'status': 'valid'}
