#!/usr/bin/env python3
"""Confere o tema contra o pipeline: temas/ai-diagrams.json é a fonte da verdade das cores.

Uso: python3 conferir_tema.py [tema.json]   (padrão: temas/ai-diagrams.json desta skill)

Checks (exit 1 em qualquer falha):
  TOKEN-DIVERGE    valor do :root de assets/estilo.css, assets/estilo-conceitual.css ou do
                   TEMA de bpmn/gerar_bpmn.py diferente do JSON, ou token ausente.
  COR-FORA-DO-TEMA cor literal no CSS base fora do :root, nos geradores (der/*.mjs,
                   scripts/gerar_*.py) ou no gerar_bpmn.py fora do dicionário TEMA.
"""
import json, os, re, sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SK, 'scripts'))
import cor_tema


def tokens_root(css):
    m = re.search(r':root\{(.*?)\n\}', css, re.S)
    corpo = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    return {k: v.strip() for k, v in re.findall(r'--([\w-]+):([^;]+);', corpo)}, css[:m.start()] + css[m.end():]


def main():
    tema = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SK, 'temas', 'ai-diagrams.json')))
    falhas = []
    todas = {**tema['cores'], **tema['cores_derivadas'], **tema['paleta_der']}
    esperado = {k.replace('_', '-'): v.upper() for k, v in todas.items()}
    calor = esperado.pop('der-calor')
    esperado['der-calor-rgb'] = ','.join(str(int(calor[i:i + 2], 16)) for i in (1, 3, 5))

    def confere(nome, achado, chaves):
        for k in chaves:
            if k not in achado:
                falhas.append('TOKEN-DIVERGE %s: falta --%s' % (nome, k))
            elif achado[k].upper().replace(' ', '') != esperado[k]:
                falhas.append('TOKEN-DIVERGE %s: --%s é %s, o tema diz %s' % (nome, k, achado[k], esperado[k]))

    base = {k.replace('_', '-') for k in list(tema['cores']) + ['acento_forte', 'cinza_claro']}
    for arq, chaves in (('estilo.css', set(esperado)), ('estilo-conceitual.css', base)):
        css = open(os.path.join(SK, 'assets', arq)).read()
        achado, resto = tokens_root(css)
        confere(arq, achado, sorted(chaves))
        for k, v in achado.items():  # --apoio-rgb e afins repetem a cor em canais, para rgba()
            if k.endswith('-rgb') and k != 'der-calor-rgb':
                cor = '#' + ''.join('%02X' % int(c) for c in v.split(','))
                if cor != esperado.get(k[:-4]):
                    falhas.append('TOKEN-DIVERGE %s: --%s é %s, o tema diz %s' % (arq, k, cor, esperado.get(k[:-4])))
        falhas += ['COR-FORA-DO-TEMA %s: %s na linha %d' % (arq, c, l) for c, l in cor_tema.cores_fora(resto)]

    bpmn = open(os.path.join(SK, 'bpmn', 'gerar_bpmn.py')).read()
    m = re.search(r'^TEMA = \{.*?\}\n', bpmn, re.S | re.M)
    confere('gerar_bpmn.py', dict(re.findall(r"'([\w-]+)': '(#\w+)'", m.group(0))),
            re.findall(r"'([\w-]+)': '#", m.group(0)))
    falhas += ['COR-FORA-DO-TEMA gerar_bpmn.py: %s' % c for c, _ in cor_tema.cores_fora(bpmn.replace(m.group(0), ''))]

    geradores = [os.path.join(SK, 'der', f) for f in sorted(os.listdir(os.path.join(SK, 'der'))) if f.endswith('.mjs')]
    geradores += [os.path.join(SK, 'scripts', f) for f in sorted(os.listdir(os.path.join(SK, 'scripts')))
                  if f.startswith('gerar_') and f.endswith('.py')]
    for g in geradores:
        falhas += ['COR-FORA-DO-TEMA %s: %s na linha %d' % (os.path.basename(g), c, l)
                   for c, l in cor_tema.cores_fora(open(g).read())]

    for f in falhas:
        print('  ' + f)
    print('tema: %d tokens conferidos, %d falhas' % (len(esperado), len(falhas)))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
