from pathlib import Path
import bibtexparser
import re
import subprocess

# --------- CONFIG ---------
pubfile = Path("Publications.bib")
talksfile = Path("Talks.bib")
cvfile = Path("CV.tex")
htmlfile = Path("index.html")
author_to_bold = "Boukraa"
# --------------------------

def latex_to_unicode(s: str) -> str:
    """Convert common LaTeX accents to Unicode for HTML output."""
    replacements = {
        r"{\'a}": "á", r"{\'e}": "é", r"{\'i}": "í", r"{\'o}": "ó", r"{\'u}": "ú",
        r"{\`a}": "à", r"{\`e}": "è", r"{\`i}": "ì", r"{\`o}": "ò", r"{\`u}": "ù",
        r"{\^a}": "â", r"{\^e}": "ê", r"{\^i}": "î", r"{\^o}": "ô", r"{\^u}": "û",
        r"{\"a}": "ä", r"{\"e}": "ë", r"{\"i}": "ï", r"{\"o}": "ö", r"{\"u}": "ü",
        r"{\~n}": "ñ", r"{\c{c}}": "ç",
        r"\\&": "&"
    }
    for latex, uni in replacements.items():
        s = s.replace(latex, uni)
    return re.sub(r"[{}]", "", s)

def shorten_url(url: str) -> str:
    """Return only the domain (no https/http)."""
    return url.replace("https://", "").replace("http://", "").strip("/")

def format_authors(authors_raw: str, html=False):
    authors = [a.strip() for a in authors_raw.replace("\n", " ").split(" and ")]
    out = []
    for a in authors:
        if author_to_bold in a:
            if html:
                out.append(f"<strong>{a}</strong>")
            else:
                out.append(f"\\textbf{{{a}}}")
        else:
            out.append(a)
    authors_str = ", ".join(out)
    return latex_to_unicode(authors_str) if html else authors_str

def format_publication(entry, html=False):
    etype = entry["ENTRYTYPE"].lower()
    authors = format_authors(entry.get("author", ""), html=html)
    title = entry.get("title", "").strip("{}")
    year = entry.get("year", "")
    doi = entry.get("doi", "")
    hal = entry.get("hal_id", "") or entry.get("url", "")

    if html:
        title = latex_to_unicode(title)

    if etype == "article":
        journal = entry.get("journal", "")
        vol = entry.get("volume", "")
        num = entry.get("number", "")
        pages = entry.get("pages", "")

        details = f"{journal}"
        if vol:
            details += f", {vol}"
        if num:
            details += f"({num})"
        if pages:
            details += f", {pages}"
        if year:
            details += f", {year}"

        if html:
            line = f"{authors}. {title}. <em>{latex_to_unicode(details)}</em>."
            if doi:
                line += f' <a href="https://doi.org/{doi}">DOI</a>'
            if hal:
                line += f' <a href="{hal}">HAL</a>'
        else:
            line = f"\\item {authors}. {title}. \\textit{{{details}}}."
            if doi:
                 line += f": \\href{{https://doi.org/{doi}}}{{{doi}}}"
            #if hal:
              #  line += f" \\url{{https://hal.science/{hal}}}"
        return "journal", line

    elif etype == "inproceedings":
        book = entry.get("booktitle", "")
        addr = entry.get("address", "")
        details = f"{book}"
        if addr:
            details += f", {addr}"
        if year:
            details += f", {year}"

        if html:
            line = f"{authors}. {title}. <em>{latex_to_unicode(details)}</em>."
            if doi:
                line += f' <a href="https://doi.org/{doi}">DOI</a>'
            if hal:
                line += f' <a href="{hal}">HAL</a>'
        else:
            line = f"\\item {authors}. {title}. \\textit{{{details}}}."
            if doi:
                line += f": \\href{{https://doi.org/{doi}}}{{\\nolinkurl{{{doi}}}}}"
            else:
                line += f": \\href{{{hal}}}{{\\nolinkurl{{{hal}}}}}"
        return "conference", line

    return None, None

def format_talk(entry, html=False):
    title = entry.get("title", "")
    address = entry.get("address", "")
    year = entry.get("year", "")
    note = entry.get("note", "")
    url = entry.get("url", "")

    # Build details string with year after month
    details = address
    if note:
        details += f", {note} {year}" if year else f", {note}"
    elif year:
        details += f", {year}"

    if html:
        if url:
            line = f'{title}, {details}. <a href="{url}" style="text-decoration:none">↗️</a>'
        else:
            line = f"{title}, {details}."
    else:
        line = f"\\item {title}, {details}."
        if url:
            line += f" \\url{{{url}}}"   # no 🔗 website for LaTeX

    return entry.get("type", "other"), line


def replace_between_markers(text, begin_marker, end_marker, new_content):
    start = text.find(begin_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        raise ValueError(f"Markers {begin_marker} / {end_marker} not found")
    return text[: start + len(begin_marker)] + "\n" + new_content + "\n" + text[end:]

# --------- MAIN ---------
# Publications
with open(pubfile) as f:
    bib = bibtexparser.load(f)

journal_tex_entries, conf_tex_entries = [], []
journal_html_entries, conf_html_entries = [], []

bib.entries.sort(key=lambda e: e.get("year", "0"), reverse=True)

for entry in bib.entries:
    cat, line = format_publication(entry, html=False)
    if cat == "journal":
        journal_tex_entries.append(line)
    elif cat == "conference":
        conf_tex_entries.append(line)

    cat, line = format_publication(entry, html=True)
    if cat == "journal":
        journal_html_entries.append(f"<li>{line}</li>")
    elif cat == "conference":
        conf_html_entries.append(f"<li>{line}</li>")

# Talks
with open(talksfile) as f:
    talks = bibtexparser.load(f)

conf_talks_tex, other_talks_tex = [], []
conf_talks_html, other_talks_html = [], []

talks.entries.sort(key=lambda e: e.get("year", "0"), reverse=True)

for entry in talks.entries:
    cat, line = format_talk(entry, html=False)
    if cat == "conference":
        conf_talks_tex.append(line)
    else:
        other_talks_tex.append(line)

    cat, line = format_talk(entry, html=True)
    if cat == "conference":
        conf_talks_html.append(f"<li>{line}</li>")
    else:
        other_talks_html.append(f"<li>{line}</li>")

# --- Update CV files ---
for texfile in [cvfile, Path("CV-Full.tex")]:
    if texfile.exists():
        cv = texfile.read_text(encoding="utf-8")
        cv = replace_between_markers(
            cv, "% BEGIN JOURNALS", "% END JOURNALS",
            "\\begin{enumerate}\n" + "\n".join(journal_tex_entries) + "\n\\end{enumerate}"
        )
        cv = replace_between_markers(
            cv, "% BEGIN CONFS", "% END CONFS",
            "\\begin{enumerate}\n" + "\n".join(conf_tex_entries) + "\n\\end{enumerate}"
        )
        cv = replace_between_markers(
            cv, "% BEGIN CONF TALKS", "% END CONF TALKS",
            "\\begin{itemize}\n" + "\n".join(conf_talks_tex) + "\n\\end{itemize}"
        )
        cv = replace_between_markers(
            cv, "% BEGIN OTHER TALKS", "% END OTHER TALKS",
            "\\begin{itemize}\n" + "\n".join(other_talks_tex) + "\n\\end{itemize}"
        )
        texfile.write_text(cv, encoding="utf-8")
        print(f"✅ Updated {texfile.name}")

# --- Update index.html ---
html = htmlfile.read_text(encoding="utf-8")
html = replace_between_markers(
    html, "<!-- BEGIN JOURNALS -->", "<!-- END JOURNALS -->",
    "\n".join(journal_html_entries)
)
html = replace_between_markers(
    html, "<!-- BEGIN CONFS -->", "<!-- END CONFS -->",
    "\n".join(conf_html_entries)
)
html = replace_between_markers(
    html, "<!-- BEGIN CONF TALKS -->", "<!-- END CONF TALKS -->",
    "\n".join(conf_talks_html)
)
html = replace_between_markers(
    html, "<!-- BEGIN OTHER TALKS -->", "<!-- END OTHER TALKS -->",
    "\n".join(other_talks_html)
)
htmlfile.write_text(html, encoding="utf-8")
print("✅ Updated index.html with journals, conferences, and talks")

# --- Compile LaTeX CVs ---
for texfile in [cvfile, Path("CV-Full.tex")]:
    try:
        subprocess.run(["xelatex", "-interaction=nonstopmode", str(texfile)], check=True)
        subprocess.run(["xelatex", "-interaction=nonstopmode", str(texfile)], check=True)
        print(f"✅ {texfile.name} compiled successfully")
    except Exception as e:
        print(f"⚠️ LaTeX compilation failed for {texfile.name}:", e)
