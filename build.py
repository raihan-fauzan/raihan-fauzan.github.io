import re

README_PATH = "README.md"
TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "index.html"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def md_inline(text):
    """Convert inline markdown: bold+italic, bold, italic, links."""
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text


def md_to_html(md_text):
    """Convert markdown to HTML with proper nesting of sections and cards."""
    lines = md_text.strip().split("\n")
    html = []
    list_items = []
    in_list = False
    in_card = False
    in_section = False
    is_first_content = True

    def flush_list():
        nonlocal list_items, in_list
        if list_items:
            indent = "    " if in_card else "  "
            html.append(f"{indent}<ul>")
            for item in list_items:
                html.append(f"{indent}  <li>{md_inline(item)}</li>")
            html.append(f"{indent}</ul>")
            list_items = []
            in_list = False

    def close_card():
        nonlocal in_card
        if in_card:
            flush_list()
            html.append("  </div>")
            in_card = False

    def close_section():
        nonlocal in_section
        if in_section:
            close_card()
            html.append("</section>")
            in_section = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            flush_list()
            i += 1
            continue

        # H1 — page title (skip, used in template header)
        if line.startswith("# ") and not line.startswith("## "):
            i += 1
            continue

        # H2 — main section
        if line.startswith("## "):
            close_section()
            section_name = line[3:].strip()
            section_id = section_name.lower().replace(" ", "-")
            html.append(f'<section id="{section_id}">')
            html.append(f"  <h2>{md_inline(section_name)}</h2>")
            in_section = True
            i += 1
            continue

        # H3 — subsection (open new card)
        if line.startswith("### "):
            close_card()
            subsection = line[4:].strip()
            html.append("  <div class='card'>")
            html.append(f"    <h3>{md_inline(subsection)}</h3>")
            in_card = True
            i += 1
            continue

            # Bold standalone — company/org name (pure bold lines only)
        if re.match(r"^\*\*.+\*\*$", line) and "***" not in line:
            flush_list()
            text = line.strip("*").strip()
            html.append(f"    <p class='subtitle'>{md_inline(text)}</p>")
            i += 1
            continue

        # Italic standalone — date
        if re.match(r"^\*.+\*$", line) and not line.startswith("**"):
            flush_list()
            text = line.strip("*").strip()
            html.append(f"    <p class='date'>{md_inline(text)}</p>")
            i += 1
            continue

        # List items
        if line.startswith("- "):
            in_list = True
            list_items.append(line[2:].strip())
            i += 1
            continue

        # Intro paragraph (before first section) — skip, already in header
        if not in_section and is_first_content:
            # This is the subtitle/intro text, skip it (shown in header)
            is_first_content = False
            # Skip this line and the next resume link line if present
            i += 1
            # Also skip the "download resume" paragraph that follows
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                if next_line.startswith("#"):
                    break
                # Skip the resume link line
                if "resume" in next_line.lower() or ".pdf" in next_line.lower():
                    i += 1
                break
            continue

        # Regular paragraph
        flush_list()
        html.append(f"    <p>{md_inline(line)}</p>")
        i += 1

    flush_list()
    close_section()

    return "\n".join(html)


def extract_resume_link(md_text):
    """Extract the resume PDF link from README."""
    match = re.search(r"\[.*?\]\((.*?\.pdf)\)", md_text)
    return match.group(1) if match else None


def build():
    md_content = read_file(README_PATH)
    template = read_file(TEMPLATE_PATH)

    # Extract page title from H1
    title_match = re.search(r"^# (.+)$", md_content, re.MULTILINE)
    page_title = title_match.group(1).strip() if title_match else "Personal Website"

    # Extract subtitle (professional summary — first non-heading line after H1)
    lines = md_content.strip().split("\n")
    subtitle = ""
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            subtitle = re.sub(r"\[.*?\]\(.*?\)", "", stripped).strip()
            break

    # Extract resume link
    resume_link = extract_resume_link(md_content)
    resume_html = ""
    if resume_link:
        resume_html = f'<p style="margin-top: 0.8rem;"><a href="{resume_link}" target="_blank">Download Resume (PDF)</a></p>'

    # Convert body
    body_html = md_to_html(md_content)

    # Inject into template
    output = template.replace("{{TITLE}}", page_title)
    output = output.replace("{{SUBTITLE}}", md_inline(subtitle))
    output = output.replace("{{RESUME_LINK}}", resume_html)
    output = output.replace("{{BODY}}", body_html)

    write_file(OUTPUT_PATH, output)
    print(f"Generated {OUTPUT_PATH} successfully!")


if __name__ == "__main__":
    build()
