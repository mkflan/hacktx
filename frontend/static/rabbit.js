/* Shared browser helpers: escaping, a small safe markdown renderer, and the plan renderer.
   Only http(s) links survive rendering; the server has already removed URLs that were not
   among the supplied sources. */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function inline(text) {
  // text is already escaped. Bold, inline code, and [title](https://...) links.
  return text
    .replace(/\*\*([^*]+)\*\*/g, "<strong class='text-cream'>$1</strong>")
    .replace(/`([^`]+)`/g, "<code class='bg-panel-2 px-1 rounded text-[11px]'>$1</code>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, "<a href='$2' target='_blank' rel='noopener' class='text-gold underline underline-offset-2'>$1</a>")
    .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, "$1<a href='$2' target='_blank' rel='noopener' class='text-gold underline underline-offset-2'>$2</a>");
}

function renderMarkdown(md) {
  const lines = esc(md).split(/\r?\n/);
  let html = "", list = null;
  const closeList = () => { if (list) { html += `</${list}>`; list = null; } };
  for (const raw of lines) {
    const line = raw.trim();
    let m;
    if ((m = line.match(/^[-*]\s+(.*)/))) {
      if (list !== "ul") { closeList(); html += "<ul class='list-disc pl-5 space-y-1'>"; list = "ul"; }
      html += `<li>${inline(m[1])}</li>`;
    } else if ((m = line.match(/^\d+[.)]\s+(.*)/))) {
      if (list !== "ol") { closeList(); html += "<ol class='list-decimal pl-5 space-y-1'>"; list = "ol"; }
      html += `<li>${inline(m[1])}</li>`;
    } else if ((m = line.match(/^#{1,6}\s+(.*)/))) {
      closeList(); html += `<p class='text-gold uppercase text-xs tracking-wider mt-2'>${inline(m[1])}</p>`;
    } else if (line === "") {
      closeList();
    } else {
      closeList(); html += `<p>${inline(line)}</p>`;
    }
  }
  closeList();
  return html;
}

function list(items, f) {
  return items && items.length ? "<ul class='list-disc pl-5 space-y-1'>" + items.map(f).join("") + "</ul>" : "<p class='text-gray-500'>none</p>";
}

function renderSources(items, note) {
  if (!items || !items.length) return "";
  return `<div class="mt-3 border-t border-moss pt-3">
    ${note ? `<p class="text-[10px] text-gray-500 mb-2">${esc(note)}</p>` : ""}
    <div class="grid gap-2">${items.map((r) => `
      <a href="${esc(r.url)}" target="_blank" rel="noopener" class="flex gap-3 text-xs text-gray-200 hover:text-gold">
        ${r.thumbnail_url ? `<img src="${esc(r.thumbnail_url)}" alt="" class="w-20 h-12 object-cover rounded border border-moss shrink-0">` : ""}
        <span>${esc(r.title)}<span class="block text-[10px] text-gray-500">${esc(r.kind)} · ${esc(r.provider || "")}${r.metadata && r.metadata.channel ? " · " + esc(r.metadata.channel) : ""}${r.source && r.source !== "authored" ? " · found via " + esc(r.source.replace("serpapi:", "SerpApi ")) : ""}</span></span>
      </a>`).join("")}</div></div>`;
}

function renderPlan(p, meta) {
  const sources = [...(p.resources || []), ...(p.research_connections || []), ...(p.similar_examples || [])];
  const seen = new Set(); const unique = sources.filter((r) => !seen.has(r.id) && seen.add(r.id));
  return `
    <article class="bg-panel border-2 border-gold rounded-md p-6 font-magical text-sm text-gray-200 space-y-4">
      <div class="flex items-start justify-between gap-3">
        <h2 class="font-mystical text-sm md:text-base text-gold uppercase tracking-wider font-bold">${esc(p.name)}</h2>
        <span class="text-[10px] text-gray-500 whitespace-nowrap">${esc(meta.generation_mode || "")} · ${p.estimated_total_hours} h${p.difficulty ? " · " + esc(p.difficulty) : ""}</span>
      </div>
      <p>${esc(p.summary)}</p>
      <p><span class="text-gold">Deliverable:</span> ${esc(p.deliverable)}</p>
      <p><span class="text-gold">First action:</span> ${esc(p.first_action)}</p>
      <div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Milestones</h3>
        <ol class="list-decimal pl-5 space-y-2">${(p.milestones || []).map((m) => `<li><span class="text-cream font-semibold">${esc(m.title)}</span> <span class="text-gray-500">(${m.estimated_hours} h)</span><br>${esc(m.objective)}</li>`).join("")}</ol></div>
      <div class="grid md:grid-cols-2 gap-4">
        <div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Materials</h3>${list(p.materials, (m) => `<li>${esc(m.name)}${m.estimated_cost_usd != null ? ` <span class='text-gray-500'>~$${m.estimated_cost_usd}</span>` : ""}</li>`)}</div>
        <div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Software</h3>${list(p.software, (m) => `<li>${esc(m.name)}</li>`)}</div>
      </div>
      <div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Schedule</h3>
        <p class="text-xs text-gray-400">${(p.suggested_schedule || []).map((s) => `Week ${s.week}: ${esc(s.focus)} (${s.hours} h)`).join(" · ")}</p></div>
      <div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Customize it</h3>${list(p.customization_ideas, (c) => `<li>${esc(c)}</li>`)}</div>
      ${unique.length ? `<div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Sources</h3>${renderSources(unique)}</div>` : ""}
      ${(p.suggested_search_queries || []).length && !unique.length ? `<p class="text-xs text-gray-500">No supplied source fit. Searches to try: ${p.suggested_search_queries.map(esc).join("; ")}</p>` : ""}
      ${(p.scope_adjustments || []).length ? `<div><h3 class="text-gold uppercase text-xs tracking-wider mb-1">Scope changes for your time</h3>${list(p.scope_adjustments, (s) => `<li>${esc(s)}</li>`)}</div>` : ""}
      <details class="text-xs text-gray-500"><summary class="cursor-pointer">Assumptions and notes</summary>
        ${list(p.assumptions, (a) => `<li>${esc(a)}</li>`)}${list((meta.warnings || []).map((w) => w.message), (w) => `<li>${esc(w)}</li>`)}</details>
    </article>`;
}
