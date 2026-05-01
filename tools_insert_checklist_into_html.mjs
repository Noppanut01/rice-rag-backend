import fs from "node:fs";

const htmlPath = "/Users/noppanut/Downloads/rice_expert_system_with_code_chatgpt.html";
const checklistPath = "CODE_READING_CHECKLIST.md";
const outputPath = "rice_expert_system_with_code_chatgpt_updated.html";

const escapeHtml = (value) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

const inlineMarkdown = (value) =>
  escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");

function markdownToHtml(markdown) {
  const lines = markdown.split(/\r?\n/);
  const out = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      closeList();
      continue;
    }

    if (line.startsWith("### ")) {
      closeList();
      out.push(`<h4>${inlineMarkdown(line.slice(4))}</h4>`);
      continue;
    }
    if (line.startsWith("## ")) {
      closeList();
      out.push(`<h3>${inlineMarkdown(line.slice(3))}</h3>`);
      continue;
    }
    if (line.startsWith("# ")) {
      closeList();
      out.push(`<h2 id="code-reading-checklist">${inlineMarkdown(line.slice(2))}</h2>`);
      continue;
    }

    if (line.startsWith("- [ ] ")) {
      if (!inList) {
        out.push('<ul class="checklist">');
        inList = true;
      }
      out.push(
        `<li><label><input type="checkbox"> ${inlineMarkdown(line.slice(6))}</label></li>`,
      );
      continue;
    }

    if (line.startsWith("- ")) {
      if (!inList) {
        out.push('<ul class="checklist">');
        inList = true;
      }
      out.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
      continue;
    }

    closeList();
    out.push(`<p>${inlineMarkdown(line)}</p>`);
  }

  closeList();
  return out.join("\n");
}

const html = fs.readFileSync(htmlPath, "utf8");
const checklist = fs.readFileSync(checklistPath, "utf8");

if (html.includes('id="code-reading-checklist"')) {
  throw new Error("HTML already contains code-reading-checklist section");
}

const checklistHtml = `

<!-- ===== CODE READING CHECKLIST ===== -->
<div class="hr"></div>
<section class="code-reading-checklist-section">
${markdownToHtml(checklist)}
</section>
`;

const withToc = html.replace(
  '  <a class="toc-h4" href="#ch3-variety">3.4.5 ระบบจัดการพันธุ์ข้าว</a>\n</nav>',
  '  <a class="toc-h4" href="#ch3-variety">3.4.5 ระบบจัดการพันธุ์ข้าว</a>\n  <div class="sep"></div>\n  <a class="toc-h2" href="#code-reading-checklist">Code Reading Checklist</a>\n</nav>',
);

const withStyles = withToc.replace(
  "</style>",
  `  .checklist { list-style: none; padding-left: 0; }
  .checklist li { margin: 5px 0; padding-left: 0; }
  .checklist input[type="checkbox"] { margin-right: 8px; transform: translateY(1px); }
  .code-reading-checklist-section h3 { margin-top: 34px; }
</style>`,
);

const finalHtml = withStyles.replace("\n<script>\n// Active TOC highlight", `${checklistHtml}\n<script>\n// Active TOC highlight`);

fs.writeFileSync(outputPath, finalHtml);
