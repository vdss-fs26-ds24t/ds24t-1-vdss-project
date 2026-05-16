---
name: quarto
description: >
  Build reproducible documents, reports, presentations, dashboards, websites, and books
  with Quarto and Python. Use this skill whenever the user asks to create a `.qmd` file,
  render a notebook to HTML/PDF/Word/Typst, build a Quarto project, make a Revealjs
  presentation, create a Quarto dashboard, set up a Quarto website or blog, or author
  a scholarly manuscript with citations and cross-references. Also trigger when the user
  mentions "quarto", "qmd", "quarto render", "quarto preview", executable markdown,
  "literate programming in Python", or wants to combine Python code, prose, and
  publication-quality output in a single reproducible workflow. Covers YAML front matter,
  code cell options, execution control, figure/table cross-references, callout blocks,
  dashboards, presentations, multi-format output, project structure, publishing, and
  caching. Even if the user doesn't say "Quarto" explicitly, consider this skill when
  they want a reproducible document that mixes Python computation with narrative text.
---

# Quarto Skill (Python Focus)

Create publication-quality, reproducible documents powered by Python. This skill covers
the full Quarto workflow: document structure, YAML configuration, executable code cells,
output formats, cross-references, dashboards, presentations, websites, books, projects,
caching, and publishing.

---

## 1. What Is Quarto

Quarto is an open-source scientific and technical publishing system. You author content
in `.qmd` (Quarto Markdown) files or `.ipynb` Jupyter notebooks that mix narrative
markdown with executable code. Quarto renders these into HTML, PDF, Word, Typst,
Revealjs slides, dashboards, websites, books, and more.

Quarto uses Jupyter kernels under the hood. If Python 3 and the `jupyter` package are
installed, Quarto can execute Python code blocks during rendering — no extra setup needed.

### 1.1 Installation Check

```bash
quarto check jupyter
```

Override the Python version with the `QUARTO_PYTHON` environment variable if needed.

---

## 2. Document Anatomy

Every `.qmd` file has two parts: a YAML front matter block and the body.

### 2.1 Minimal Document

```yaml
---
title: "Quarterly Revenue Report"
author: "Data Team"
date: today
format: html
jupyter: python3
---
```

```markdown
## Overview

This report summarises Q3 performance.

```{python}
#| label: fig-revenue
#| fig-cap: "Monthly revenue trend"

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("revenue.csv")
df.plot(x="month", y="revenue", kind="line")
plt.tight_layout()
plt.show()
```

As shown in @fig-revenue, revenue grew steadily.
```

### 2.2 Key YAML Fields

| Field | Purpose | Example |
|---|---|---|
| `title` | Document title | `"My Report"` |
| `author` | One or more authors | `"Jane Doe"` or a list |
| `date` | Publication date | `today`, `last-modified`, or a literal date |
| `format` | Output format(s) | `html`, `pdf`, `docx`, `typst`, `revealjs` |
| `jupyter` | Jupyter kernel | `python3` |
| `execute` | Execution options block | See §4 |
| `bibliography` | Path to `.bib` file | `references.bib` |
| `csl` | Citation style | `apa.csl` |
| `toc` | Table of contents | `true` |
| `number-sections` | Numbered headings | `true` |
| `code-fold` | Collapse code in HTML | `true`, `false`, `show` |
| `code-line-numbers` | Show line numbers | `true` |
| `theme` | HTML Bootstrap theme | `cosmo`, `flatly`, `darkly`, etc. |

---

## 3. Code Cells

### 3.1 Executable Code Blocks

Wrap Python code in fenced blocks with `{python}`:

````markdown
```{python}
import numpy as np
x = np.linspace(0, 2 * np.pi, 100)
```
````

These blocks are executed during `quarto render`. Their output (text, plots, tables)
is captured and embedded in the final document.

### 3.2 Cell-Level Options

Cell options use the `#|` (hash-pipe) comment syntax at the top of the block:

````markdown
```{python}
#| label: fig-scatter
#| fig-cap: "Relationship between X and Y"
#| fig-width: 8
#| fig-height: 5
#| echo: false
#| warning: false

import matplotlib.pyplot as plt
plt.scatter(df["x"], df["y"])
plt.show()
```
````

### 3.3 Common Cell Options Reference

| Option | Type | Description |
|---|---|---|
| `label` | `str` | Unique identifier for cross-referencing. Prefix with `fig-` for figures, `tbl-` for tables. |
| `fig-cap` | `str` | Figure caption |
| `fig-subcap` | `list` | Subcaptions for multi-panel figures |
| `fig-width` | `float` | Figure width in inches |
| `fig-height` | `float` | Figure height in inches |
| `fig-align` | `str` | `default`, `left`, `center`, `right` |
| `tbl-cap` | `str` | Table caption |
| `echo` | `bool` | Show source code in output (`true`/`false`) |
| `eval` | `bool` | Execute the code (`true`/`false`) |
| `output` | `bool/str` | Show output. `false` hides, `"asis"` renders raw markdown. |
| `warning` | `bool` | Show warnings |
| `error` | `bool` | If `true`, continue rendering even on errors |
| `include` | `bool` | If `false`, execute but show nothing (no code, no output) |
| `code-fold` | `bool/str` | Fold code in HTML output |
| `code-summary` | `str` | Label for the fold toggle (e.g. `"Show the code"`) |
| `code-overflow` | `str` | `wrap` or `scroll` |
| `cache` | `bool` | Cache cell results |
| `freeze` | `bool/str` | `true` or `auto` — skip re-execution during project renders |
| `column` | `str` | Layout column: `body`, `page`, `screen`, `margin` |
| `panel` | `str` | `tabset`, `sidebar`, `fill`, `center` |
| `layout-ncol` | `int` | Number of columns for multi-output layout |
| `layout-nrow` | `int` | Number of rows for multi-output layout |

### 3.4 Inline Code

For inline computation within prose, use backtick syntax:

```markdown
The mean value is `{python} f"{df['revenue'].mean():.2f}"`.
```

This renders as part of the paragraph text.

---

## 4. Execution Options

Control code execution globally in YAML under the `execute` key:

```yaml
execute:
  echo: false          # Hide all code by default
  warning: false       # Suppress warnings globally
  cache: true          # Cache all cell outputs
  freeze: auto         # Re-execute only when source changes (projects)
  enabled: true        # Set to false to skip all execution
  daemon: 300          # Keep kernel alive for 300 seconds (speeds re-renders)
```

### 4.1 Precedence

Cell-level `#|` options override document-level `execute` options, which override
project-level `_quarto.yml` settings.

### 4.2 Caching

Quarto uses `jupyter-cache` under the hood. Install it with:

```bash
python3 -m pip install jupyter-cache
```

When `cache: true`, cell outputs are stored. If any cell in the notebook changes,
all cells are re-executed. Markdown-only changes do not invalidate the cache.

Command-line overrides:

```bash
quarto render doc.qmd --cache           # Force caching on
quarto render doc.qmd --no-cache        # Force caching off
quarto render doc.qmd --cache-refresh   # Refresh the cache
```

### 4.3 Freeze (Project-Level)

For multi-document projects, use `freeze` to avoid re-executing unchanged documents:

```yaml
execute:
  freeze: auto   # Re-render only when the source .qmd changes
```

Individual document renders (`quarto render doc.qmd`) always execute regardless of
the `freeze` setting.

---

## 5. Cross-References

Cross-references let you link to figures, tables, equations, sections, and custom
floats with automatic numbering.

### 5.1 Figures

````markdown
```{python}
#| label: fig-trend
#| fig-cap: "Revenue over time"

df.plot(x="month", y="revenue")
plt.show()
```

See @fig-trend for the trend.
````

### 5.2 Tables

````markdown
```{python}
#| label: tbl-summary
#| tbl-cap: "Summary statistics"

from IPython.display import Markdown
Markdown(df.describe().to_markdown())
```

@tbl-summary shows summary statistics.
````

### 5.3 Equations

```markdown
$$
E = mc^2
$$ {#eq-einstein}

As shown in @eq-einstein, energy and mass are equivalent.
```

### 5.4 Sections

```markdown
## Methodology {#sec-methods}

See @sec-methods for details.
```

### 5.5 Prefix Rules

| Prefix | Type |
|---|---|
| `fig-` | Figure |
| `tbl-` | Table |
| `eq-` | Equation |
| `sec-` | Section |
| `lst-` | Listing |
| `thm-` | Theorem |

Labels must start with the correct prefix for cross-references to work.

---

## 6. Authoring Features

### 6.1 Callout Blocks

```markdown
::: {.callout-note}
This is a note callout.
:::

::: {.callout-warning}
## Deprecation Warning
This API will be removed in v3.0.
:::

::: {.callout-tip collapse="true"}
## Click to expand
Hidden content here.
:::
```

Available types: `note`, `warning`, `important`, `tip`, `caution`.

### 6.2 Tabsets

```markdown
::: {.panel-tabset}

## Matplotlib

```{python}
plt.plot(x, y)
plt.show()
```

## Plotly

```{python}
import plotly.express as px
px.line(df, x="month", y="revenue")
```

:::
```

### 6.3 Figures from Markdown

```markdown
![Caption text](image.png){#fig-photo fig-alt="Alt text" width=80%}
```

### 6.4 Tables from Markdown

```markdown
| Column A | Column B |
|----------|----------|
| 1        | alpha    |
| 2        | beta     |

: My table caption {#tbl-data}
```

### 6.5 Diagrams

Quarto renders Mermaid and Graphviz diagrams natively:

````markdown
```{mermaid}
flowchart LR
    A[Raw Data] --> B[Clean]
    B --> C[Analyse]
    C --> D[Report]
```
````

### 6.6 Code Annotation

````markdown
```{python}
import pandas as pd          # <1>
df = pd.read_csv("data.csv") # <2>
df = df.dropna()              # <3>
```

1. Import the pandas library.
2. Load the dataset from a CSV file.
3. Remove rows with missing values.
````

### 6.7 Citations

Reference a `.bib` file in YAML, then cite with `@key` syntax:

```yaml
bibliography: references.bib
```

```markdown
Recent work [@smith2024] demonstrates that...
```

### 6.8 Article Layout

Control how content spans the page in HTML output:

````markdown
```{python}
#| column: page

wide_plot()
```
````

Layout options: `body` (default), `body-outset`, `page`, `page-inset-left`,
`page-inset-right`, `screen`, `screen-inset`, `margin`.

---

## 7. Output Formats

### 7.1 Single Format

```yaml
format: html
```

### 7.2 Multiple Formats

```yaml
format:
  html:
    toc: true
    code-fold: true
    theme: cosmo
  pdf:
    documentclass: article
    papersize: a4
  docx:
    reference-doc: template.docx
```

Render a specific format:

```bash
quarto render doc.qmd --to pdf
```

### 7.3 Format-Specific Notes

**HTML** — supports themes (25+ Bootstrap themes), `code-fold`, `code-tools`,
lightbox figures, and interactive widgets. Add `self-contained: true` for a
single portable `.html` file.

**PDF** — requires a LaTeX installation (TinyTeX recommended: `quarto install tinytex`).
Configure via `pdf-engine`, `documentclass`, `geometry`, `fontfamily`, etc.

**Typst** — a modern alternative to LaTeX. Faster compilation, simpler syntax. Use
`format: typst` and customise with Typst-specific options.

**Word (docx)** — use `reference-doc` to apply a custom Word template with your
organisation's styles.

**Revealjs** — see §8.

---

## 8. Presentations (Revealjs)

### 8.1 Basic Setup

```yaml
---
title: "My Talk"
format: revealjs
jupyter: python3
---
```

Slides are separated by level-2 headings (`##`). Level-1 headings (`#`) create
section title slides.

### 8.2 Slide with Code

````markdown
## Data Loading

```{python}
#| echo: true
#| code-line-numbers: "|1|3-4"

import pandas as pd

df = pd.read_csv("data.csv")
df.head()
```
````

`code-line-numbers` highlights specific lines step by step during presentation.

### 8.3 Key Revealjs Options

```yaml
format:
  revealjs:
    theme: dark            # Built-in themes: beige, blood, dark, league, moon, etc.
    slide-number: true
    transition: slide      # none, fade, slide, convex, concave, zoom
    width: 1600
    height: 900
    center: true
    code-fold: true
    scrollable: true
    smaller: true          # Smaller base font
    incremental: true      # Bullet points appear one at a time
    footer: "Company Name"
    logo: logo.png
    chalkboard: true       # Enable drawing on slides
```

### 8.4 Speaker Notes

```markdown
## My Slide

Content visible to the audience.

::: {.notes}
These notes are only visible in the speaker view (press S).
:::
```

### 8.5 Fragments (Incremental Reveal)

```markdown
::: {.fragment}
This appears on click.
:::

::: {.fragment .fade-in-then-out}
This fades in, then fades out.
:::
```

### 8.6 Multi-Column Slides

```markdown
:::: {.columns}

::: {.column width="50%"}
Left column content.
:::

::: {.column width="50%"}
Right column content.
:::

::::
```

### 8.7 Other Presentation Formats

```yaml
format: pptx        # PowerPoint
format: beamer      # LaTeX Beamer (PDF slides)
```

---

## 9. Dashboards

### 9.1 Basic Setup

```yaml
---
title: "Sales Dashboard"
format: dashboard
jupyter: python3
---
```

### 9.2 Layout Model

Dashboards use headings and code cells as layout primitives:

- `#` (H1) — creates pages (tabs when multiple exist)
- `##` (H2) — creates rows
- `###` (H3) — creates cards within rows

````markdown
## Row {height=70%}

```{python}
#| title: Revenue Over Time
df.plot(x="month", y="revenue")
plt.show()
```

```{python}
#| title: Revenue by Region
df.groupby("region")["revenue"].sum().plot(kind="bar")
plt.show()
```

## Row {height=30%}

```{python}
#| title: Key Metrics
#| content: valuebox

dict(
    icon="currency-dollar",
    color="primary",
    value="$12.4M",
    title="Total Revenue"
)
```
````

### 9.3 Orientation

```yaml
format:
  dashboard:
    orientation: columns   # Default is "rows"
```

With `orientation: columns`, `##` headings create columns instead of rows.

### 9.4 Value Boxes

Display key metrics using the `valuebox` content type:

````markdown
```{python}
#| content: valuebox
#| title: "Active Users"
#| icon: people
#| color: success

dict(value=f"{active_users:,}")
```
````

### 9.5 Tabsets in Dashboards

```markdown
## Row {.tabset}

### Tab One

Content for first tab.

### Tab Two

Content for second tab.
```

### 9.6 Data Display

For interactive tables in dashboards, use the `itables` library:

```python
from itables import show
show(df, paging=True, searching=True)
```

### 9.7 Interactive Dashboards (Shiny for Python)

Add `server: shiny` to make dashboards interactive with reactive inputs and outputs:

```yaml
---
title: "Interactive Dashboard"
format: dashboard
server: shiny
jupyter: python3
---
```

````markdown
## {.sidebar}

```{python}
from shiny import ui, render
ui.input_slider("n", "Sample size", 10, 1000, 250)
```

## Column

```{python}
@render.plot
def histogram():
    import numpy as np
    data = np.random.randn(input.n())
    plt.hist(data, bins=30)
```
````

---

## 10. Websites and Blogs

### 10.1 Project Configuration

Create `_quarto.yml` in the project root:

```yaml
project:
  type: website

website:
  title: "My Site"
  navbar:
    left:
      - text: Home
        href: index.qmd
      - text: About
        href: about.qmd
      - text: Blog
        href: blog.qmd

format:
  html:
    theme: cosmo
    toc: true
```

### 10.2 Blog

```yaml
# blog.qmd front matter
---
title: "Blog"
listing:
  contents: posts
  sort: "date desc"
  type: default          # default, grid, or table
  categories: true
---
```

Each post is a `.qmd` file inside the `posts/` directory with its own YAML front matter
including `title`, `date`, `author`, `categories`, and `description`.

### 10.3 Website Search

Quarto websites include built-in search. Enable or disable in `_quarto.yml`:

```yaml
website:
  search: true
```

---

## 11. Books

```yaml
project:
  type: book

book:
  title: "My Book"
  author: "Author Name"
  chapters:
    - index.qmd
    - intro.qmd
    - methods.qmd
    - results.qmd
    - references.qmd

format:
  html:
    theme: cosmo
  pdf:
    documentclass: scrbook
```

Books support cross-references across chapters and render to HTML, PDF, and EPUB.

---

## 12. Manuscripts

Manuscripts are notebook-first scholarly articles with embedded computation:

```yaml
project:
  type: manuscript

manuscript:
  article: article.qmd
  notebooks:
    - notebooks/analysis.ipynb
```

Manuscripts produce a bundled output with the article, source notebooks, and
supplementary materials all linked together.

---

## 13. Project Structure

### 13.1 Single Document

A standalone `.qmd` file — no project configuration needed.

### 13.2 Multi-Document Project

```
my-project/
├── _quarto.yml          # Project config (type, format, shared options)
├── index.qmd            # Home / main document
├── analysis.qmd
├── appendix.qmd
├── _variables.yml       # Shared variables (referenced with {{< var key >}})
├── references.bib       # Bibliography
├── custom.scss          # Custom theme overrides
├── images/
│   └── logo.png
└── _freeze/             # Frozen execution output (auto-generated)
```

### 13.3 `_quarto.yml` Essentials

```yaml
project:
  type: website           # website, book, manuscript, or default

format:
  html:
    theme: flatly
    toc: true
    code-fold: true

execute:
  freeze: auto            # Only re-execute when source changes
  cache: true
```

### 13.4 Virtual Environments

Quarto respects standard Python virtual environments. Activate your venv before
running `quarto render` or set `QUARTO_PYTHON` to point to the venv's Python binary.

For `requirements.txt` or `conda` environments, see the Quarto docs on
[Virtual Environments](https://quarto.org/docs/projects/virtual-environments.html).

### 13.5 Environment Variables

Use `_environment` or `_environment.local` files (gitignored) for project-level env vars:

```
# _environment.local
API_KEY=sk-xxxx
DB_HOST=localhost
```

---

## 14. Publishing

### 14.1 Quarto Pub (Free Hosting)

```bash
quarto publish quarto-pub
```

### 14.2 GitHub Pages

```bash
quarto publish gh-pages
```

Or configure in `_quarto.yml` for CI/CD:

```yaml
project:
  type: website
  output-dir: docs
```

### 14.3 Netlify

```bash
quarto publish netlify
```

### 14.4 Other Targets

Quarto also supports Posit Connect, Posit Connect Cloud, Confluence, and Hugging Face
Spaces. See the [Publishing Guide](https://quarto.org/docs/publishing/index.html).

### 14.5 Self-Contained HTML

For sharing a single file via email or download:

```yaml
format:
  html:
    embed-resources: true
```

---

## 15. CLI Quick Reference

| Command | Description |
|---|---|
| `quarto render doc.qmd` | Render to all formats in YAML |
| `quarto render doc.qmd --to pdf` | Render to a specific format |
| `quarto render doc.ipynb --execute` | Render a notebook with execution |
| `quarto preview doc.qmd` | Live preview with auto-reload |
| `quarto preview doc.qmd --to pdf` | Live preview as PDF |
| `quarto publish quarto-pub` | Publish to Quarto Pub |
| `quarto publish gh-pages` | Publish to GitHub Pages |
| `quarto check jupyter` | Verify Jupyter setup |
| `quarto convert doc.qmd` | Convert `.qmd` to `.ipynb` (or vice versa) |
| `quarto install tinytex` | Install TinyTeX for PDF rendering |

---

## 16. Python Libraries for Quarto

### 16.1 Plotting

Any Python plotting library works. The most common choices:

- **Matplotlib** — static plots, widest compatibility, works in all output formats.
- **Plotly** — interactive HTML charts. Use `plotly.io.show()` or just return the figure.
- **Altair** — declarative statistical visualisation.
- **Seaborn** — statistical plots built on matplotlib.

### 16.2 Tables

- **pandas** — `df.to_markdown()` combined with `#| output: asis` for markdown tables.
- **Great Tables** (`great_tables`) — publication-quality tables with rich formatting.
- **itables** — interactive DataTables for HTML output.
- **tabulate** — simple text tables.

### 16.3 Displaying Rich Output

Use `IPython.display` to emit raw HTML or Markdown from code cells:

```python
from IPython.display import Markdown, HTML

Markdown(f"The mean is **{value:.2f}**.")
```

Combine with `#| output: asis` for full control over rendered output.

---

## 17. Advanced Features

### 17.1 Includes

Reuse content across documents:

```markdown
{{< include _methods.qmd >}}
```

### 17.2 Variables

Define in `_variables.yml`:

```yaml
version: "2.4.1"
release_date: "2025-03-15"
```

Use in any `.qmd`:

```markdown
Current version: {{< var version >}} (released {{< var release_date >}}).
```

### 17.3 Conditional Content

Show content only for specific formats:

```markdown
::: {.content-visible when-format="html"}
This only appears in HTML output.
:::

::: {.content-hidden when-format="pdf"}
This is hidden in PDF output.
:::
```

### 17.4 Shortcodes

```markdown
{{< video https://www.youtube.com/watch?v=dQw4w9WgXcQ >}}
```

### 17.5 Embedding Notebook Cells

Pull specific cells from external `.ipynb` files into a `.qmd`:

```markdown
{{< embed notebooks/analysis.ipynb#fig-results >}}
```

### 17.6 Parameters

Parameterise documents for batch rendering:

```yaml
params:
  region: "North America"
  year: 2024
```

Access in code:

```python
region = params["region"]
```

Override from the command line:

```bash
quarto render report.qmd -P region:"Europe" -P year:2025
```

### 17.7 Rendering Script Files

Quarto can render plain `.py` files with specially formatted comments:

```python
# %% [markdown]
# ---
# title: "Analysis"
# format: html
# ---

# %% [markdown]
# ## Data Loading

# %%
import pandas as pd
df = pd.read_csv("data.csv")
df.head()
```

Render with:

```bash
quarto render analysis.py
```

---

## 18. Clean Code Standards for Quarto Documents

| Principle | Application |
|---|---|
| **Separate computation from prose** | Keep code cells focused on one task. Narrative explains the *why*; code produces the *what*. |
| **Label every figure and table** | Every code cell producing a visual or table gets a `label` and caption for cross-referencing. |
| **Hide boilerplate code** | Use `echo: false` at the document level and selectively show code with `echo: true` on pedagogical cells. |
| **Use cell options, not inline hacks** | Control output with `#|` options, not `plt.savefig()` workarounds or manual HTML. |
| **One concept per cell** | A code cell should produce one output. Split complex pipelines into multiple cells with explanatory markdown between them. |
| **Pin your environment** | Use `requirements.txt` or a conda `environment.yml`. Reproducibility fails without pinned dependencies. |
| **Use freeze in projects** | Set `freeze: auto` in multi-document projects so unchanged documents aren't needlessly re-executed. |
| **Cache expensive computation** | Use `cache: true` for cells with long-running operations (model training, large data loads). |
| **Type-hint helper functions** | Any Python function defined in a `.qmd` should have full type annotations. |
| **Keep YAML DRY** | Shared configuration goes in `_quarto.yml`. Per-document YAML should only contain overrides. |

---

## 19. Common Patterns

### Report with Hidden Code

```yaml
---
title: "Q3 Performance Report"
format:
  html:
    toc: true
    code-fold: true
    theme: flatly
execute:
  echo: false
  warning: false
---
```

### Multi-Format Output

```bash
quarto render report.qmd              # Renders all formats in YAML
quarto render report.qmd --to pdf     # Renders only PDF
```

### Parameterised Batch Rendering

```bash
for region in "EMEA" "APAC" "AMER"; do
  quarto render report.qmd -P region:"$region" --output "report_${region}.html"
done
```

### Notebook to Document

```bash
quarto convert analysis.ipynb         # .ipynb → .qmd
quarto render analysis.ipynb          # Render .ipynb directly (no execution by default)
quarto render analysis.ipynb --execute  # Render with execution
```

---

## Documentation Reference

- Get started: https://quarto.org/docs/get-started/index.html
- Guide: https://quarto.org/docs/guide/index.html
- Using Python: https://quarto.org/docs/computations/python.html
- Execution options: https://quarto.org/docs/computations/execution-options.html
- Cross-references: https://quarto.org/docs/authoring/cross-references.html
- Dashboards: https://quarto.org/docs/dashboards/index.html
- Presentations: https://quarto.org/docs/presentations/revealjs/index.html
- Websites: https://quarto.org/docs/websites/index.html
- Books: https://quarto.org/docs/books/index.html
- Manuscripts: https://quarto.org/docs/manuscripts/index.html
- Publishing: https://quarto.org/docs/publishing/index.html
- Projects: https://quarto.org/docs/projects/quarto-projects.html
- Virtual Environments: https://quarto.org/docs/projects/virtual-environments.html
- Extensions: https://quarto.org/docs/extensions/index.html
- Full reference: https://quarto.org/docs/reference/index.html
