import fs from "node:fs";

const htmlPath = "/Users/noppanut/Downloads/rice_expert_system_with_code_chatgpt.html";
const checklistPath = "CODE_READING_CHECKLIST_DETAILED.md";
const outputPath = "rice_expert_system_with_code_chatgpt_detailed_checklist.html";

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
      out.push(`<li><label><input type="checkbox"> ${inlineMarkdown(line.slice(6))}</label></li>`);
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
const newSection = `<section class="code-reading-checklist-section">\n${markdownToHtml(checklist)}\n</section>`;

const sectionRegex = /<section class="code-reading-checklist-section">[\s\S]*?<\/section>/;
if (!sectionRegex.test(html)) {
  throw new Error("Could not find existing code-reading-checklist-section");
}

const updated = html
  .replace(
    '<a class="toc-h2" href="#code-reading-checklist">Code Reading Checklist</a>',
    '<a class="toc-h2" href="#code-reading-checklist">เช็คลิสต์อ่านโค้ด</a>',
  )
  .replace(sectionRegex, newSection);
fs.writeFileSync(outputPath, updated);
