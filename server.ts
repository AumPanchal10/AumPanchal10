import express from "express";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = __dirname.endsWith(`${path.sep}dist`)
  ? path.resolve(__dirname, "..")
  : __dirname;

const PORT = Number(process.env.PORT) || 3000;
const HOST = "0.0.0.0";

const app = express();

app.use("/assets", express.static(path.join(ROOT_DIR, "assets")));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true });
});

app.get("/api/config", (_req, res) => {
  const configDir = path.join(ROOT_DIR, "config");
  if (!fs.existsSync(configDir)) {
    res.json({});
    return;
  }
  const result: Record<string, unknown> = {};
  for (const file of fs.readdirSync(configDir).sort()) {
    if (!file.endsWith(".json")) continue;
    try {
      const raw = fs.readFileSync(path.join(configDir, file), "utf-8");
      result[file] = JSON.parse(raw);
    } catch {
      result[file] = { error: "Invalid JSON" };
    }
  }
  res.json(result);
});

function escapeHtml(str: string): string {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderMarkdownPage(): string {
  const readmePath = path.join(ROOT_DIR, "README.md");
  const markdown = fs.existsSync(readmePath)
    ? fs.readFileSync(readmePath, "utf-8")
    : "# README.md not found";

  const renderedBody = marked.parse(markdown, {
    gfm: true,
    breaks: false,
  }) as string;

  const configDir = path.join(ROOT_DIR, "config");
  const configFiles = fs.existsSync(configDir)
    ? fs.readdirSync(configDir).filter((f) => f.endsWith(".json")).sort()
    : [];

  const configSections = configFiles
    .map((file) => {
      const content = fs.readFileSync(path.join(configDir, file), "utf-8");
      return `
        <details class="config-card">
          <summary><code>config/${escapeHtml(file)}</code></summary>
          <pre><code>${escapeHtml(content)}</code></pre>
        </details>
      `;
    })
    .join("\n");

  return `<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aum Panchal — GitHub Profile 3.0 Preview</title>
  <meta name="description" content="GitHub Profile 3.0 preview for Aum Panchal (AumPanchal10)" />
  <meta property="og:title" content="Aum Panchal — GitHub Profile 3.0" />
  <meta property="og:description" content="Configuration-driven GitHub Profile repository preview" />
  <style>
    :root[data-theme="dark"] {
      --bg: #0b0f14;
      --surface: #11161d;
      --surface-elevated: #161c24;
      --border: #262e39;
      --text: #e8edf3;
      --muted: #939ead;
      --accent: #84cc16;
      --link: #84cc16;
      --code-bg: #161c24;
    }
    :root[data-theme="light"] {
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-elevated: #f1f5f9;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #475569;
      --accent: #4d7c0f;
      --link: #3f6212;
      --code-bg: #f1f5f9;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 15px;
      line-height: 1.7;
      letter-spacing: -0.006em;
      -webkit-font-smoothing: antialiased;
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 14px;
      letter-spacing: -0.01em;
    }
    .brand-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent);
    }
    .actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .btn {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 6px 14px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
    }
    .btn:hover {
      color: var(--text);
      border-color: var(--muted);
    }
    .btn.active {
      background: var(--surface-elevated);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }
    .container {
      max-width: 900px;
      margin: 32px auto 72px;
      padding: 0 20px;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 40px 44px;
    }
    @media (max-width: 640px) {
      .card { padding: 24px 20px; }
    }
    .markdown-body img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
    }
    .markdown-body a {
      color: var(--link);
      text-decoration: none;
      font-weight: 500;
    }
    .markdown-body a:hover { text-decoration: underline; }
    .markdown-body h1, .markdown-body h2 {
      font-size: 21px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text);
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
      margin-top: 32px;
      margin-bottom: 16px;
    }
    .markdown-body h3 {
      font-size: 16px;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: var(--text);
      margin-top: 24px;
      margin-bottom: 6px;
    }
    .markdown-body p {
      margin: 0 0 14px;
      color: var(--text);
    }
    .markdown-body ul {
      padding-left: 20px;
      margin: 8px 0 16px;
    }
    .markdown-body li {
      margin-bottom: 6px;
    }
    .markdown-body blockquote {
      margin: 12px 0 18px;
      padding: 10px 16px;
      color: var(--muted);
      background: var(--surface-elevated);
      border-left: 3px solid var(--accent);
      border-radius: 0 8px 8px 0;
    }
    .markdown-body blockquote p {
      margin: 0;
      color: var(--text);
    }
    .markdown-body pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 18px;
      overflow-x: auto;
      font-size: 13.5px;
    }
    .markdown-body code {
      background: var(--code-bg);
      padding: 2px 7px;
      border-radius: 5px;
      font-size: 13px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .markdown-body pre code { background: transparent; padding: 0; }
    .markdown-body table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 16px 0 22px;
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      font-size: 14px;
    }
    .markdown-body th, .markdown-body td {
      padding: 11px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .markdown-body tr:last-child td { border-bottom: none; }
    .markdown-body th {
      background: var(--surface-elevated);
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .markdown-body td:first-child {
      white-space: nowrap;
      width: 220px;
    }
    .markdown-body details {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 12px;
      background: var(--surface-elevated);
      transition: border-color 0.15s ease;
    }
    .markdown-body details[open] {
      padding-bottom: 16px;
    }
    .markdown-body details:hover {
      border-color: var(--muted);
    }
    .markdown-body summary {
      cursor: pointer;
      list-style-position: inside;
      font-size: 15px;
      color: var(--text);
    }
    .markdown-body details > *:nth-child(2) {
      margin-top: 14px;
    }
    .config-card {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 16px;
      margin-bottom: 12px;
      background: var(--surface-elevated);
    }
    .config-card pre {
      margin-top: 12px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      overflow-x: auto;
      font-size: 12.5px;
    }
    .hidden { display: none; }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <span class="brand-dot"></span>
      <span>AumPanchal10 / README.md</span>
    </div>
    <div class="actions">
      <button id="tab-preview" class="btn active" type="button">README Preview</button>
      <button id="tab-config" class="btn" type="button">Config JSON</button>
      <button id="theme-toggle" class="btn" type="button">Light Mode</button>
    </div>
  </header>
  <main class="container">
    <article id="view-preview" class="card markdown-body">
      ${renderedBody}
    </article>
    <section id="view-config" class="card hidden">
      <h2 style="margin-top:0">Profile Configuration Files</h2>
      <p style="color:var(--muted)">Edit JSON files under <code>config/</code> and run <code>python3 scripts/generate_readme.py</code> to regenerate <code>README.md</code>.</p>
      ${configSections}
    </section>
  </main>
  <script>
    const root = document.documentElement;
    const themeBtn = document.getElementById('theme-toggle');
    const tabPreview = document.getElementById('tab-preview');
    const tabConfig = document.getElementById('tab-config');
    const viewPreview = document.getElementById('view-preview');
    const viewConfig = document.getElementById('view-config');

    themeBtn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      themeBtn.textContent = next === 'dark' ? 'Light Mode' : 'Dark Mode';
    });

    tabPreview.addEventListener('click', () => {
      tabPreview.classList.add('active');
      tabConfig.classList.remove('active');
      viewPreview.classList.remove('hidden');
      viewConfig.classList.add('hidden');
    });

    tabConfig.addEventListener('click', () => {
      tabConfig.classList.add('active');
      tabPreview.classList.remove('active');
      viewConfig.classList.remove('hidden');
      viewPreview.classList.add('hidden');
    });
  </script>
</body>
</html>`;
}

app.get("/", (_req, res) => {
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.send(renderMarkdownPage());
});

app.listen(PORT, HOST, () => {
  console.log(`GitHub Profile preview running at http://${HOST}:${PORT}`);
});
