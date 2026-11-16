// The theme in the browser: the same tokens skills/ai-diagrams/scripts/theme.py writes, so the editor shows what the engine draws.
// check.mjs compares themeTokens() with `theme.py --css` for the shipped themes and a random one.
import {contrast} from './editor.mjs';

export const GROUPS = {
  colors: ['ink', 'support', 'muted', 'zone', 'paper', 'accent', 'risk', 'risk_bg'],
  derived: ['accent_strong', 'muted_light', 'c4_person_type', 'c4_person_desc', 'c4_external', 'c4_boundary'],
  er_palette: ['er_border', 'er_legend', 'er_row_even', 'er_key', 'er_domain', 'er_external', 'er_copy', 'er_strong',
    'er_dependent', 'er_associative', 'er_control', 'er_fact', 'er_versioned', 'er_projection', 'er_trail', 'er_domain_bg',
    'er_config', 'er_reference', 'er_view', 'er_heat'],
};
export const CHANNELS = ['support', 'paper', 'risk'];
export const FONT_NAMES = ['IBM Plex Sans', 'IBM Plex Mono', 'Public Sans', 'Source Code Pro', 'Inter', 'JetBrains Mono'];
const HEX = /^#[\da-f]{6}$/i;

// schema_version 1 (Portuguese keys) -> 2, as theme.py v2()
const V1_GROUPS = {cores: 'colors', cores_derivadas: 'derived', paleta_der: 'er_palette', fontes: 'fonts'};
const V1_KEYS = {
  tinta: 'ink', apoio: 'support', cinza: 'muted', zona: 'zone', papel: 'paper', acento: 'accent', risco: 'risk', risco_fundo: 'risk_bg',
  acento_forte: 'accent_strong', cinza_claro: 'muted_light', c4_pessoa_tipo: 'c4_person_type', c4_pessoa_desc: 'c4_person_desc',
  c4_externo: 'c4_external', c4_limite: 'c4_boundary', der_borda: 'er_border', der_legenda: 'er_legend', der_linha_par: 'er_row_even',
  der_chave: 'er_key', der_dominio: 'er_domain', der_fora: 'er_external', der_copia: 'er_copy', der_forte: 'er_strong',
  der_dependente: 'er_dependent', der_associativa: 'er_associative', der_controle: 'er_control', der_fato: 'er_fact',
  der_versionada: 'er_versioned', der_projecao: 'er_projection', der_trilha: 'er_trail', der_dominio_fundo: 'er_domain_bg',
  der_configuracao: 'er_config', der_referencia: 'er_reference', der_visao: 'er_view', der_calor: 'er_heat', texto: 'text', mono: 'mono',
};
const V1_FRAME = {cabecalho: 'header', rodape: 'footer', rodape_direita: 'footer_right', classificacao: 'classification', mostrar_cliente: 'show_client'};

export function toV2(theme) {
  if (!theme || typeof theme !== 'object' || Array.isArray(theme)) throw new Error('THEME-INVALID: the theme must be a JSON object');
  if (!('cores' in theme) && theme.versao_schema !== 1) return theme;
  const out = {schema_version: 2, name: theme.nome ?? '', company: theme.empresa ?? '', logo: theme.logo ?? null};
  for (const [old, group] of Object.entries(V1_GROUPS)) {
    if (theme[old] && typeof theme[old] === 'object') out[group] = Object.fromEntries(Object.entries(theme[old]).map(([k, v]) => [V1_KEYS[k] ?? k, v]));
  }
  if (theme.moldura) out.frame = Object.fromEntries(Object.entries(theme.moldura).map(([k, v]) => [V1_FRAME[k] ?? k, v]));
  return out;
}

// Same checks and messages as theme.py carregar(); returns the theme as schema_version 2.
export function validate(input) {
  const theme = toV2(input);
  for (const [group, keys] of [...Object.entries(GROUPS), ['fonts', ['text', 'mono']]]) {
    if (!theme[group] || typeof theme[group] !== 'object') throw new Error(`THEME-INCOMPLETE: missing ${group}`);
    for (const key of keys) {
      const value = theme[group][key];
      if (value === undefined || value === null || value === '') throw new Error(`THEME-INCOMPLETE: missing ${group}.${key}`);
      if (group !== 'fonts' && !HEX.test(String(value))) throw new Error(`THEME-INVALID: ${group}.${key} is "${value}"; use #RRGGBB`);
    }
  }
  return theme;
}

const rgb = value => [1, 3, 5].map(start => parseInt(value.slice(start, start + 2), 16)).join(',');

// [token name without --, value], in the order of theme.py tokens()
export function tokenList(theme) {
  const out = [];
  for (const [group, keys] of Object.entries(GROUPS)) {
    for (const key of keys) if (key !== 'er_heat') out.push([key.replaceAll('_', '-'), theme[group][key].toUpperCase()]);
  }
  for (const key of CHANNELS) out.push([`${key}-rgb`, rgb(theme.colors[key])]);
  out.push(['er-heat-rgb', rgb(theme.er_palette.er_heat)]);
  out.push(['font-text', `'${theme.fonts.text}',Arial,sans-serif`]);
  out.push(['font-mono', `'${theme.fonts.mono}',monospace`]);
  return out;
}

export function themeTokens(input, {frame = 'full'} = {}) {
  const theme = validate(input);
  for (const kind of ['text', 'mono']) if (!FONT_NAMES.includes(theme.fonts[kind])) throw new Error(`Font is not embedded: ${theme.fonts[kind]}`);
  const lines = tokenList(theme).map(([name, value]) => `--${name}:${value};`);
  lines.push(`--frame-visibility:${frame === 'minimal' ? 'hidden' : 'visible'};`);
  return `:root{\n${lines.join('\n')}\n}`;
}

// the token :root of an engine HTML file: the first :root that declares --ink
export const ROOT = /:root\s*\{[^}]*--ink\s*:[^}]*\}/;

export function themedHtml(diagram, theme, options = {}) {
  if (!ROOT.test(diagram.html)) throw new Error(`Missing diagram token root: ${diagram.id}`);
  return diagram.html.replace(ROOT, () => themeTokens(theme, options));
}

// The theme file the editor exports: schema_version 2 with the group order of the shipped themes.
export function exportTheme(input) {
  const theme = validate(input);
  const out = {schema_version: 2, name: theme.name || 'my-theme', company: theme.company ?? '', logo: theme.logo ?? null};
  for (const group of [...Object.keys(GROUPS), 'fonts']) out[group] = {...theme[group]};
  if (theme.frame) out.frame = {...theme.frame};
  return out;
}

export {contrast};
