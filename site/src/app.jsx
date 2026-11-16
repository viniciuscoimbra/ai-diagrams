import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Card, SectionHeader, Segmented, Input, Select, CodeBlock, Accordion, NavCard, SettingsSubnav } from '@refy-design/web';
import { siteData } from 'virtual:site-data';
import { content as sourceContent } from './content.mjs';
import { translator, localizeContent, languageHref, importGateMessage } from './i18n.mjs';

const t = translator(siteData.language, siteData.translations);
const content = localizeContent(sourceContent, t);
content.aws.prompt = siteData.aws.prompt;
content.aws.exampleData = siteData.aws.exampleData;
import { themeTokens, tokenList, validate, exportTheme, GROUPS } from './preview.mjs';
import { contrastPairs } from './editor.mjs';

const repo = 'https://github.com/viniciuscoimbra/ai-diagrams';
const pages = [
  ['home', '01-home.html', t("Home")], ['catalog', '02-diagrams.html', t("Diagrams")],
  ['aws', '03-aws-architecture.html', t("AWS architecture")], ['themes', '04-themes.html', t("Themes")],
  ['compatibility', '05-compatibility.html', t("Compatibility & install")], ['brand', '06-brand.html', t("Brand")],
  ['import', '07-import.html', t("Import")],
];
const route = id => pages.find(page => page[0] === id)[1];
const familyFor = type => content.families.find(family => family.id === type.family);
const typeHref = type => type.id === 'aws-architecture' ? route('aws') : `${route('catalog')}#${type.id}`;
const themeOptions = [{ value: 'ai-diagrams', label: 'ai-diagrams' }, { value: 'paper', label: 'paper' }];
const modeOptions = [{ value: 'light', label: t("Light") }, { value: 'dark', label: t("Dark") }];

function download(name, value, mime = 'application/json') {
  const url = value.startsWith('data:') ? value : URL.createObjectURL(new Blob([value], { type: mime }));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  if (url.startsWith('blob:')) setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Code({ code, label, language = 'bash' }) {
  return <CodeBlock code={code} label={t(label)} language={language} copyLabel={t("Copy")} copiedLabel={t("Copied")} />;
}

// A diagram in an iframe. The theme travels by postMessage, so a color change repaints without reloading the page.
function Preview({ id = 'aws-architecture', source, theme = siteData.themes['ai-diagrams'], frame = 'full', compact = false, crop = false, inspect = false, onMessage, frameRef, zoom }) {
  const diagram = source || siteData.diagrams.find(item => item.id === id);
  const viewport = useRef(null);
  const iframe = useRef(null);
  const [height, setHeight] = useState(diagram.height);
  // counts real loads of the diagram page; 0 until the first one (a new iframe starts as about:blank)
  const [loaded, setLoaded] = useState(0);
  const [fitScale, setFitScale] = useState((compact ? 360 : 1160) / diagram.width);
  const scale = zoom ? fitScale * zoom : fitScale;
  useEffect(() => {
    setHeight(diagram.height);
    // a diagram that finished loading before hydration fires no load event for React
    try {
      const doc = iframe.current?.contentDocument;
      setLoaded(doc?.readyState === 'complete' && doc.URL !== 'about:blank' ? 1 : 0);
    } catch { setLoaded(0); }
  }, [diagram.url]);
  useEffect(() => {
    const receive = event => {
      if (event.source !== iframe.current?.contentWindow) return;
      if (event.data?.type === 'ai-diagrams-size' && Number.isFinite(event.data.height) && event.data.height > 0) setHeight(event.data.height);
      else if (onMessage) onMessage(event.data);
    };
    addEventListener('message', receive);
    return () => removeEventListener('message', receive);
  }, [diagram.url, onMessage]);
  useEffect(() => {
    // a zoomable preview fits the scroll area around it; the others fit their own width
    const target = zoom ? viewport.current.parentElement : viewport.current;
    const observer = new ResizeObserver(entries => setFitScale(entries[0].contentRect.width / diagram.width));
    observer.observe(target);
    return () => observer.disconnect();
  }, [diagram.width, !!zoom]);
  const post = message => iframe.current?.contentWindow?.postMessage(message, '*');
  useEffect(() => { if (loaded) post({ type: 'ai-diagrams:hello' }); }, [loaded]);
  useEffect(() => {
    if (!loaded) return;
    try { post({ type: 'ai-diagrams:theme', css: themeTokens(theme, { frame }), tokens: tokenList(validate(theme)) }); } catch { /* an invalid theme keeps the last one drawn */ }
  }, [loaded, theme, frame]);
  useEffect(() => { if (loaded) post({ type: 'ai-diagrams:inspect', on: inspect, scale }); }, [loaded, inspect, scale]);
  useEffect(() => { if (frameRef) frameRef.current = { post, loaded }; });
  const box = zoom ? { width: diagram.width * scale, height: height * scale } : { aspectRatio: crop ? '16 / 10' : `${diagram.width} / ${height}` };
  return <div className={`diagram-viewport${compact ? ' compact' : ''}${zoom ? ' zoomable' : ''}`} ref={viewport} style={box}>
    <iframe ref={iframe} title={`${source ? t(source.name) : content.types.find(type => type.id === id).name}, ${theme.name}`}
      sandbox="allow-scripts allow-same-origin" tabIndex={inspect ? 0 : -1} loading="eager" src={diagram.url} onLoad={() => { if (iframe.current?.contentWindow?.location?.href !== 'about:blank') setLoaded(count => count + 1); }}
      width={diagram.width} height={height} style={{ transform: `scale(${scale})` }} />
  </div>;
}

function Header({ page, mode, setMode }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  return <header className="masthead"><div className="masthead-inner">
    <a className="logo-link" href={route('home')} aria-label={t("ai-diagrams home")}><img className="nav-logo" src={siteData.assets[mode === 'dark' ? 'logo-solid-reverse.svg' : 'logo-solid.svg']} alt="ai-diagrams" width="180" /></a>
    <nav className={`main-nav${open ? ' is-open' : ''}`} aria-label={t("Main navigation")}>
      {[['catalog', t("Diagrams")], ['themes', t("Theme editor")], ['import', t("Import")], ['compatibility', t("Models")], ['brand', t("Brand")]].map(([id, label]) => <a key={id} href={route(id)} aria-current={page === id ? 'page' : undefined}>{t(label)}</a>)}
    </nav>
    <form className="header-search" role="search" onSubmit={event => { event.preventDefault(); location.href = `${route('catalog')}?q=${encodeURIComponent(query)}`; }}>
      <Input aria-label={t("Search diagrams")} placeholder={t("Search diagrams")} type="search" value={query} onChange={event => setQuery(event.target.value)} />
    </form>
    <div className="header-actions"><LanguageSelector page={page} /><Segmented label={t("Site appearance")} value={mode} onChange={setMode} options={modeOptions} /><a href={repo}>GitHub ↗</a><Button className="menu-button" variant="secondary" aria-expanded={open} onClick={() => setOpen(!open)}>{t("Menu")}</Button></div>
  </div></header>;
}

function LanguageSelector({ page }) {
  return <Select className="language-select" block={false} aria-label={t('Site language')} value={siteData.language} onChange={event => { location.href = languageHref(siteData.language, event.target.value, pages.find(item => item[0] === page)?.[1] || 'index.html') + location.search + location.hash; }}><option value="en">en</option><option value="es">es</option><option value="pt-BR">pt-BR</option></Select>;
}

function Footer({ page }) {
  return <footer className="site-footer"><div className="footer-top"><a href={route('home')} className="footer-wordmark">ai-diagrams</a><p>{t("Describe it. Keep the source.")}</p><a href="index.html">{t("All seven boards →")}</a></div>
    <div className="footer-bottom"><nav aria-label={t("Project links")}>{[['GitHub', repo], [t("MIT license"), `${repo}/blob/main/LICENSE`], [t("Contribute"), `${repo}/blob/main/CONTRIBUTING.md`], [t("Changelog"), `${repo}/commits/main`]].map(([label, href]) => <a key={label} href={href}>{t(label)}</a>)}</nav>
      <a href="https://github.com/viniciuscoimbra">{t("Made by Vinícius Coimbra")}</a><LanguageSelector page={page} />
    </div></footer>;
}

function PageIntro({ eyebrow, title, children, action }) {
  return <div className="page-intro"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <p className="lead">{children}</p>}</div>{action && <div className="intro-action">{action}</div>}</div>;
}

function TypeCard({ type, index, detailed = false }) {
  const family = familyFor(type);
  return <Card padding="none" className="type-card" id={type.id} data-type-card={type.id}>
    <div className="type-art">
      <div className="type-art-label"><span>{family.name}</span><span>{String(index + 1).padStart(2, '0')}</span></div>
      <Preview id={type.id} compact crop />
    </div>
    <div className="type-description"><h3><a href={typeHref(type)}>{type.name}<span aria-hidden="true"> ↗</span></a></h3><p>{detailed ? type.question : type.summary}</p>{detailed && <p>{type.advantage}</p>}</div>
  </Card>;
}

function TypeGrid({ types = content.types, detailed = false }) {
  return <div className="type-grid">{types.map(type => <TypeCard key={type.id} type={type} detailed={detailed} index={content.types.indexOf(type)} />)}</div>;
}

function ComingSoon() {
  return <section id="coming-soon" className="section coming-section"><SectionHeader title={t("Next on the drawing board")} sub={t("Eight proposed types. None started yet.")} count={t("Coming soon")} />
    <div className="coming-grid">{content.comingSoon.map((item, index) => <article key={item.name} data-upcoming={item.name} data-status="proposed"><span className="mono muted">{String(index + 12).padStart(2, '0')}</span><div><h3>{item.name}</h3><p>{item.description}</p><span className="small muted">{t("Proposed")}</span></div></article>)}</div>
  </section>;
}

function Install({ compact = false }) {
  const [tool, setTool] = useState('npm');
  const selected = content.install.find(item => item.id === tool);
  return <div className="install-content"><Segmented label={t("Installation tool")} value={tool} onChange={setTool} options={content.install.map(item => ({ value: item.id, label: item.id === 'npm' ? item.label : `git clone · ${item.label}` }))} />
    <p className="small muted install-note">{tool === 'npm' ? t("Published on npm as ai-diagrams. npx downloads it on first use.") : t("Use absolute paths for <AI_DIAGRAMS> and <PROJECT>. Check existing installs before creating a link.")}</p>
    <div className="install-columns"><Code code={selected.command} label={`${t('Install in')} ${selected.label}`} /><div className="expected-output"><p className="eyebrow">{t("Expected output")}</p><pre>{selected.expected}</pre><p className="small">{selected.usage}</p><p className="small muted install-note">{selected.note}</p></div></div>
    {!compact && <Accordion type="multiple" items={[
      { id: 'requirements', title: t("Before you install: requirements"), content: <div className="requirements">{content.installPrerequisites.map((item, index) => <div key={index}><code>{item.command}</code><p>{item.expected}</p>{item.note && <p className="small muted">{item.note}</p>}</div>)}</div> },
      { id: 'smoke-test', title: t("Verify the complete pipeline"), content: <><Code code={content.smokeTest.command} label={t("Smoke test")} /><p className="small">{content.smokeTest.expected}</p></> },
      { id: 'web-assistants', title: t("Claude.ai and ChatGPT"), content: <p>{t("The documented installation targets Claude Code, Codex CLI and Kiro CLI. A verified web-app installation is not provided in INSTALL.md.")}</p> },
    ]} />}
  </div>;
}

function LiveDemo() {
  const [tab, setTab] = useState('diagrams');
  const [preset, setPreset] = useState('ai-diagrams');
  const [diagram, setDiagram] = useState('aws-architecture');
  const selected = content.types.find(type => type.id === diagram);
  return <section id="diagram-showcase" aria-label={t("Explore all 11 diagrams")}><Card className="live-demo" padding="none"><div className="demo-toolbar"><Segmented label={t("Explore ai-diagrams")} value={tab} onChange={setTab} options={[{ value: 'diagrams', label: t("Diagrams") }, { value: 'themes', label: t("Themes") }, { value: 'install', label: t("Install") }]} /><span className="mono small muted">{t("Real examples. Editable source.")}</span></div>
    {tab === 'install' ? <div className="demo-install"><Install compact /></div> : <><div className="diagram-tabs" data-showcase-types={content.types.length}><Segmented label={t("Choose a diagram")} value={diagram} onChange={setDiagram} options={content.types.map(type => ({ value: type.id, label: type.name }))} /></div><div className="showcase-question"><p className="eyebrow">{selected.name}</p><h2>{selected.question}</h2></div>{tab === 'themes' && <div className="demo-controls"><Segmented label={t("Diagram preset")} value={preset} onChange={setPreset} options={themeOptions} /><a href={route('themes')}>{t("Open the theme editor →")}</a></div>}<div className="hero-diagram"><Preview id={diagram} theme={siteData.themes[preset]} /></div><div className="demo-caption"><span>{t("Example:")} {selected.name}</span><span>{siteData.language}</span></div></>}
  </Card></section>;
}

function ImportExamples({ compact = false }) {
  const [id, setId] = useState('flowchart');
  const selected = siteData.imports.find(item => item.id === id);
  return <div className="import-examples"><div className="diagram-tabs"><Segmented label={t("Input format")} value={id} onChange={setId} options={siteData.imports.map(item => ({value: item.id, label: t(item.name)}))} /></div><div className="import-meta"><h3>{t(selected.name)}</h3><p className="small muted">{t(importGateMessage(selected.gate))}</p></div><div className="import-input"><Code code={selected.command} label={t("Import command")} /><Code code={selected.inputText} language={selected.syntax} label={selected.input} /></div><div className="import-result" data-import-preview={id}><p className="eyebrow">{t("Generated by the ai-diagrams engine")}</p><Preview source={selected} /></div><div className="demo-caption"><span className="mono">{selected.output}</span><Button variant="secondary" onClick={() => download(selected.input.split('/').at(-1), selected.inputText, 'text/plain;charset=utf-8')}>{t("Download input ↓")}</Button></div>{!compact && <p className="small muted import-note">{t("Unsupported syntax returns an error with its location. The importer keeps the engine's native source, then runs the regular generator and gate.")}</p>}</div>;
}

function Repository() {
  return <section className="section" id="repository"><SectionHeader title={t("Source and package")} sub={t("Made by Vinícius Coimbra")} /><div className="repository-grid"><Card><p className="eyebrow">{t("GitHub")}</p><h3>ai-diagrams</h3><p>{t("Source, examples and issue tracking. MIT license.")}</p><a href={repo}>{t("Open repository ↗")}</a><a href={`${repo}/blob/main/LICENSE`}>{t("MIT license")}</a></Card><Card><p className="eyebrow">{t("npm")}</p><h3>ai-diagrams</h3><p>{t("Published on npm. Zero npm dependencies.")}</p><code>{'npx ai-diagrams install --claude'}</code><a href="https://www.npmjs.com/package/ai-diagrams">{t("Open on npm ↗")}</a></Card></div><a className="author-link" href="https://github.com/viniciuscoimbra">{t("Made by Vinícius Coimbra")}</a></section>;
}

function ImportPage() {
  return <><PageIntro eyebrow={t("Import an existing source")} title={t("Keep the source. Redraw with ai-diagrams.")}>{t("Start from Mermaid, BPMN XML, DDL, CSV or YAML. These examples are converted into the engine's native formats and rendered by its existing generators.")}</PageIntro><ImportExamples /><section className="section"><SectionHeader title={t("From file to checked diagram")} sub={t("The layout is rebuilt by the engine; original drawing coordinates are not preserved.")} /><p className="import-note">{t("A Mermaid flowchart becomes BPMN. A flowchart with subgraph lanes becomes swimlanes. DDL can also produce a schema dependency matrix with --type matrix. A Structurizr DSL workspace becomes one page per C4 view.")}</p><Code code={`npx ai-diagrams import examples/import/${siteData.language}/schema.sql --type matrix --out diagrams/matrix --lang ${siteData.language}`} label={t("DDL to dependency matrix")} /></section><Repository /></>;
}

function Home() {
  return <><div className="home-intro"><div><p className="eyebrow">{t("An open skill for Claude Code, Codex CLI and Kiro CLI")}</p><h1>{t("Describe it in words.")}<br />{t("See how it connects.")}</h1><p className="lead">{t("Turn a document, a process or a database schema into a diagram. Get editable source and a PNG, checked by a geometric gate.")}</p><div className="actions"><Button variant="primary" onClick={() => location.assign(`${route('compatibility')}#install`)}>{t("Install ai-diagrams →")}</Button><Button variant="secondary" onClick={() => location.assign(route('themes'))}>{t("Edit colors in a diagram →")}</Button><Button variant="secondary" onClick={() => { location.hash = 'diagram-showcase'; }}>{t("See diagrams")}</Button></div></div><div className="hero-side"><img src={siteData.assets['symbol-solid.svg']} width="120" height="120" alt={t("Encontro, the ai-diagrams symbol")} /><p>{t("Ideas, systems")}<br />{t("and processes.")}<br /><span className="muted">{t("Give them a shape.")}</span></p></div></div>
    <LiveDemo />
    <section className="workflow" aria-label={t("How it works")}>{[
      ['01', t("Describe"), t("A plain-language request, a document or a DDL.")],
      ['02', t("The gate rejects"), t("Loose arrows, overlapping text and clipped margins.")],
      ['03', t("Receive"), t("Editable source and a PNG you can keep in your repository.")],
    ].map(([number, title, text], index) => <div key={number}><span className="mono muted">{number}</span><h2>{t(title)}{index < 2 && <span aria-hidden="true"> →</span>}</h2><p>{t(text)}</p></div>)}</section>
    <section className="section" id="diagram-types"><SectionHeader title={t("A diagram for the question at hand")} sub={t("11 types, from the first service call to the last database relationship.")} action={<a href={route('catalog')}>{t("Browse all diagrams →")}</a>} /><TypeGrid /></section>
    <section className="section models-section"><SectionHeader title={t("Choose a model with evidence")} sub={t("Setups with a recorded clean pass, read from docs/models/runs.json. A measured pass is not a universal ranking.")} action={<a href={route('compatibility')}>{t("See all measurements →")}</a>} /><div className="model-list">{siteData.compat.rows.map(row => { const passed = siteData.compat.columns.filter((column, index) => row.cells[index].result === 'pass'); return <div key={row.type}><a href={typeHref(content.types.find(type => type.id === row.type))}>{typeName(row.type)}</a><strong>{passed.length ? passed.map(column => columnLabel(column).at(-1)).join(', ') : t("No clean pass yet")}</strong><span className="small muted"><StateIcon state={passed.length ? 'pass' : 'none'} size={14} /> {passed.length}/{siteData.compat.columns.length} {t("measured setups passed with a clean PNG")}</span></div>; })}</div></section>
    <ComingSoon />
    <section className="section" id="import"><SectionHeader title={t("Already have a source file?")} sub={t("Nine input formats, using the same generators and gate.")} action={<a href={route('import')}>{t("Explore importing →")}</a>} /><ImportExamples compact /></section>
    <section className="section" id="install"><SectionHeader title={t("Keep the workflow in your CLI")} sub={t("Install once. Describe the next diagram in the project where it belongs.")} /><Install compact /><a href={`${route('compatibility')}#install`}>{t("Requirements and full installation →")}</a></section>
    <Repository />
  </>;
}

function Catalog() {
  const [family, setFamily] = useState('all');
  const [query, setQuery] = useState('');
  useEffect(() => setQuery(new URLSearchParams(location.search).get('q') || ''), []);
  const filtered = content.types.filter(type => (family === 'all' || type.family === family) && `${type.name} ${type.summary} ${type.question}`.toLowerCase().includes(query.toLowerCase()));
  return <><PageIntro eyebrow={t("The diagram library")} title={t("Start with a question.")}>{t("Find the form that makes the answer visible. Every preview comes from a real example in the repository.")}</PageIntro>
    <div className="catalog-controls"><Segmented label={t("Diagram family")} value={family} onChange={setFamily} options={[{ value: 'all', label: t("All types") }, ...content.families.map(item => ({ value: item.id, label: item.name }))]} /><Input type="search" aria-label={t("Filter diagrams")} placeholder={t("Find a diagram…")} value={query} onChange={event => setQuery(event.target.value)} /></div>
    <p className="small muted results-count" role="status">{filtered.length} {t("of 11 types")}</p><TypeGrid types={filtered} detailed />{filtered.length === 0 && <p className="empty-results">{t("No diagrams match. Try a broader question or choose another family.")}</p>}<ComingSoon />
  </>;
}

// ---------- Compatibility: every state comes from the measurement files (compatibility.mjs) ----------
const STATE_LABEL = { pass: "Passed", fail: "Failed", none: "Not measured" };
const RESULT_LABEL = { pass: "Passed", gate_only: "Gate only", defect: "Defect", fail: "Failed", not_measured: "Not measured" };

function StateIcon({ state, size = 18 }) {
  const label = t(STATE_LABEL[state]);
  return <svg className={`state-icon is-${state}`} width={size} height={size} viewBox="0 0 20 20" role="img" aria-label={label}>
    <circle cx="10" cy="10" r="9" />
    {state === 'pass' && <path d="M5.8 10.4l2.7 2.7 5.7-6" />}
    {state === 'fail' && <path d="M6.6 6.6l6.8 6.8M13.4 6.6l-6.8 6.8" />}
    {state === 'none' && <path d="M6.5 10h7" />}
  </svg>;
}

const typeName = id => content.types.find(type => type.id === id)?.name ?? id;
const columnLabel = column => [column.cli_label, column.model_label].filter(Boolean);

function MeasureCell({ cell }) {
  const text = t(RESULT_LABEL[cell.result]);
  return <span className={`measure is-${cell.state}`} title={cell.note ? `${text}: ${t(cell.note)}` : text}>
    <StateIcon state={cell.state} />
    <span className="measure-text">{text}{cell.note && <span className="measure-note">{t(cell.note)}</span>}</span>
    {cell.source && <a className="measure-source" href={`#source-${cell.source}`} aria-label={`${t("Source")} ${cell.source}`}>{cell.source}</a>}
  </span>;
}

function CompatibilityMatrix({ only }) {
  const data = siteData.compat;
  const clis = [...new Set(data.columns.map(column => column.cli_label))];
  const [cli, setCli] = useState('all');
  const columns = data.columns.map((column, index) => ({ column, index })).filter(({ column }) => cli === 'all' || column.cli_label === cli);
  const rows = data.rows.filter(row => !only || row.type === only);
  const gate = Object.fromEntries(data.gates.rows.map(row => [row.type, row.state]));
  const count = state => rows.reduce((sum, row) => sum + columns.filter(({ index }) => row.cells[index].state === state).length, 0);
  return <div className="compat" data-compatibility={only ? 'single' : 'full'}>
    {!only && <div className="compat-head">
      <div className="compat-totals" aria-label={t("Totals")}>{['pass', 'fail', 'none'].map(state => <div key={state} className={`compat-total is-${state}`}><StateIcon state={state} size={22} /><strong>{count(state)}</strong><span>{t(STATE_LABEL[state])}</span></div>)}</div>
      <Segmented label={t("Filter by CLI")} value={cli} onChange={setCli} options={[{ value: 'all', label: t("All CLIs") }, ...clis.map(label => ({ value: label, label }))]} />
    </div>}
    <div className="compat-scroll" role="region" aria-label={t("Measured compatibility by diagram type and model")} tabIndex={0}>
      <table className="compat-table">
        <caption className="visually-hidden">{t("Measured compatibility by diagram type and model")}</caption>
        <thead><tr><th scope="col">{t("Diagram type")}</th><th scope="col" className="gate-col">{t("Template gate")}<span>{data.gates.date || t("not run")}</span></th>{columns.map(({ column }) => <th scope="col" key={column.id}>{columnLabel(column).map((part, i) => i ? <strong key={i}>{part}</strong> : <span key={i}>{part}</span>)}</th>)}</tr></thead>
        <tbody>{rows.map(row => <tr key={row.type}>
          <th scope="row"><a href={typeHref(content.types.find(type => type.id === row.type))}>{typeName(row.type)}</a></th>
          <td className="gate-col"><span className={`measure is-${gate[row.type]}`}><StateIcon state={gate[row.type]} /><span className="measure-text">{t(STATE_LABEL[gate[row.type]])}</span></span></td>
          {columns.map(({ column, index }) => <td key={column.id}><MeasureCell cell={row.cells[index]} /></td>)}
        </tr>)}</tbody>
        {!only && <tfoot><tr><th scope="row">{t("Passed")}</th><td className="gate-col">{data.gates.rows.filter(row => row.state === 'pass').length}/{data.gates.rows.length}</td>{columns.map(({ column, index }) => <td key={column.id}>{rows.filter(row => row.cells[index].state === 'pass').length}/{rows.length}</td>)}</tr></tfoot>}
      </table>
    </div>
    <div className="compat-cards">{rows.map(row => <article key={row.type} className="compat-card"><h3>{typeName(row.type)}</h3>
      <ul><li><span>{t("Template gate")}</span><StateIcon state={gate[row.type]} /></li>{columns.map(({ column, index }) => <li key={column.id}><span>{columnLabel(column).join(' · ')}</span><MeasureCell cell={row.cells[index]} /></li>)}</ul></article>)}</div>
  </div>;
}

function Legend() {
  const results = siteData.compat.results;
  return <dl className="measurement-legend">{['pass', 'gate_only', 'defect', 'fail', 'not_measured'].map(key => <div key={key}><dt><StateIcon state={{ pass: 'pass', gate_only: 'pass', defect: 'fail', fail: 'fail', not_measured: 'none' }[key]} />{t(RESULT_LABEL[key])}</dt><dd>{t(results[key])}</dd></div>)}</dl>;
}

function InstallChecks() {
  const { install } = siteData.compat;
  const groups = [['claude', 'Claude Code'], ['codex', 'Codex CLI'], ['kiro', 'Kiro CLI'], [null, t("Any CLI")]];
  return <section className="section" id="install-checks"><SectionHeader title={t("Installation checks")} sub={install.date ? `${t("npm smoke test")} · ${install.date} · ai-diagrams ${install.package} · Node ${install.node} · ${install.platform}` : t("The npm smoke test has not written a report yet.")} />
    <div className="check-grid">{groups.map(([cli, label]) => <Card key={label} className="check-card"><h3>{label}</h3><ul>{install.rows.filter(row => row.cli === cli).map(row => <li key={row.id}><StateIcon state={row.state} /><span>{t(row.label)}</span></li>)}</ul></Card>)}</div></section>;
}

function ImportChecks() {
  const rows = siteData.compat.imports;
  const ids = [...new Set(rows.map(row => row.id))];
  const langs = ['en', 'es', 'pt-BR'];
  return <section className="section" id="import-checks"><SectionHeader title={t("Import samples")} sub={t("Source test and full gate of each sample in examples/import/manifest.json.")} />
    <div className="compat-scroll" tabIndex={0} role="region" aria-label={t("Import samples")}><table className="compat-table import-table"><thead><tr><th scope="col">{t("Sample")}</th>{langs.map(lang => <th scope="col" key={lang}><span>{t("Source test · gate")}</span><strong>{lang}</strong></th>)}</tr></thead>
      <tbody>{ids.map(id => <tr key={id}><th scope="row">{id}</th>{langs.map(lang => { const row = rows.find(item => item.id === id && item.language === lang); return <td key={lang}>{row ? <span className="pair"><StateIcon state={row.tested} /><StateIcon state={row.gate} /></span> : <StateIcon state="none" />}</td>; })}</tr>)}</tbody></table></div></section>;
}

function AwsPage() {
  const [query, setQuery] = useState('');
  const [preset, setPreset] = useState('ai-diagrams');
  const [frame, setFrame] = useState('full');
  return <div className="type-layout"><aside className="type-sidebar"><p className="eyebrow">{t("Diagram types / 11")}</p><Input aria-label={t("Find a type")} type="search" placeholder={t("Find a type…")} value={query} onChange={event => setQuery(event.target.value)} /><SettingsSubnav label={t("Diagram types")} activeHref={route('aws')} items={content.types.filter(type => type.name.toLowerCase().includes(query.toLowerCase())).map(type => ({ href: typeHref(type), label: type.name, icon: <span className="family-dot" aria-hidden="true" /> }))} /><a href={`${route('catalog')}#coming-soon`}>{t("Coming soon →")}</a></aside>
    <div className="type-main"><PageIntro eyebrow={t("Diagrams / Architecture")} title={t("AWS architecture poster")}>{t("Which services exist, and how does a request move through them?")}</PageIntro>
      <Card padding="none" className="aws-preview"><div className="demo-controls"><Segmented label={t("Example theme")} value={preset} onChange={setPreset} options={themeOptions} /><Select block={false} aria-label={t("Example frame")} value={frame} onChange={event => setFrame(event.target.value)}><option value="full">{t("Full frame")}</option><option value="minimal">{t("Drawing only")}</option></Select></div><div className="type-art"><Preview theme={siteData.themes[preset]} frame={frame} /></div><div className="demo-caption">{t("Transfer fraud decision")}</div></Card>
      <section className="use-cases section"><div><h2>{t("When to use it")}</h2><p>{content.aws.when}</p></div><div><h2>{t("What it makes clear")}</h2><ul>{content.aws.advantages.map(text => <li key={text}>{text}</li>)}</ul></div><div><h2>{t("When another type fits")}</h2><p>{content.aws.avoid}</p></div></section>
      <section className="section"><SectionHeader title={t("Start with the actual example")} sub={t("The request and source document use the selected language.")} /><Code code={content.aws.prompt} label="prompt.md" language="markdown" /><Accordion items={[{ id: 'example-data', title: t("Read the accompanying source document"), content: <Code code={content.aws.exampleData} label="antifraud-decision.md" language="markdown" /> }]} /></section>
      <section className="section gate-section"><SectionHeader title={t("What the gate checks")} sub={t("Geometry checks help catch drawing defects. Review the meaning of the diagram yourself.")} /><ul className="gate-list">{content.aws.gate.map(text => <li key={text}>{text}</li>)}</ul><Card className="gate-failure"><p className="eyebrow">{t("A rejected case")}</p><p>{content.aws.gateFailure}</p></Card></section>
      <section className="section"><SectionHeader title={t("Measured compatibility")} sub={t("Results for this type, read from docs/models/runs.json.")} /><CompatibilityMatrix only="aws-architecture" /><a href={route('compatibility')}>{t("Read all measurements and sources →")}</a></section>
    </div></div>;
}

function CompatibilityPage() {
  const { sources } = siteData.compat;
  return <><PageIntro eyebrow={t("Compatibility / Install")} title={t("What works, measured.")}>{t("Every cell is a recorded run. Green passed, red failed, gray was not measured. Nothing on this page is typed by hand: it is read from the files the tests and runs write.")}</PageIntro>
    <CompatibilityMatrix /><Legend />
    <InstallChecks />
    <ImportChecks />
    <section className="section provenance"><SectionHeader title={t("Where each result comes from")} sub={t("Sources: docs/models/runs.json, docs/models/gates.json, docs/models/install-checks.json and examples/import/manifest.json.")} /><ol>{Object.entries(sources).map(([id, source]) => <li key={id} id={`source-${id}`} value={Number(id)}>{source.date && <span className="mono muted">{source.date} · </span>}{t(source.text)}</li>)}</ol><a href={`${repo}/blob/main/docs/models.md`}>{t("Read the source table on GitHub ↗")}</a></section>
    <section className="section install-section" id="install"><SectionHeader title={t("Install ai-diagrams")} sub={t("Choose your CLI, check the requirements, and run the documented steps.")} /><Install /><p className="small muted">{t("Installation source:")} <a href={`${repo}/blob/main/INSTALL.md`}>INSTALL.md</a>{t(". The diagram workflow uses local headless Chrome; this site does not need it.")}</p></section>
  </>;
}

// ---------- Themes: a canvas editor. Click a shape, the panel jumps to the token it paints with. ----------
const TOKEN_LABELS = {
  ink: 'Ink', support: 'Support', muted: 'Muted', zone: 'Zone', paper: 'Paper', accent: 'Accent', risk: 'Risk', risk_bg: 'Risk background',
  accent_strong: 'Strong accent', muted_light: 'Light muted', c4_person_type: 'C4 person type', c4_person_desc: 'C4 person description',
  c4_external: 'C4 external system', c4_boundary: 'C4 boundary', er_border: 'ER border', er_legend: 'ER legend', er_row_even: 'ER even row',
  er_key: 'ER key', er_domain: 'ER domain', er_external: 'ER external', er_copy: 'ER copy', er_strong: 'ER strong entity',
  er_dependent: 'ER dependent', er_associative: 'ER associative', er_control: 'ER control', er_fact: 'ER fact', er_versioned: 'ER versioned',
  er_projection: 'ER projection', er_trail: 'ER audit trail', er_domain_bg: 'ER domain background', er_config: 'ER configuration',
  er_reference: 'ER reference', er_view: 'ER view', er_heat: 'Matrix heat',
};
const GROUP_LABELS = { colors: 'Colors', derived: 'Derived colors', er_palette: 'Data diagram palette' };
const ROLE_LABELS = { fill: 'Fill', line: 'Line', text: 'Text' };
const keyOf = cssName => cssName.replaceAll('-', '_');
const groupOf = key => Object.keys(GROUPS).find(group => GROUPS[group].includes(key));
const HEX = /^#[\da-f]{6}$/i;

function TokenRow({ token, group, value, selected, roles, count, onChange, onShow }) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  return <div className={`token-row${selected ? ' is-selected' : ''}${count === 0 ? ' is-unused' : ''}`} data-token={token} data-group={group}>
    <input className="token-swatch" type="color" value={value.toLowerCase()} aria-label={`${t(TOKEN_LABELS[token])} ${t("color")}`} onChange={event => onChange(token, event.target.value.toUpperCase())} />
    <div className="token-name"><span>{t(TOKEN_LABELS[token])}</span><code>--{token.replaceAll('_', '-')}</code>{roles?.length > 0 && <span className="token-roles">{roles.map(role => <em key={role}>{t(ROLE_LABELS[role])}</em>)}</span>}</div>
    <input className="token-hex" aria-label={`${t(TOKEN_LABELS[token])} hex`} value={draft} spellCheck={false} maxLength={7}
      onChange={event => { const next = event.target.value.trim(); setDraft(next); if (HEX.test(next)) onChange(token, next.toUpperCase()); }}
      onBlur={() => setDraft(value)} />
    <button type="button" className="token-show" onClick={() => onShow(token)} disabled={!count} title={count ? t("Show in the diagram") : t("Not used in this diagram")} aria-label={`${t("Show in the diagram")}: ${t(TOKEN_LABELS[token])}`}>{count ? count : '·'}</button>
  </div>;
}

function ThemesPage() {
  const [preset, setPreset] = useState('ai-diagrams');
  const [theme, setTheme] = useState(siteData.themes['ai-diagrams']);
  const [diagram, setDiagram] = useState('c4');
  const [zoom, setZoom] = useState(1);
  const [selection, setSelection] = useState(null);
  const [focus, setFocus] = useState(null);
  const [counts, setCounts] = useState({});
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const frame = useRef(null);
  const panel = useRef(null);
  const fileInput = useRef(null);
  const focusFrom = useRef('canvas');
  const onMessage = useCallback(data => {
    if (data?.type === 'ai-diagrams:pick') {
      focusFrom.current = 'canvas';
      setSelection(data);
      const first = data.uses.find(use => use.role === 'fill') || data.uses[0];
      setFocus(first ? keyOf(first.token) : null);
    } else if (data?.type === 'ai-diagrams:scan') setCounts(Object.fromEntries(Object.entries(data.counts).map(([k, v]) => [keyOf(k), v])));
  }, []);
  // ask which tokens the drawing uses once it is loaded (and after each diagram change)
  useEffect(() => {
    setSelection(null); setFocus(null); setCounts({});
    const timer = setInterval(() => { if (frame.current?.loaded) { frame.current.post({ type: 'ai-diagrams:scan' }); clearInterval(timer); } }, 150);
    return () => clearInterval(timer);
  }, [diagram]);
  useEffect(() => {
    if (!focus || !panel.current) return;
    const row = panel.current.querySelector(`[data-token="${focus}"]`);
    if (!row) return;
    row.closest('details')?.setAttribute('open', '');
    // the panel scrolls on its own beside the canvas (desktop); below it (phone) the page only moves when asked from the chips
    const own = getComputedStyle(panel.current).overflowY === 'auto' && panel.current.scrollHeight > panel.current.clientHeight;
    if (own) panel.current.scrollTo({ top: row.offsetTop - panel.current.clientHeight / 3, behavior: 'smooth' });
    else if (focusFrom.current === 'chip') row.scrollIntoView({ block: 'center', behavior: 'smooth' });
    row.querySelector('.token-swatch')?.focus({ preventScroll: true });
  }, [focus, selection]);
  const setColor = (key, value) => { const group = groupOf(key); setTheme(current => ({ ...current, [group]: { ...current[group], [key]: value } })); };
  const show = key => { focusFrom.current = 'row'; setFocus(key); frame.current?.post({ type: 'ai-diagrams:highlight', token: key.replaceAll('_', '-') }); };
  const loadPreset = name => { setPreset(name); setTheme(structuredClone(siteData.themes[name])); setError(''); };
  const importFile = async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    try { setTheme(validate(JSON.parse(await file.text()))); setPreset('custom'); setError(''); }
    catch (problem) { setError(String(problem.message || problem)); }
    event.target.value = '';
  };
  const exported = exportTheme(theme);
  const slug = (theme.name || 'my-theme').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-|-$/g, '') || 'my-theme';
  const command = `python3 <skill>/scripts/build.py diagrams/_src/<diagram>.html --theme diagrams/_src/${slug}.json`;
  const rolesOf = key => selection?.uses.filter(use => keyOf(use.token) === key).map(use => use.role) || [];
  const groupHasUse = group => GROUPS[group].some(key => counts[key]);
  return <><PageIntro eyebrow={t("Themes / Editor")} title={t("Click a shape. Change its color.")}>{t("Pick a diagram and click any box, line or label: the panel jumps to the color token it uses. Every change repaints the drawing, and the file you export is the theme the engine reads.")}</PageIntro>
    <div className="studio-bar">
      <Select label={t("Start from")} block={false} value={preset} onChange={event => loadPreset(event.target.value)}>{themeOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}{preset === 'custom' && <option value="custom">{t("Imported file")}</option>}</Select>
      <Input label={t("Theme name")} value={theme.name} onChange={event => setTheme({ ...theme, name: event.target.value })} />
      <div className="studio-actions">
        <input ref={fileInput} type="file" accept="application/json,.json" hidden onChange={importFile} />
        <Button variant="secondary" onClick={() => fileInput.current?.click()}>{t("Open theme.json")}</Button>
        <Button variant="primary" onClick={() => download(`${slug}.json`, `${JSON.stringify(exported, null, 2)}\n`)}>{t("Export theme ↓")}</Button>
      </div>
      {error && <p className="studio-error" role="alert">{error}</p>}
    </div>
    <div className="studio">
      <section className="studio-canvas" aria-label={t("Diagram canvas")}>
        <div className="studio-types" role="tablist" aria-label={t("Choose a diagram")}>{content.types.map(type => <button key={type.id} type="button" role="tab" aria-selected={diagram === type.id} className={diagram === type.id ? 'is-active' : ''} onClick={() => setDiagram(type.id)}>{type.name}</button>)}</div>
        <div className="canvas-toolbar">
          <div className="zoom-controls" role="group" aria-label={t("Zoom")}><button type="button" onClick={() => setZoom(z => Math.max(1, +(z - 0.5).toFixed(1)))} aria-label={t("Zoom out")} disabled={zoom <= 1}>−</button><span className="mono">{Math.round(zoom * 100)}%</span><button type="button" onClick={() => setZoom(z => Math.min(4, +(z + 0.5).toFixed(1)))} aria-label={t("Zoom in")} disabled={zoom >= 4}>+</button><button type="button" onClick={() => setZoom(1)} disabled={zoom === 1}>{t("Fit")}</button></div>
          <span className="small muted">{t("Click a shape to select it.")}</span>
        </div>
        <div className="canvas-scroll"><Preview key={diagram} id={diagram} theme={theme} inspect zoom={zoom} onMessage={onMessage} frameRef={frame} /></div>
        <div className="selection-bar" aria-live="polite">{selection ? <><span className="eyebrow">{t("Selected")}</span><strong className="selection-label">{selection.label || t("element")}</strong><span className="selection-uses">{selection.uses.length ? selection.uses.map(use => { const key = keyOf(use.token); const group = groupOf(key); return <button type="button" key={use.token + use.role} className={focus === key ? 'is-active' : ''} onClick={() => { focusFrom.current = 'chip'; setFocus(key); }}><i style={{ background: theme[group]?.[key] }} />{t(ROLE_LABELS[use.role])}: {t(TOKEN_LABELS[key] || key)}</button>; }) : <span className="small muted">{t("This element uses no theme color.")}</span>}</span></> : <span className="small muted">{t("Nothing selected yet. Tokens used by this diagram show a count in the panel; click the count to outline every element that uses it.")}</span>}</div>
      </section>
      <aside className="studio-panel" ref={panel} aria-label={t("Theme tokens")}>
        {Object.keys(GROUPS).map(group => <details key={`${diagram}-${group}`} open={group === 'colors' || groupHasUse(group)}><summary>{t(GROUP_LABELS[group])}<span className="small muted">{GROUPS[group].filter(key => counts[key]).length}/{GROUPS[group].length} {t("in this diagram")}</span></summary>
          {GROUPS[group].map(key => <TokenRow key={key} token={key} group={group} value={theme[group][key]} selected={focus === key} roles={rolesOf(key)} count={counts[key] || 0} onChange={setColor} onShow={show} />)}
        </details>)}
        <details open><summary>{t("Fonts")}</summary><div className="font-fields">{[['text', t("Text"), ['IBM Plex Sans', 'Public Sans', 'Inter']], ['mono', t("Code and labels"), ['IBM Plex Mono', 'Source Code Pro', 'JetBrains Mono']]].map(([key, label, fonts]) => <Select key={key} label={label} value={theme.fonts[key]} onChange={event => setTheme({ ...theme, fonts: { ...theme.fonts, [key]: event.target.value } })}>{fonts.map(font => <option key={font}>{font}</option>)}</Select>)}</div></details>
      </aside>
    </div>
    <section className="section contrast-section"><SectionHeader title={t("Measured text contrast")} sub={t("Actual ratios from the edited palette. Normal text needs at least 4.5:1.")} /><div className="contrast-grid">{contrastPairs(theme).map(pair => <div key={pair.label}><span className="contrast-sample" style={{ color: pair.foreground, background: pair.background }}>Aa</span><span>{t(pair.label)}<small>{pair.foreground} / {pair.background}</small></span><strong className={pair.ratio >= 4.5 ? 'is-pass' : 'is-fail'}><StateIcon state={pair.ratio >= 4.5 ? 'pass' : 'fail'} />{pair.ratio.toFixed(2)}:1</strong></div>)}</div></section>
    <section className="section"><SectionHeader title={t("Take it back to the skill")} sub={t("Save the file in your project and pass it to every command, or ask the agent to use it. The engine reads exactly this file.")} />
      <Code code={command} label={t("Build with this theme")} />
      <Code code={JSON.stringify(exported, null, 2)} label={`${slug}.json`} language="json" /></section>
  </>;
}

const colorNames = { Ciano: t("Cyan"), Coral: t("Coral"), Amarelo: t("Yellow"), Violeta: t("Violet") };

function BrandPage() {
  return <><PageIntro eyebrow={t("The ai-diagrams brand")} title={<>{t("Documents")}<br />{t("come to life.")}</>} action={<Button onClick={() => download('logo-solid.svg', siteData.assets['logo-solid.svg'])}>{t("Download the signature ↓")}</Button>}>{t("Ideas, systems and processes find a shape. A neutral interface gives the drawing room to speak.")}</PageIntro>
    <nav className="section-links" aria-label={t("Brand sections")}>{[['signature', t("01 Signature")], ['palette', t("02 Color & type")], ['voice', t("03 Voice")], ['applications', t("04 Applications")]].map(([id, label]) => <a href={`#${id}`} key={id}>{t(label)}</a>)}</nav>
    <Card padding="none" className="brand-board"><section className="brand-section" id="signature"><SectionHeader title={t("01 Signature")} sub={t("Encontro. A D with an A inside.")} /><div className="brand-signature"><div className="symbol-stage"><img src={siteData.assets['symbol-solid.svg']} alt={t("Encontro: cyan stem, coral circle and an upright yellow triangle")} width="200" height="200" /></div><div><h3>{t("Different shapes. One meeting point.")}</h3><p>{t("The stem and the circle form a D. The equilateral triangle points up like an A. Yellow stays solid on top; only cyan and coral overlap in multiply.")}</p><div className="symbol-sizes">{[16, 32, 64].map(size => <figure key={size}><img src={siteData.assets['symbol-solid.svg']} width={size} height={size} alt={`${t('Symbol')} · ${size} px`} /><figcaption>{size} px</figcaption></figure>)}</div><p className="small muted">{t("Keep clear space equal to ¼ of the symbol width. Minimum: 16 px for the symbol, 160 px for the signature. Always write ai-diagrams in lowercase.")}</p></div></div><div className="signature-pair">{[['logo-solid.svg', t("Primary signature"), 'paper'], ['logo-solid-reverse.svg', t("On a dark background"), 'ink']].map(([file, label, theme]) => <figure className={`signature-specimen ${theme}`} key={file}><img src={siteData.assets[file]} alt={t(label)} /><figcaption>{t(label)}</figcaption></figure>)}</div><div className="actions"><Button onClick={() => download('logo-solid.svg', siteData.assets['logo-solid.svg'])}>{t("Signature SVG ↓")}</Button><Button variant="secondary" onClick={() => download('symbol-solid.svg', siteData.assets['symbol-solid.svg'])}>{t("Symbol SVG ↓")}</Button><Button variant="ghost" onClick={() => download('logo-mono-dark.svg', siteData.assets['logo-mono-dark.svg'])}>{t("Monochrome SVG ↓")}</Button></div></section>
      <section className="brand-section" id="palette"><SectionHeader title={t("02 Color & typography")} sub={t("Color belongs to the drawing. Controls stay neutral.")} /><div className="brand-color-layout"><div><div className="brand-swatches">{siteData.palette.colors.map(color => <figure key={color.name}><div style={{ background: color.hex, color: color.foreground }}>Aa</div><figcaption>{t(colorNames[color.name])}<code>{color.hex}</code><small>{color.contrast.toFixed(2)}:1</small></figcaption></figure>)}</div><h3>{t("Where the colors meet")}</h3><div className="multiply-swatches">{siteData.palette.pairs.map(pair => <figure key={pair.hex}><div style={{ background: pair.hex, color: pair.foreground }}>Aa <code>{pair.hex}</code></div><figcaption>{pair.names.map(name => t(colorNames[name])).join(' + ')}<small>{pair.contrast.toFixed(2)}:1</small></figcaption></figure>)}</div></div><div className="type-specimens"><p className="eyebrow">Inter / 400 · 500 · 600 · 700</p><p className="type-display">{t("Suddenly,")}<br />{t("it all connects.")}</p><p>{t("Titles, body text and the signature.")}</p><div className="mono-specimen"><p className="eyebrow">JetBrains Mono / 400 · 600</p><p className="type-display">01 → 02 → 03</p><p>{t("Labels, measurements and code.")}</p></div></div></div></section>
      <section className="brand-section" id="voice"><SectionHeader title={t("03 Voice")} sub={t("Lively. Clear. Grounded.")} /><div className="voice-grid"><p>{t("Use short sentences and concrete verbs. Explain the next step. Be curious about the drawing, precise about what was checked.")}</p><div><p>{t("“The diagram is ready. See how the parts connect.”")}</p><p>{t("“Two boxes overlap. Let's make room between them.”")}</p><p className="small muted">{t("Geometry checks help with the drawing. Content still needs a human review.")}</p></div></div></section>
      <section className="brand-section" id="applications"><SectionHeader title={t("04 Applications")} sub={t("From the browser tab to the complete drawing.")} /><div className="brand-applications"><figure><img src={siteData.assets['exemplo-diagrama.svg']} alt={t("Brand diagram using the four colors and numbered connections")} /><figcaption>{t("Identity study with the brand palette.")}</figcaption></figure><div><p className="eyebrow">{t("Favicon / actual size")}</p><div className="symbol-sizes">{[16, 32, 64].map(size => <figure key={size}><img src={siteData.assets[`favicon-${size}.png`]} width={size} height={size} alt={`Favicon · ${size} px`} /><figcaption>{size} px</figcaption></figure>)}</div><Button variant="secondary" onClick={() => download('favicon.svg', siteData.assets['favicon.svg'])}>{t("Favicon SVG ↓")}</Button><p className="small muted">{t("The same Encontro geometry, from the smallest icon to the full signature.")}</p></div></div></section>
    </Card></>;
}

function IndexPage() {
  return <><PageIntro eyebrow={t("ai-diagrams / design review")} title={t("Seven boards. One direction.")}>{t("Static mockups for approval before the real site is built. Open each board to review content, layout and local interactions.")}</PageIntro><div className="board-index">{pages.map(([id, file, label], index) => <NavCard key={id} href={file} title={t(label)} description={id === 'home' ? '1440 px + 390 px' : '1440 px'} leading={<span className="mono muted">{String(index + 1).padStart(2, '0')}</span>} />)}</div><p className="small muted index-note">{t("Pages share one stylesheet, one script per language and the fonts in assets/. Each diagram is its own HTML in diagrams/. Use Light / Dark to compare appearances.")}</p></>;
}

export function App({ page = 'home' }) {
  const [mode, setMode] = useState('light');
  useEffect(() => { if (new URLSearchParams(location.search).get('theme') === 'dark') setMode('dark'); }, []);
  const views = { home: Home, catalog: Catalog, aws: AwsPage, themes: ThemesPage, compatibility: CompatibilityPage, brand: BrandPage, import: ImportPage, index: IndexPage };
  const View = views[page];
  return <div className="site" data-theme={mode} data-page={page}><a className="skip-link" href="#main">{t("Skip to content")}</a><Header page={page} mode={mode} setMode={setMode} /><main id="main" className={`content page-${page}`}><View /><Footer page={page} /></main></div>;
}
