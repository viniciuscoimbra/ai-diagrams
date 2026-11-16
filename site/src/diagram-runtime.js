// Runs inside each diagram page of the site (an iframe). It talks to the page only through postMessage:
//   in:  {type: 'ai-diagrams:theme', css, tokens}  replaces the theme :root (tokens: [[name, value], ...])
//        {type: 'ai-diagrams:inspect', on, scale}  turns element picking on or off (scale: how the page shows this frame)
//        {type: 'ai-diagrams:clear'}               removes the selection outline and highlights
//        {type: 'ai-diagrams:scan'}                asks which tokens the drawing uses
//        {type: 'ai-diagrams:highlight', token}    outlines every element painted with the token
//   out: {type: 'ai-diagrams-size', height}
//        {type: 'ai-diagrams:pick', uses: [{token, role}], label}
//        {type: 'ai-diagrams:scan', counts: {token: elements}}
//        {type: 'ai-diagrams:highlight', token, count}
(function () {
  var root = document.getElementById('ai-diagrams-theme');
  var tokens = window.__aiDiagramsTokens || [];
  var inspect = false;
  var scale = 1;
  var outline = null;

  function reportSize() {
    parent.postMessage({type: 'ai-diagrams-size', height: Math.ceil(document.body.scrollHeight)}, '*');
  }
  addEventListener('load', reportSize);
  addEventListener('DOMContentLoaded', function () {
    new ResizeObserver(reportSize).observe(document.body);
    document.fonts.ready.then(reportSize);
    reportSize();
  });

  // Each color token (and each -rgb channel) gets a unique color for one synchronous read, so an element's
  // computed colors name the tokens it uses even when two tokens share a value.
  function sentinels() {
    var map = {}, css = [], i = 0;
    tokens.forEach(function (pair) {
      var name = pair[0], value = pair[1];
      if (name.indexOf('font-') === 0) { css.push('--' + name + ':' + value + ';'); return; }
      var r = 13 + (i % 200), g = 7 + Math.floor(i / 200), b = 241 - (i % 200);
      i++;
      var base = name.replace(/-rgb$/, '');
      map[r + ',' + g + ',' + b] = base;
      css.push('--' + name + ':' + (/-rgb$/.test(name) ? r + ',' + g + ',' + b : 'rgb(' + r + ',' + g + ',' + b + ')') + ';');
    });
    return {map: map, css: ':root{' + css.join('') + '}'};
  }

  function colorsIn(value) {
    var out = [], re = /rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)/g, m;
    while ((m = re.exec(value || ''))) out.push(m[1] + ',' + m[2] + ',' + m[3]);
    return out;
  }

  var PROPS = [['color', 'text'], ['fill', 'fill'], ['background-color', 'fill'], ['background-image', 'fill'],
    ['stroke', 'line'], ['border-top-color', 'line'], ['border-right-color', 'line'], ['border-bottom-color', 'line'],
    ['border-left-color', 'line'], ['outline-color', 'line']];

  function usesOf(el, map, roles) {
    var cs = getComputedStyle(el), found = [];
    PROPS.forEach(function (p) {
      if (roles && roles.indexOf(p[1]) < 0) return;
      if (/^border/.test(p[0]) && parseFloat(cs[p[0].replace('color', 'width')]) === 0) return;
      if (p[0] === 'outline-color' && (cs.outlineStyle === 'none' || parseFloat(cs.outlineWidth) === 0)) return;
      colorsIn(cs.getPropertyValue(p[0])).forEach(function (key) {
        if (map[key]) found.push({token: map[key], role: p[1]});
      });
    });
    return found;
  }

  function pick(target) {
    if (window.__aiDiagramsBpmnPick) return window.__aiDiagramsBpmnPick(target);
    var saved = root.textContent, s = sentinels(), uses = [], box = null;
    root.textContent = s.css;
    try {
      uses = usesOf(target, s.map);
      // the box around the clicked text or shape: the element itself when it has a fill or line, else the nearest ancestor that does
      if (usesOf(target, s.map, ['fill', 'line']).length) box = target;
      for (var el = target.parentElement; !box && el && el !== document.body; el = el.parentElement) {
        var own = usesOf(el, s.map, ['fill', 'line']);
        if (own.length) { uses = uses.concat(own); box = el; break; }
      }
    } finally {
      root.textContent = saved;
    }
    var seen = {};
    uses = uses.filter(function (u) { var k = u.token + u.role; if (seen[k]) return false; seen[k] = 1; return true; });
    return {uses: uses, element: box || target};
  }

  function drawOutline(el) {
    if (!outline) {
      outline = document.createElement('div');
      outline.setAttribute('data-ai-diagrams-ui', '');
      outline.style.cssText = 'position:absolute;pointer-events:none;z-index:2147483647;outline:3px solid #2563EB;outline-offset:2px;border-radius:2px;box-shadow:0 0 0 6px rgba(37,99,235,.18)';
      document.body.appendChild(outline);
    }
    var r = el.getBoundingClientRect();
    outline.style.left = (r.left + scrollX) + 'px';
    outline.style.top = (r.top + scrollY) + 'px';
    outline.style.width = r.width + 'px';
    outline.style.height = r.height + 'px';
    outline.style.display = 'block';
  }

  // every element of the drawing and the tokens it paints with, read in one sentinel pass
  function scan() {
    if (window.__aiDiagramsBpmnScan) return window.__aiDiagramsBpmnScan();
    var saved = root.textContent, s = sentinels(), list = [];
    root.textContent = s.css;
    try {
      document.querySelectorAll('body *').forEach(function (el) {
        if (el.hasAttribute('data-ai-diagrams-ui') || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
        var r = el.getBoundingClientRect();
        // a straight line has no width or no height, but it is drawn
        if (r.width < 1 && r.height < 1) return;
        var uses = usesOf(el, s.map);
        if (uses.length) list.push({element: el, uses: uses});
      });
    } finally {
      root.textContent = saved;
    }
    return list;
  }

  var marks = [];
  function highlight(token) {
    marks.forEach(function (m) { m.remove(); });
    marks = [];
    if (!token) return 0;
    scan().forEach(function (item) {
      if (!item.uses.some(function (u) { return u.token === token; }) || marks.length > 300) return;
      var r = item.element.getBoundingClientRect(), m = document.createElement('div');
      m.setAttribute('data-ai-diagrams-ui', '');
      m.style.cssText = 'position:absolute;pointer-events:none;z-index:2147483646;outline:2px dashed #2563EB;outline-offset:1px;left:' +
        (r.left + scrollX) + 'px;top:' + (r.top + scrollY) + 'px;width:' + r.width + 'px;height:' + r.height + 'px';
      document.body.appendChild(m);
      marks.push(m);
    });
    return marks.length;
  }

  // A line (an arrow, a BPMN flow) is as far from the tap as its stroke, not as its bounding box, which for an
  // elbow covers the empty area inside the elbow.
  function line(el) {
    // a BPMN flow groups its line with the filled arrowhead marker; the line is the unfilled one
    if (el.classList && el.classList.contains('djs-connection')) {
      el = [].slice.call(el.querySelectorAll('polyline, path')).filter(function (g) { return getComputedStyle(g).fill === 'none'; })[0] || el;
    }
    if (!(el instanceof SVGGeometryElement) || /^(rect|circle|ellipse)$/.test(el.tagName)) return null;
    var fill = getComputedStyle(el).fill;
    return fill && fill !== 'none' && !/rgba\(.*,\s*0\)$/.test(fill) ? null : el;
  }
  function strokeDistance(path, x, y) {
    var matrix = path.getScreenCTM(), total = path.getTotalLength(), best = Infinity;
    if (!matrix || !total) return Infinity;
    for (var at = 0; at <= total; at += Math.max(2, total / 400)) {
      var p = path.getPointAtLength(at), sx = matrix.a * p.x + matrix.c * p.y + matrix.e, sy = matrix.b * p.x + matrix.d * p.y + matrix.f;
      best = Math.min(best, Math.hypot(sx - x, sy - y));
    }
    return best;
  }

  // The smallest painted shape under the tap wins, so a small box inside a large zone is not lost to the zone.
  // A line wins when the tap is closer to its stroke than to the edge of that shape (arrows end on box edges);
  // with nothing under the tap, the nearest element within reach of a finger on the scaled-down drawing.
  function nearest(x, y, reach) {
    var box = null, boxArea = Infinity, inset = Infinity, wire = null, wireDistance = Infinity, near = null, nearDistance = Infinity;
    scan().forEach(function (item) {
      var path = line(item.element), d;
      if (path) {
        d = strokeDistance(path, x, y);
        if (d < wireDistance) { wire = item.element; wireDistance = d; }
      } else {
        var r = item.element.getBoundingClientRect();
        d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
        if (d === 0 && r.width * r.height < boxArea) {
          box = item.element; boxArea = r.width * r.height;
          inset = Math.min(x - r.left, r.right - x, y - r.top, r.bottom - y);
        }
      }
      if (d > 0 && d <= reach && d < nearDistance) { near = item.element; nearDistance = d; }
    });
    // a shape that comes after the line in the document is painted over it, like a badge on an arrow
    // (an HTML shape over an SVG line; inside one SVG, as in BPMN, the order of the groups is not the paint order of lanes and flows)
    var over = box && wire && !(box instanceof SVGElement) && !box.contains(wire) && (wire.compareDocumentPosition(box) & Node.DOCUMENT_POSITION_FOLLOWING);
    if (wire && !over && wireDistance <= Math.max(3, reach / 2) && wireDistance < inset) return wire;
    return box || near;
  }

  addEventListener('click', function (event) {
    if (!inspect) return;
    event.preventDefault();
    event.stopPropagation();
    var reach = (event.pointerType === 'mouse' ? 3 : 14) / (scale || 1);
    var result = pick(nearest(event.clientX, event.clientY, reach) || event.target);
    if (!result) return;
    drawOutline(result.element);
    var label = (result.element.textContent || result.element.getAttribute('class') || result.element.tagName || '').replace(/\s+/g, ' ').trim().slice(0, 60);
    parent.postMessage({type: 'ai-diagrams:pick', uses: result.uses, label: label}, '*');
  }, true);

  addEventListener('message', function (event) {
    var data = event.data || {};
    if (data.type === 'ai-diagrams:hello') {
      reportSize();
    } else if (data.type === 'ai-diagrams:theme') {
      tokens = data.tokens || tokens;
      root.textContent = data.css;
      if (window.__aiDiagramsRetheme) window.__aiDiagramsRetheme();
    } else if (data.type === 'ai-diagrams:inspect') {
      inspect = !!data.on;
      if (data.scale > 0) scale = data.scale;
      document.documentElement.style.cursor = inspect ? 'crosshair' : '';
      if (!inspect && outline) outline.style.display = 'none';
    } else if (data.type === 'ai-diagrams:clear') {
      if (outline) outline.style.display = 'none';
      highlight(null);
    } else if (data.type === 'ai-diagrams:scan') {
      var counts = {};
      scan().forEach(function (item) {
        var seen = {};
        item.uses.forEach(function (u) { if (!seen[u.token]) { seen[u.token] = 1; counts[u.token] = (counts[u.token] || 0) + 1; } });
      });
      parent.postMessage({type: 'ai-diagrams:scan', counts: counts}, '*');
    } else if (data.type === 'ai-diagrams:highlight') {
      if (outline) outline.style.display = 'none';
      parent.postMessage({type: 'ai-diagrams:highlight', token: data.token, count: highlight(data.token)}, '*');
    }
  });
})();
