"""Spec files (the JSON a generator reads) between the public English names and the engine's internal names.

The public names are in spec_keys.json. A spec may also use the 0.1.x Portuguese names, which are the
engine's internal names: they keep working until 0.3.0. ler() turns a spec into the internal form;
escrever() turns an internal spec into the public one, for a generator that writes a spec file.
"""
import json
import os

_MAPA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec_keys.json')))
# kinds that also use the common keys; bpmn already uses English names for everything except header/footer
_COMUNS = {'swimlanes', 'sequence', 'states', 'er_model', 'er_layout', 'comparison_yaml'}
# dicts whose keys are data (schema and table names), not field names
_DADOS = {'schemas', 'tabelas'}


def _tabelas(tipo):
    chaves = dict(_MAPA['common']['keys']) if tipo in _COMUNS else {}
    chaves.update(_MAPA[tipo]['keys'])
    valores = {}
    for secao in (['common'] if tipo in _COMUNS else []) + [tipo]:
        for campo, mapa in _MAPA[secao]['values'].items():
            valores.setdefault(campo, {}).update(mapa)
    return chaves, valores


def _troca(obj, chaves, valores, campos_valor):
    """chaves: public -> internal (or the reverse); valores: field -> {value -> value}; campos_valor: field name -> public field."""
    if isinstance(obj, list):
        return [_troca(v, chaves, valores, campos_valor) for v in obj]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        nk = chaves.get(k, k)
        if nk in _DADOS and isinstance(v, dict):
            v = {dk: _troca(dv, chaves, valores, campos_valor) for dk, dv in v.items()}
        else:
            v = _troca(v, chaves, valores, campos_valor)
        mapa = valores.get(campos_valor.get(nk, nk))
        if mapa and isinstance(v, str):
            v = mapa.get(v, v)
        out[nk] = v
    return out


def ler(tipo, spec):
    """Public (English) or 0.1.x spec -> internal spec."""
    chaves, valores = _tabelas(tipo)
    interno = {en: pt for pt, en in chaves.items()}
    # values by public field name; the internal field name points to it
    inverso = {campo: {en: pt for pt, en in m.items()} for campo, m in valores.items()}
    campos = {pt: en for pt, en in chaves.items()}
    return _troca(spec, interno, inverso, campos)


def escrever(tipo, spec):
    """Internal spec -> public (English) spec."""
    chaves, valores = _tabelas(tipo)
    return _troca(spec, chaves, valores, {})
