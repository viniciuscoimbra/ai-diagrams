// Spec files between the public English names and the engine's internal names; the same rules as scripts/spec.py.
// The public names are in scripts/spec_keys.json. The 0.1.x Portuguese names are the internal ones and keep working until 0.3.0.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const MAPA = JSON.parse(fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'spec_keys.json'), 'utf8'));
const COMUNS = new Set(['swimlanes', 'sequence', 'states', 'er_model', 'er_layout', 'comparison_yaml']);
const DADOS = new Set(['schemas', 'tabelas']);

function tabelas(tipo) {
  const chaves = { ...(COMUNS.has(tipo) ? MAPA.common.keys : {}), ...MAPA[tipo].keys };
  const valores = {};
  for (const secao of [...(COMUNS.has(tipo) ? ['common'] : []), tipo])
    for (const [campo, mapa] of Object.entries(MAPA[secao].values)) valores[campo] = { ...(valores[campo] || {}), ...mapa };
  return { chaves, valores };
}

function troca(obj, chaves, valores, campos) {
  if (Array.isArray(obj)) return obj.map(v => troca(v, chaves, valores, campos));
  if (!obj || typeof obj !== 'object') return obj;
  const out = {};
  for (const [k, v0] of Object.entries(obj)) {
    const nk = chaves[k] ?? k;
    let v = DADOS.has(nk) && v0 && typeof v0 === 'object' && !Array.isArray(v0)
      ? Object.fromEntries(Object.entries(v0).map(([dk, dv]) => [dk, troca(dv, chaves, valores, campos)]))
      : troca(v0, chaves, valores, campos);
    const mapa = valores[campos[nk] ?? nk];
    if (mapa && typeof v === 'string') v = mapa[v] ?? v;
    out[nk] = v;
  }
  return out;
}

// public (English) or 0.1.x spec -> internal spec
export function ler(tipo, spec) {
  const { chaves, valores } = tabelas(tipo);
  const interno = Object.fromEntries(Object.entries(chaves).map(([pt, en]) => [en, pt]));
  const inverso = Object.fromEntries(Object.entries(valores).map(([campo, m]) => [campo, Object.fromEntries(Object.entries(m).map(([pt, en]) => [en, pt]))]));
  return troca(spec, interno, inverso, chaves);
}

// internal spec -> public (English) spec
export function escrever(tipo, spec) {
  const { chaves, valores } = tabelas(tipo);
  return troca(spec, chaves, valores, {});
}
