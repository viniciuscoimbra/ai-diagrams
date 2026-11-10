// Localize the outlined specimen without changing its shapes or text sizes.
const labels = [
  ['ESTUDO DE COR / 01', 'COLOR STUDY / 01', 'ESTUDIO DE COLOR / 01', 13, true],
  ['UM DOCUMENTO, MUITAS FORMAS.', 'ONE DOCUMENT, MANY FORMS.', 'UN DOCUMENTO, MUCHAS FORMAS.', 15, true],
  ['Uma ideia fica clara quando ganha forma.', 'An idea becomes clear when it takes shape.', 'Una idea se aclara cuando toma forma.', 43],
  ['Da descrição ao diagrama, com o fonte sempre por perto.', 'From description to diagram, with the source close at hand.', 'De la descripción al diagrama, con el fuente siempre cerca.', 23],
  ['DA IDEIA À IMAGEM', 'FROM IDEA TO IMAGE', 'DE LA IDEA A LA IMAGEN', 13, true],
  ['Descrição', 'Description', 'Descripción', 25], ['Fonte', 'Source', 'Fuente', 25],
  ['Diagrama', 'Diagram', 'Diagrama', 25],
  ['sua ideia em texto', 'your idea in words', 'tu idea en texto', 13, true],
  ['arquivo editável', 'editable file', 'archivo editable', 13, true],
  ['confere geometria', 'checks geometry', 'revisa geometría', 13, true],
  ['imagem final', 'final image', 'imagen final', 13, true],
  ['O gate confere caixas, textos e conectores antes da renderização.', 'The gate checks boxes, text and connectors before rendering.', 'El gate revisa cajas, textos y conectores antes del renderizado.', 18],
  ['LEGENDA', 'LEGEND', 'LEYENDA', 13, true],
  ['Ideia', 'Idea', 'Idea', 18], ['Construção', 'Construction', 'Construcción', 18],
  ['Verificação', 'Verification', 'Verificación', 18], ['Resultado', 'Result', 'Resultado', 18],
  ['Estudo de identidade com a paleta viva. O tema atual do produto permanece igual.', 'Identity study with the brand palette. The current product theme stays the same.', 'Estudio de identidad con la paleta de marca. El tema actual del producto se mantiene.', 18],
  ['ai-diagrams · Fluxo de geração · 2026-11', 'ai-diagrams · Generation flow · 2026-11', 'ai-diagrams · Flujo de generación · 2026-11', 13, true],
  ['Proposta visual / sem execução do gate', 'Visual proposal / gate not run', 'Propuesta visual / gate sin ejecutar', 13],
];
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
export function brandPreview(svg, language, fonts) {
  if (language === 'pt-BR') return svg;
  const index = language === 'en' ? 1 : 2;
  const result = svg.replace(/<g fill="([^"]+)" aria-label="([^"]+)">([\s\S]*?)<\/g>/g, (all, color, label, paths) => {
    const row = labels.find(item => item[0] === label);
    if (!row) return all;
    const [, x, y] = paths.match(/translate\(([\d.]+) ([\d.]+)\)/);
    return `<text x="${x}" y="${y}" fill="${color}" font-family="${row[4] ? 'JetBrains Mono' : 'Inter'}" font-size="${row[3]}" font-weight="${row[3] === 43 || row[3] === 25 ? 600 : 400}">${escape(row[index])}</text>`;
  }).replace(/<title>[\s\S]*?<\/title>/, `<title>${escape(labels[2][index])}</title>`).replace(/<desc>[\s\S]*?<\/desc>/, '');
  return result.replace(/(<svg\b[^>]*>)/, `$1<style>${fonts.join('\n')}</style>`);
}
