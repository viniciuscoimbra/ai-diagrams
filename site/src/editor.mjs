export function contrast(a, b) {
  const luminance = hex => {
    const rgb = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255)
      .map(channel => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

export function contrastPairs(theme) {
  const c = theme.colors;
  return [['Ink / paper', 'ink', 'paper'], ['Support / paper', 'support', 'paper'], ['Muted / paper', 'muted', 'paper'],
    ['Accent / paper', 'accent', 'paper'], ['Ink / zone', 'ink', 'zone'], ['Risk / risk background', 'risk', 'risk_bg']]
    .map(([label, fg, bg]) => ({ label, tokens: [fg, bg], foreground: c[fg], background: c[bg], ratio: contrast(c[fg], c[bg]) }));
}
