const form = document.querySelector("#generate-form");
const button = document.querySelector("#submit-button");
const result = document.querySelector(".result");
const errorMessage = document.querySelector("#form-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  result.setAttribute("aria-busy", "true");
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Researching and writing...";

  const values = new FormData(form);
  const payload = Object.fromEntries(values.entries());
  payload.word_count = Number(payload.word_count);

  try {
    const response = await fetch("/api/v1/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Generation failed. Please try again.");
    renderArticle(data);
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    result.setAttribute("aria-busy", "false");
    button.disabled = false;
    button.querySelector("span:first-child").textContent = "Generate article";
  }
});

function renderArticle(data) {
  document.querySelector("#empty-state").hidden = true;
  const article = document.querySelector("#article");
  article.hidden = false;
  document.querySelector("#article-topic").textContent = data.topic;
  document.querySelector("#article-title").textContent = data.title;
  const stats = [`${data.metadata.word_count ?? 0} words`, `${data.metadata.estimated_reading_time ?? 1} min read`];
  if (data.quality_score !== null) stats.push(`Quality ${Math.round(data.quality_score * 100)}%`);
  document.querySelector("#article-stats").textContent = stats.join("  /  ");
  const content = document.querySelector("#article-content");
  content.replaceChildren(...data.content.split(/\n\s*\n/).filter(Boolean).map((paragraph) => {
    const node = document.createElement("p");
    node.textContent = paragraph;
    return node;
  }));

  const list = document.querySelector("#source-list");
  list.replaceChildren(...(data.sources || []).map((source) => {
    const item = document.createElement("li");
    let sourceUrl;
    try {
      sourceUrl = new URL(source.url);
    } catch {
      sourceUrl = null;
    }
    if (sourceUrl && ["http:", "https:"].includes(sourceUrl.protocol)) {
      const link = document.createElement("a");
      link.textContent = source.title || source.url;
      link.href = sourceUrl.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      item.append(link);
    } else {
      item.textContent = source.title || "Source";
    }
    if (source.snippet) item.append(document.createTextNode(`: ${source.snippet}`));
    return item;
  }));
  document.querySelector("#source-section").hidden = !data.sources?.length;
  article.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#copy-button").addEventListener("click", async () => {
  const title = document.querySelector("#article-title").textContent;
  const content = [...document.querySelectorAll("#article-content p")].map((paragraph) => paragraph.textContent).join("\n\n");
  await navigator.clipboard.writeText(`# ${title}\n\n${content}`);
  const buttonLabel = document.querySelector("#copy-button");
  buttonLabel.title = "Copied";
  window.setTimeout(() => { buttonLabel.title = "Copy article"; }, 1500);
});
