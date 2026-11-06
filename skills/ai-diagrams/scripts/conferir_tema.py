#!/usr/bin/env python3
"""Confere o tema contra o pipeline: o json do tema é a fonte da verdade de cor e fonte.

Uso: python3 conferir_tema.py [tema.json]   (padrão: temas/ai-diagrams.json desta skill)

O :root de tokens de assets/estilo.css e assets/estilo-conceitual.css é só o fallback do tema
padrão: o gate troca esse bloco pelo do tema escolhido (scripts/tema.py). Aqui se confere que o
fallback é exatamente o que tema.py gera para o json, e que nada fora dele fixa cor ou fonte.

Checks (exit 1 em qualquer falha):
  TOKEN-DIVERGE      token do :root do CSS base com valor diferente do json, ausente ou a mais.
  COR-FORA-DO-TEMA   cor literal no CSS base fora do :root de tokens, nos geradores (der/*.mjs,
                     scripts/gerar_*.py) ou no bpmn/gerar_bpmn.py.
  FONTE-FORA-DO-TEMA font-family com família literal nos mesmos arquivos; fonte só por
                     var(--fonte-texto) e var(--fonte-mono).
  TEMA-INCOMPLETO    algum json de temas/ sem uma chave obrigatória (ou TEMA-INVALIDO).
"""
import os, re, sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SK, 'scripts'))
import cor_tema
import tema


def tokens_bloco(css):
    b = tema.bloco_tokens(css)
    if b is None:
        return None, css
    corpo = re.sub(r'/\*.*?\*/', '', css[b[0]:b[1]], flags=re.S)
    achado = {k: v.strip() for k, v in re.findall(r'--([\w-]+):([^;]+);', corpo)}
    return achado, css[:b[0]] + css[b[1]:]


def normal(v):
    return v.replace(' ', '').upper()


def main():
    falhas = []
    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SK, 'temas', 'ai-diagrams.json')
    try:
        esperado = dict(tema.tokens(tema.carregar(caminho)))
    except SystemExit as e:
        print('  ' + str(e))
        sys.exit(1)

    for arq in ('estilo.css', 'estilo-conceitual.css'):
        css = open(os.path.join(SK, 'assets', arq)).read()
        achado, resto = tokens_bloco(css)
        if achado is None:
            falhas.append('TOKEN-DIVERGE %s: sem :root de tokens (--tinta)' % arq)
            achado = {}
        for k, v in esperado.items():
            if k not in achado:
                falhas.append('TOKEN-DIVERGE %s: falta --%s' % (arq, k))
            elif normal(achado[k]) != normal(v):
                falhas.append('TOKEN-DIVERGE %s: --%s é %s, o tema diz %s' % (arq, k, achado[k], v))
        for k in sorted(set(achado) - set(esperado)):
            falhas.append('TOKEN-DIVERGE %s: --%s não vem do tema (o gate troca o bloco e ele some)' % (arq, k))
        falhas += ['COR-FORA-DO-TEMA %s: %s na linha %d' % (arq, c, l) for c, l in cor_tema.cores_fora(resto)]
        falhas += ['FONTE-FORA-DO-TEMA %s: %s na linha %d' % (arq, c, l) for c, l in cor_tema.fontes_fora(resto)]

    geradores = [os.path.join(SK, 'der', f) for f in sorted(os.listdir(os.path.join(SK, 'der'))) if f.endswith('.mjs')]
    geradores += [os.path.join(SK, 'scripts', f) for f in sorted(os.listdir(os.path.join(SK, 'scripts')))
                  if f.startswith('gerar_') and f.endswith('.py')]
    geradores.append(os.path.join(SK, 'bpmn', 'gerar_bpmn.py'))
    for g in geradores:
        txt = open(g).read()
        falhas += ['COR-FORA-DO-TEMA %s: %s na linha %d' % (os.path.basename(g), c, l) for c, l in cor_tema.cores_fora(txt)]
        falhas += ['FONTE-FORA-DO-TEMA %s: %s na linha %d' % (os.path.basename(g), c, l) for c, l in cor_tema.fontes_fora(txt)]

    pasta = os.path.join(SK, 'temas')
    for f in sorted(os.listdir(pasta)):
        if f.endswith('.json'):
            try:
                tema.carregar(os.path.join(pasta, f))
            except SystemExit as e:
                falhas.append(str(e))

    for f in falhas:
        print('  ' + f)
    print('tema: %d tokens conferidos, %d falhas' % (len(esperado), len(falhas)))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
