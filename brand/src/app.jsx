import React, { useState } from 'react';
import { Button, Card, SectionHeader, Segmented } from '@refy/ui';
import data from 'brand-data';

const repo = 'https://github.com/viniciuscoimbra/ai-diagrams';
const proposals = [
  { id: 'encontro', name: 'Encontro', description: 'D de diagrams. Haste vertical, círculo da mesma altura e triângulo interno. Uma silhueta clara em tamanhos pequenos.' },
  { id: 'mosaico', name: 'Mosaico', description: 'Quatro formas ocupam a mesma grade. Um pequeno catálogo da diversidade de pôsteres.' },
  { id: 'orbita', name: 'Órbita', description: 'Círculo, meia-lua e quadrado. Um pôster com mais movimento e curvas.' },
];

export function App() {
  const [mode, setMode] = useState('light');
  React.useEffect(() => {
    const requested = new URLSearchParams(location.search).get('theme');
    setMode(requested === 'dark' ? 'dark' : 'light');
  }, []);
  const logo = mode === 'dark' ? 'logo-solid-reverse.svg' : 'logo-solid.svg';
  const download = (file) => {
    const link = document.createElement('a');
    link.href = data.assets[file];
    link.download = file;
    document.body.append(link);
    link.click();
    link.remove();
  };

  return <div id="app-scope" className="brandkit" data-theme={mode}>
    <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
    <header className="masthead">
      <div className="masthead-inner">
        <a href="#conteudo" aria-label="ai-diagrams, início do brandkit"><img className="nav-logo" src={data.assets[logo]} alt="ai-diagrams" /></a>
        <span className="masthead-label">Brandkit / 02</span>
        <Segmented label="Aparência do brandkit" value={mode} onChange={setMode} options={[{ value: 'light', label: 'Claro' }, { value: 'dark', label: 'Escuro' }]} />
      </div>
    </header>

    <main id="conteudo" className="content">
      <div className="intro">
        <div>
          <p className="eyebrow">ai-diagrams · Identidade do produto</p>
          <h1>Documentos<br />ganham vida.</h1>
          <p className="intro-copy">Do texto corrido a diagramas que dão vontade de olhar. Ideias, sistemas e processos encontram uma forma bonita de aparecer.</p>
        </div>
        <div className="intro-aside">
          <p>Uma skill aberta para criar diagramas.</p>
          <p>Claude Code · Codex · Kiro</p>
          <Button href={repo} target="_blank" variant="secondary">Explorar o projeto ↗</Button>
        </div>
      </div>

      <nav className="section-nav" aria-label="Seções do brandkit">
        {[['assinatura', '01 Assinatura'], ['cor-tipografia', '02 Cor e tipografia'], ['tom-de-voz', '03 Tom de voz'], ['aplicacoes', '04 Aplicações']].map(([id, label]) => <Button key={id} href={`#${id}`} size="sm" variant="ghost">{label}</Button>)}
      </nav>

      <Card padding="none" className="brand-board">
        <section id="assinatura" className="brand-section signature-section" aria-label="01 Assinatura">
          <SectionHeader title="01 Assinatura" sub="Um pôster. Muitas formas de ver." />
          <div className="proposals">
            {proposals.map(({ id, name, description }, index) => <figure className="proposal" key={id} data-proposal={id} data-recommended={index === 0 ? 'true' : undefined}>
              <div className="proposal-art brand-paper"><img src={data.assets[`proposta-${id}.svg`]} width="160" height="160" alt={`Proposta ${name}: formas geométricas sobrepostas em um pôster quadrado`} /></div>
              <figcaption>
                <div className="proposal-heading"><h3>{String(index + 1).padStart(2, '0')} / {name}</h3>{index === 0 && <span className="recommendation">Recomendada</span>}</div>
                <p>{description}</p>
                <div className="proposal-sizes">{[16, 32, 64].map(size => <span key={size}><img src={data.assets[`proposta-${id}.svg`]} width={size} height={size} alt={`${name} a ${size} pixels`} /><small>{size} px</small></span>)}</div>
                <Button variant="ghost" size="sm" onClick={() => download(`proposta-${id}.svg`)}>Baixar {name}</Button>
              </figcaption>
            </figure>)}
          </div>
          <p className="section-copy">Encontro forma o D de diagrams: haste vertical à esquerda, bojo circular à direita e triângulo dentro da silhueta. As interseções revelam novas cores.</p>
          <div className="signature-lockups">
            <figure className="signature-main specimen brand-paper"><img src={data.assets['logo-solid.svg']} alt="Assinatura ai-diagrams com símbolo Encontro colorido e nome preto em minúsculas" /><figcaption>Assinatura principal</figcaption></figure>
            <figure className="signature-main specimen brand-ink"><img src={data.assets['logo-solid-reverse.svg']} alt="Assinatura ai-diagrams com símbolo colorido e nome branco sobre fundo preto" /><figcaption>Assinatura para fundo escuro</figcaption></figure>
          </div>
          <div className="signature-variants">
            <figure className="specimen brand-paper"><img src={data.assets['logo-mono-dark.svg']} alt="Assinatura ai-diagrams em uma tinta preta" /><figcaption>Uma tinta / preto</figcaption></figure>
            <figure className="specimen brand-ink"><img src={data.assets['logo-mono-light.svg']} alt="Assinatura ai-diagrams em uma tinta branca" /><figcaption>Uma tinta / branco</figcaption></figure>
          </div>
          <div className="usage-rule"><img src={data.assets['symbol-solid.svg']} width="48" height="48" alt="Símbolo Encontro isolado" /><p>Área livre: ¼ da largura do símbolo em cada lado. Símbolo a partir de 16 px; assinatura a partir de 160 px. Preserve proporções, cores e interseções.</p></div>
          <div className="asset-actions"><Button size="sm" onClick={() => download('logo-solid.svg')}>Baixar assinatura SVG</Button><Button size="sm" variant="secondary" onClick={() => download('logo-solid-reverse.svg')}>Baixar versão para fundo escuro</Button><Button size="sm" variant="ghost" onClick={() => download('logo-mono-dark.svg')}>Baixar monocromática</Button></div>
        </section>

        <section id="cor-tipografia" className="brand-section" aria-label="02 Cor e tipografia">
          <SectionHeader title="02 Cor e tipografia" sub="Cor no desenho. Respiro ao redor." />
          <div className="color-type-grid">
            <div>
              <div className="swatches">{data.palette.colors.map(color => <figure key={color.name}><div className="color-chip" style={{ background: color.hex, color: color.foreground }}><span>Aa</span></div><figcaption>{color.name}<code>{color.hex}</code><small>{color.contrast.toFixed(2)}:1 · texto {color.foreground === '#FFFFFF' ? 'branco' : 'preto'}</small></figcaption></figure>)}</div>
              <p className="color-note">Quatro cores para símbolos, pôsteres e diagramas. A interface usa os neutros do plyngo: preto, branco e cinza, inclusive nos botões e no foco.</p>
              <h3 className="subheading">Quando as cores se encontram</h3>
              <p className="small-note">Multiply em sRGB: cada canal é A × B ÷ 255, arredondado. Os seis pares aparecem abaixo com a tinta de texto que mantém contraste mínimo de 4,5:1.</p>
              <div className="multiply-grid">{data.palette.pairs.map(pair => <figure key={pair.names.join('-')}><div className="multiply-chip" style={{ background: pair.hex, color: pair.foreground }}><span>Aa</span><code>{pair.hex}</code></div><figcaption>{pair.names.join(' + ')}<small>{pair.contrast.toFixed(2)}:1 · texto {pair.foreground === '#FFFFFF' ? 'branco' : 'preto'}</small></figcaption></figure>)}</div>
              <p className="small-note">Os SVGs já contêm as interseções com cor sólida. A aparência não depende do modo de mesclagem do aplicativo. Use o texto indicado sobre cada cor; sobre interseções do símbolo, nenhum texto.</p>
            </div>
            <div className="typography">
              <div className="type-sample">
                <div className="type-heading"><strong>Inter</strong><span>400 · 500 · 600 · 700</span></div>
                <p className="type-display">De repente,<br />tudo se conecta.</p>
                <p>Títulos, texto e assinatura. A mesma família da interface do plyngo, com espaço para o desenho brilhar.</p>
              </div>
              <div className="type-sample mono-sample">
                <div className="type-heading"><strong>JetBrains Mono</strong><span>400 · 600</span></div>
                <p className="mono-display">01 → 02 → 03</p>
                <p>Rótulos, medidas e código.<br />Precisão quando faz diferença.</p>
              </div>
              <p className="small-note">A paleta viva é uma proposta de identidade. O tema de diagramas instalado permanece como está; a proposta fica em tema-vivo.json, dentro deste brandkit.</p>
            </div>
          </div>
        </section>

        <section id="tom-de-voz" className="brand-section voice-section" aria-label="03 Tom de voz">
          <div className="voice-intro"><SectionHeader title="03 Tom de voz" sub="Vivo. Claro. Pé no chão." /><p>A marca convida a experimentar. Frases curtas, verbos concretos e entusiasmo pelo resultado. Explique o próximo passo sem transformar cada mensagem em um manual.</p></div>
          <div className="voice-examples">
            <div><span className="example-label">Convite</span><p>“Seu documento pode virar um belo diagrama. Vamos dar forma à ideia?”</p></div>
            <div><span className="example-label">Resultado</span><p>“O diagrama está pronto. Veja como as partes se conectam.”</p></div>
            <div><span className="example-label">Ajuste necessário</span><p>“Duas caixas se sobrepõem. Vamos abrir espaço entre elas.”</p></div>
          </div>
          <p className="voice-limit">Entusiasmo sem promessas absolutas. A verificação geométrica ajuda no desenho; a revisão do conteúdo continua necessária.</p>
        </section>

        <section id="aplicacoes" className="brand-section applications-section" aria-label="04 Aplicações">
          <SectionHeader title="04 Aplicações" sub="Do ícone na aba ao pôster inteiro." />
          <div className="application-heading"><h3>Cabeçalho do site</h3><span>Interface neutra · símbolo vivo</span></div>
          <div className="site-header-preview">
            <div className="sample-site-header">
              <a href={repo} target="_blank" rel="noreferrer" aria-label="ai-diagrams no GitHub"><img className="nav-logo" src={data.assets[logo]} alt="ai-diagrams" /></a>
              <nav aria-label="Exemplo de navegação do site"><Button href={`${repo}/tree/main/exemplos`} target="_blank" variant="ghost" size="sm">Exemplos</Button><Button href={`${repo}#install`} target="_blank" size="sm">Instalar</Button></nav>
            </div>
          </div>
          <div className="application-grid">
            <div className="social-application">
              <div className="application-heading"><h3>Social preview</h3><span>1280 × 640</span></div>
              <figure className="application-figure social-preview"><img src={data.assets['social-preview.svg']} alt="Social preview ai-diagrams: Documentos ganham vida, com pôster de formas coloridas sobrepostas" /><figcaption>Uma frase direta e um pôster cheio de possibilidades.</figcaption></figure>
              <div className="asset-actions"><Button size="sm" onClick={() => download('social-preview.png')}>Baixar PNG 1280 × 640</Button><Button size="sm" variant="ghost" onClick={() => download('social-preview.svg')}>Baixar SVG</Button></div>
            </div>
            <div className="favicon-application">
              <div className="application-heading"><h3>Favicon</h3><span>16 · 32 · 64 px</span></div>
              <div className="favicon-canvas specimen">
                <div className="favicon-sizes">{[16, 32, 64].map(size => <figure key={size}><img src={data.assets[`favicon-${size}.png`]} width={size} height={size} alt={`Favicon a ${size} pixels`} /><figcaption>{size} px</figcaption></figure>)}</div>
              </div>
              <p className="small-note">Tamanhos reais, sem números ou traços finos dentro do símbolo. As mesmas formas e cores em todas as escalas.</p>
              <div className="asset-actions"><Button size="sm" onClick={() => download('favicon.svg')}>SVG</Button>{[16, 32, 64].map(size => <Button key={size} size="sm" variant="ghost" onClick={() => download(`favicon-${size}.png`)}>PNG {size}</Button>)}</div>
            </div>
          </div>
          <div className="application-heading"><h3>Um documento, um diagrama</h3><span>Paleta viva · proposta</span></div>
          <figure className="application-figure diagram-preview"><img src={data.assets['exemplo-diagrama.svg']} alt="Diagrama de exemplo com etapas em cores vivas, conectores numerados e legenda" /><figcaption>As cores ajudam a encontrar cada etapa. Títulos, formas e conectores também comunicam a estrutura.</figcaption></figure>
          <div className="asset-actions"><Button size="sm" onClick={() => download('exemplo-diagrama.svg')}>Baixar diagrama SVG</Button><p className="small-note">Peça de identidade com a proposta viva. Não representa uma execução do gate.</p></div>
        </section>
      </Card>
      <footer className="page-footer"><p>ai-diagrams · Brandkit v2 · 2026</p><p>Componentes refy. Tema de interface do plyngo.</p></footer>
    </main>
  </div>;
}
