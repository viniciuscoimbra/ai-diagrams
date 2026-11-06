"""Check de registro técnico nos textos que situam o leitor: título, subtítulo, kicker e faixas.

O texto que abre um diagrama diz o que ele mostra, o recorte e como ler. Promessa,
adjetivo de valor, metáfora e frase de efeito reprovam com TEXTO-MARKETING.
Usado por poster_lint.py, conceitual.py e gerar_bpmn.py.
"""
import re

# termos de venda ou de efeito; o radical cobre as flexões
MARKETING = [
    r'transform(a|am|ar|ação|ador)\b', r'revolucion', r'potencializ',
    r'alavanc', r'impulsion', r'empoder', r'sem fric[cç]', r'de ponta\b', r'robust', r'poderos',
    r'inteligente', r'incr[ií]ve', r'perfeit', r'\bf[aá]cil\b', r'facilmente', r'm[aá]gic',
    r'nunca mais', r'o futuro\b', r'\bjornada', r'experi[eê]ncia (única|incr|fluida)', r'\bfluid[oa]\b',
    r'seamless', r'inovador', r'disrupt', r'\beleva\b', r'essencial', r'crucial', r'fundamental',
    r'simplesmente', r'verdadeir', r'sem esfor[cç]o', r'de verdade\b',
    r'—', r', e ningu[eé]m\b', r'\bn[aã]o [eé] [^.;:]{1,40}[,;] [eé]\b',
]
_RE = re.compile('|'.join(MARKETING), re.I)

_BLOCOS = [r'<h1[^>]*>(.*?)</h1>',
           r'<div class="(?:sub|kicker|f1|f2)"[^>]*>(.*?)</div>']


def _limpo(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()


def textos_de_abertura(html):
    """Título, subtítulo, kicker e faixas de um fonte HTML."""
    out = []
    for padrao in _BLOCOS:
        out += [_limpo(m) for m in re.findall(padrao, html, flags=re.S)]
    return [t for t in out if t]


def marketing(textos):
    """Lista de (termo, trecho) com cara de marketing nos textos dados."""
    achados = []
    for t in textos:
        for m in _RE.finditer(t):
            achados.append((m.group(0), t[:60]))
    return achados


MENSAGEM = ('reescreva em registro técnico: o que o diagrama mostra, o recorte e como ler; '
            'sem promessa, adjetivo de valor ou frase de efeito')
