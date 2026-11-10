export const languages = ['en', 'es', 'pt-BR'];

export function translator(language, translations = {}) {
  if (!languages.includes(language)) throw new Error(`Unknown site language: ${language}`);
  return value => translations[value] ?? value;
}

export function localizeContent(value, translate) {
  if (typeof value === 'string') return translate(value).split('\n').map(line => translate(line)).join('\n');
  if (Array.isArray(value)) return value.map(item => localizeContent(item, translate));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, localizeContent(item, translate)]));
  return value;
}

export function languageHref(current, target, filename) {
  if (!languages.includes(current) || !languages.includes(target)) throw new Error('Unknown site language');
  return `${current === 'en' ? '' : '../'}${target === 'en' ? '' : `${target}/`}${filename}`;
}

export function importGateMessage(gate) {
  if (gate === 'pending') return 'Parser and native source tests passed. Browser layout validation is pending.';
  if (gate === 'passed') return 'Parser and native source tests passed. Browser layout validation passed.';
  throw new Error(`Unknown import gate status: ${gate}`);
}
