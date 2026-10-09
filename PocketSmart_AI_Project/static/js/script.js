function showResult(data, targetId="result") {
  const el = document.getElementById(targetId);
  if (!el) return;
  if (data.error) {
    el.innerHTML = `<div class="error">${escapeHtml(data.error)}</div>`;
    return;
  }
  let html = `<h2>${escapeHtml(data.title || "Recommendations")}</h2>
              <p>${escapeHtml(data.summary || "")}</p>`;
  if (data.allocation?.length) {
    html += `<h3>Budget Allocation</h3><div class="allocation">`;
    for (const a of data.allocation) {
      html += `<div class="alloc"><b>${escapeHtml(a.category)}</b><br>₹${Number(a.amount).toLocaleString()}<br><small>${escapeHtml(a.reason)}</small></div>`;
    }
    html += `</div>`;
  }
  if (data.recommendations?.length) {
    html += `<h3>Recommendations</h3>`;
    for (const r of data.recommendations) {
      html += `<div class="recommendation">
        <span class="tag">${escapeHtml(r.platform || "AI")}</span>
        <h3>${escapeHtml(r.name || "")}</h3>
        <div class="price">₹${Number(r.price || 0).toLocaleString()}</div>
        <p>${escapeHtml(r.reason || "")}</p>
        ${r.link ? `<a class="btn" target="_blank" href="${r.link}">View/Search</a>` : ""}
      </div>`;
    }
  }
  if (data.image_analysis) html += `<p><b>Image note:</b> ${escapeHtml(data.image_analysis)}</p>`;
  if (data.image_url) html += `<img src="${data.image_url}" style="max-width:180px;border-radius:12px">`;
  el.innerHTML = html;
  el.scrollIntoView({behavior:"smooth"});
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}
