---
name: streamlit
description: >
  Build interactive Streamlit web applications in Python. Use this skill whenever the user asks
  to create a dashboard, data app, internal tool, prototype UI, chat interface, or any web-based
  Python application using Streamlit. Also trigger when the user mentions "streamlit", "st.",
  "data app", "interactive dashboard", "deploy a Python app", or wants to quickly turn a script
  into a shareable web interface. Covers architecture, widgets, layout, caching, session state,
  multipage apps, data connections, secrets management, authentication, theming, chat UIs,
  fragments, forms, and deployment. Even if the user doesn't say "Streamlit" explicitly, consider
  this skill when they want a fast, Python-only web UI without writing HTML/JS.
---

# Streamlit Skill

Build production-quality Streamlit applications that follow clean coding standards.
This skill covers the full lifecycle: architecture, data flow, widgets, layout,
performance, state management, connections, security, authentication, multipage
navigation, and deployment.

---

## 1. Execution Model

Streamlit has a unique top-to-bottom rerun model that every decision in your app
must respect. Understanding it prevents the most common bugs.

### 1.1 Data Flow

Streamlit reruns the **entire Python script** from top to bottom in two situations:

1. The source file is saved (during development).
2. A user interacts with any widget.

This means every variable is re-evaluated on each run. Expensive work must be
cached (see §5). Side effects (DB writes, API calls) must be gated behind
explicit user actions like button clicks or form submissions.

### 1.2 Client-Server Architecture

Streamlit apps are a Python **server** (Tornado + WebSockets) with a React
**client** rendered in the browser.

Key implications:

- The server does all computation; the client only renders UI.
- File paths in your code reference the **server** filesystem, not the user's machine.
- Users can only provide files through `st.file_uploader` or `st.camera_input`.
- Programs opened via `subprocess` or `os.system` run on the server, invisible to the user.
- For load-balanced deployments, enable **session affinity / stickiness** so all
  requests from one user hit the same replica. Without this, media files and
  uploads may break.

### 1.3 Widget Callbacks

Callbacks passed via `on_change` or `on_click` execute **before** the rest of
the script on that rerun. Use them to mutate `st.session_state` before the UI
renders.

---

## 2. Project Structure

Organize apps for maintainability. Separate concerns early.

```
my_app/
├── streamlit_app.py          # Entry point — navigation + shared chrome
├── pages/
│   ├── dashboard.py          # st.Page source files
│   ├── settings.py
│   └── upload.py
├── lib/
│   ├── __init__.py
│   ├── data.py               # @st.cache_data functions (loaders, transforms)
│   ├── models.py             # @st.cache_resource functions (ML, DB connections)
│   └── auth.py               # Authentication helpers
├── components/
│   └── charts.py             # Reusable chart/widget wrappers
├── static/                   # Hosted static files (images, CSS)
├── .streamlit/
│   ├── config.toml           # Theme and server config
│   └── secrets.toml          # Local secrets (NEVER commit)
├── requirements.txt
└── .gitignore                # Must include .streamlit/secrets.toml
```

### Entry Point Pattern

```python
# streamlit_app.py
import streamlit as st

st.set_page_config(page_title="My App", page_icon="🚀", layout="wide")

dashboard = st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True)
settings = st.Page("pages/settings.py", title="Settings", icon="⚙️")
upload = st.Page("pages/upload.py", title="Upload", icon="📁")

pg = st.navigation([dashboard, settings, upload])
pg.run()
```

---

## 3. Display API

### 3.1 Text

```python
st.title("Page Title")
st.header("Section Header")
st.subheader("Subsection")
st.markdown("Supports **bold**, _italic_, `code`, and LaTeX: $e^{i\\pi}+1=0$")
st.text("Fixed-width text")
st.code("print('hello')", language="python")
st.latex(r"F = ma")
st.badge("New")
st.html("<p>Raw HTML</p>")
```

### 3.2 Data

```python
st.dataframe(df)                           # Interactive table (sort, search, filter)
st.table(df.head())                        # Static table
st.metric("Revenue", "$12.4M", "+8.2%")   # KPI card with delta
st.json({"key": "value"})                  # Formatted JSON viewer
```

### 3.3 Media

```python
st.image("logo.png", caption="Our logo")
st.logo("sidebar_logo.png")
st.audio(audio_bytes)
st.video(video_bytes, subtitles="subs.vtt")
st.pdf("report.pdf")
```

### 3.4 Charts

Built-in simple charts (auto-detect columns from DataFrame):

```python
st.line_chart(df)
st.area_chart(df)
st.bar_chart(df)
st.bar_chart(df, horizontal=True)
st.scatter_chart(df)
st.map(geo_df)                             # Expects 'lat' and 'lon' columns
```

For full control, use third-party libraries:

```python
st.plotly_chart(fig, on_select="rerun")    # Interactive Plotly
st.altair_chart(chart, on_select="rerun")  # Altair / Vega-Lite
st.pyplot(mpl_fig)                         # Matplotlib
st.graphviz_chart(dot_string)              # Graphviz DOT
st.pydeck_chart(deck)                      # deck.gl 3D maps
st.vega_lite_chart(df, spec)               # Vega-Lite spec
```

### 3.5 Magic Commands

Any variable or literal on its own line auto-renders via `st.write()`:

```python
"## This becomes a markdown header"
df                                          # Renders as interactive table
```

Use `st.write()` as the Swiss-Army knife — it auto-detects type:

```python
st.write("Text", df, fig, {"key": "val"})
st.write_stream(llm_stream)                # Stream LLM token-by-token
```

---

## 4. Interactive Widgets

Every widget returns its current value. Treat widgets as variables.

### 4.1 Input Widgets

```python
# Buttons
clicked = st.button("Submit")
st.download_button("Export CSV", csv_data, "report.csv", "text/csv")
st.link_button("Docs", "https://docs.streamlit.io")

# Selection
choice = st.radio("Pick one", ["A", "B", "C"])
selected = st.selectbox("Choose", options_list)
multi = st.multiselect("Tags", ["alpha", "beta", "gamma"])
pill = st.pills("Filter", ["Open", "Closed", "All"])
segment = st.segmented_control("View", ["Table", "Chart"])
toggle = st.toggle("Dark mode")
agreed = st.checkbox("I agree to the terms")

# Numeric / Slider
val = st.slider("Threshold", 0.0, 1.0, 0.5)
size = st.select_slider("Size", ["S", "M", "L", "XL"])
num = st.number_input("Count", min_value=0, max_value=100, value=10)

# Text
name = st.text_input("Your name")
bio = st.text_area("Bio", max_chars=500)

# Date / Time
date = st.date_input("Start date")
time = st.time_input("Meeting time")
dt = st.datetime_input("Event date and time")

# File / Media
file = st.file_uploader("Upload CSV", type=["csv", "xlsx"])
photo = st.camera_input("Take a selfie")
audio = st.audio_input("Record a voice note")
color = st.color_picker("Brand color", "#FF6347")

# Feedback
rating = st.feedback("stars")
```

### 4.2 Keys and State Binding

Assign a `key=` to any widget to bind it to `st.session_state`:

```python
st.text_input("Name", key="user_name")
# Now accessible anywhere as:
st.session_state.user_name
```

### 4.3 Disabling Widgets

```python
st.slider("Locked", 0, 100, disabled=True)
```

---

## 5. Caching

Caching is critical because the entire script reruns on every interaction.

### 5.1 `@st.cache_data` — For Serializable Data

Returns a **copy** each time (safe against mutation). Use for DataFrames,
dicts, lists, strings, numbers, API responses.

```python
@st.cache_data(ttl=3600)  # Expire after 1 hour
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

df = load_data("data.csv")
```

### 5.2 `@st.cache_resource` — For Global Resources

Returns the **same object** (shared across sessions). Use for DB connections,
ML models, HTTP clients — anything unserializable or expensive to duplicate.

```python
@st.cache_resource
def get_model():
    return load_heavy_model("weights.bin")

model = get_model()
```

### 5.3 Cache Management

```python
load_data.clear(path)          # Clear one cached call
load_data.clear()              # Clear all entries for this function
st.cache_data.clear()          # Clear ALL @st.cache_data entries globally
st.cache_resource.clear()      # Clear ALL @st.cache_resource entries globally
```

### 5.4 Best Practices

- Always set `ttl=` in production to prevent stale data and memory bloat.
- Never mutate a `@st.cache_resource` return value unless the mutation is
  intentional and thread-safe.
- Cache pure functions only — functions with side effects should not be cached.
- The cache key is derived from function name, code body, and input arguments.
  Changing any of these invalidates the cache automatically during development.

---

## 6. Session State

A per-user, per-tab dictionary that persists across reruns within a single
session. Resets when the user refreshes the browser tab.

### 6.1 Basic Usage

```python
# Initialize once
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Increment on every rerun
st.session_state.counter += 1
st.write(f"Reruns: {st.session_state.counter}")
```

### 6.2 Session State vs. Caching

| Feature | `st.session_state` | `@st.cache_data` |
|---|---|---|
| Scope | One user, one tab | All users, all sessions |
| Keyed by | Arbitrary string keys | Function + arguments |
| Use case | User-specific state, form data, step tracking | Expensive computations, shared data |

### 6.3 Widget Keys Are Session State

Every widget with `key="foo"` creates `st.session_state.foo` automatically.
You can read or pre-set widget values through Session State, but avoid setting
a widget's value directly during the same script run that renders it.

---

## 7. Layout and Containers

### 7.1 Sidebar

```python
with st.sidebar:
    st.selectbox("Model", ["gpt-4", "claude"])
    st.slider("Temperature", 0.0, 2.0, 0.7)
```

### 7.2 Columns

```python
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.line_chart(df)
with col2:
    st.metric("Users", 1_420)
with col3:
    st.metric("Revenue", "$52K")

# Bottom-aligned columns
col_a, col_b = st.columns(2, vertical_alignment="bottom")
```

### 7.3 Tabs

```python
tab_table, tab_chart = st.tabs(["Table", "Chart"])
with tab_table:
    st.dataframe(df)
with tab_chart:
    st.bar_chart(df)
```

### 7.4 Expander and Popover

```python
with st.expander("Advanced Options", icon=":material/info:"):
    st.slider("Learning rate", 0.001, 0.1)

with st.popover("Filters"):
    st.checkbox("Show archived")
```

### 7.5 Containers and Placeholders

```python
# Insert out of order
container = st.container()
st.write("This appears BELOW the container content")
container.write("This appears ABOVE")

# Horizontal flex layout
flex = st.container(horizontal=True)
flex.button("Save")
flex.button("Cancel")

# Replace content dynamically
placeholder = st.empty()
placeholder.text("Loading...")
# Later:
placeholder.dataframe(result)
```

---

## 8. Control Flow

### 8.1 Stop, Rerun, Navigate

```python
st.stop()                                  # Halt script execution here
st.rerun()                                 # Force an immediate rerun
st.switch_page("pages/settings.py")        # Navigate to another page
```

### 8.2 Forms — Batch Widget Inputs

Forms let the user fill in multiple widgets and submit them all at once,
preventing a rerun on every keystroke.

```python
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

if submitted:
    authenticate(username, password)
```

### 8.3 Dialogs

```python
@st.dialog("Confirm Delete")
def confirm_delete():
    st.write("Are you sure?")
    if st.button("Yes, delete"):
        delete_item()
        st.rerun()

if st.button("Delete"):
    confirm_delete()
```

### 8.4 Fragments — Partial Reruns

Decorate a function with `@st.fragment` so that interactions inside it only
rerun that fragment, not the whole page. Great for expensive pages with
isolated interactive sections.

```python
@st.fragment
def live_chart():
    data = fetch_realtime_data()
    st.line_chart(data)
    st.button("Refresh")          # Only reruns this fragment

live_chart()
```

---

## 9. Status and Progress

```python
with st.spinner("Training model..."):
    train(model)
st.success("Done!")

bar = st.progress(0)
for i in range(100):
    bar.progress(i + 1)

with st.status("Authenticating...") as s:
    result = authenticate()
    s.update(label="Authenticated!", state="complete")

st.toast("File saved!")
st.balloons()
st.snow()

st.error("Something went wrong.")
st.warning("Check your input.")
st.info("Tip: use Ctrl+K to search.")
st.exception(caught_exception)
```

---

## 10. Chat-Based Apps

Build conversational UIs for LLM applications.

```python
import streamlit as st

# Initialize history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input
if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response
    with st.chat_message("assistant"):
        response = st.write_stream(call_llm(prompt))
    st.session_state.messages.append({"role": "assistant", "content": response})
```

---

## 11. Data Connections

### 11.1 `st.connection` — Built-In Convenience

Handles caching, secrets, and driver setup in one call.

```python
conn = st.connection("my_db", type="sql")
df = conn.query("SELECT * FROM users", ttl=600)
st.dataframe(df)
```

Configure the connection in `.streamlit/secrets.toml`:

```toml
[connections.my_db]
type = "sql"
dialect = "mysql"
username = "app_user"
password = "s3cret"
host = "db.example.com"
port = 3306
database = "production"
```

### 11.2 Supported Connection Types

- **SQL** (built-in): MySQL, PostgreSQL, SQLite, Snowflake, BigQuery via
  SQLAlchemy.
- **Snowflake** (built-in): Native Snowflake connector.
- **Cloud file storage** (`streamlit-files-connection`): S3, GCS, Azure Blob.
- **Google Sheets** (`streamlit-gsheets-connection`): Read/write Google Sheets.
- **Custom connections**: Extend `BaseConnection` for any data source.

### 11.3 Custom Connection Example

```python
from streamlit.connections import BaseConnection
import duckdb


class DuckDBConnection(BaseConnection[duckdb.DuckDBPyConnection]):
    def _connect(self, **kwargs) -> duckdb.DuckDBPyConnection:
        db = kwargs.pop("database", self._secrets.get("database", ":memory:"))
        return duckdb.connect(database=db, **kwargs)

    def query(self, sql: str, ttl: int = 3600) -> pd.DataFrame:
        @st.cache_data(ttl=ttl)
        def _query(sql: str) -> pd.DataFrame:
            return self._instance.execute(sql).fetchdf()
        return _query(sql)
```

### 11.4 Environment-Based Connection Switching

Use `env:` prefix for runtime connection selection:

```python
conn = st.connection("env:DB_CONN", "sql")
```

```bash
DB_CONN=staging streamlit run app.py
```

---

## 12. Secrets Management

### 12.1 File Locations

- **Global**: `~/.streamlit/secrets.toml` (shared across all local apps)
- **Per-project**: `.streamlit/secrets.toml` (overrides global)

Per-project secrets take precedence over global secrets.

### 12.2 Usage in Code

```python
api_key = st.secrets["OPENAI_API_KEY"]

# Nested sections
db_user = st.secrets.db_credentials.username

# Pass an entire section as kwargs
client.connect(**st.secrets.db_credentials)
```

Root-level secrets are also available as environment variables via `os.environ`.

### 12.3 Security Rules

- **Never commit secrets.toml** — add `.streamlit/secrets.toml` to `.gitignore`.
- **Never hardcode credentials** in source files.
- Use environment variables or secrets.toml for all sensitive values.
- On Streamlit Community Cloud, configure secrets via the app settings UI.
- `st.cache_data` and `st.session_state` use pickle internally — only cache and
  store data you trust.

---

## 13. User Authentication (OIDC)

Streamlit supports OpenID Connect for user authentication.

### 13.1 Supported Providers

Google Identity, Microsoft Entra ID, Okta, Auth0, and any OIDC-compliant
provider.

### 13.2 Configuration

```toml
# .streamlit/secrets.toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "randomly-generated-strong-secret"
client_id = "your-client-id"
client_secret = "your-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### 13.3 App Code

```python
import streamlit as st

if not st.user.is_logged_in:
    st.button("Log in with Google", on_click=st.login)
    st.stop()

st.button("Log out", on_click=st.logout)
st.write(f"Welcome, {st.user.name}!")
```

### 13.4 Multiple Providers

Define named provider sections under `[auth.<name>]` in secrets.toml and pass
the name to `st.login("google")` or `st.login("microsoft")`.

### 13.5 Session Behavior

- Identity cookies persist for 30 days unless the user logs out.
- `st.login()` and `st.logout()` both start new sessions after modifying the
  cookie.
- Logging out of one tab does not log out other already-open tabs.

---

## 14. Theming and Configuration

### 14.1 Page Config (call first, before any other st command)

```python
st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",             # "centered" (default) or "wide"
    initial_sidebar_state="expanded",
)
```

### 14.2 Custom Theme

Define in `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6347"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"            # "sans serif", "serif", or "monospace"
```

### 14.3 Context and Personalization

```python
st.context.cookies              # Dict of browser cookies
st.context.headers              # Dict of request headers
st.context.locale               # e.g. "en_US"
st.context.timezone             # e.g. "Europe/Zurich"
st.context.theme.type           # "light" or "dark"
st.context.ip_address           # User's IP address
```

---

## 15. Multipage Apps

### 15.1 Using `st.navigation`

```python
# streamlit_app.py
import streamlit as st

home = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
analytics = st.Page("pages/analytics.py", title="Analytics", icon="📈")
admin = st.Page("pages/admin.py", title="Admin", icon="🔒")

pg = st.navigation([home, analytics, admin])
pg.run()
```

### 15.2 Conditional Pages (Role-Based)

```python
pages = [home, analytics]
if st.session_state.get("is_admin"):
    pages.append(admin)
pg = st.navigation(pages)
pg.run()
```

---

## 16. Mutating Data and Dynamic Updates

```python
# Append rows to a displayed element
element = st.line_chart(df_initial)
element.add_rows(df_new_rows)
```

---

## 17. Testing

Streamlit has a built-in testing framework compatible with pytest.

```python
# tests/test_app.py
from streamlit.testing.v1 import AppTest

def test_counter_increments():
    at = AppTest.from_file("streamlit_app.py").run()
    assert at.session_state.counter == 1
    at.button[0].click().run()
    assert at.session_state.counter == 2
```

---

## 18. Deployment Checklist

1. Pin dependencies in `requirements.txt`.
2. Set `st.set_page_config()` as the **first** Streamlit call.
3. Move all secrets to environment variables or the deploy platform's secrets UI.
4. Set `ttl=` on every `@st.cache_data` call and `conn.query()` call.
5. For multi-replica deployments, enable session affinity.
6. Place hosted static assets in a `static/` directory and enable static file
   serving in config.
7. Run `streamlit config show` to review final configuration before deploying.

---

## 19. Clean Code Standards for Streamlit Apps

| Principle | Application |
|---|---|
| **Separate data from UI** | Data loading/transformation lives in `lib/` with `@st.cache_data`. Pages only call these functions and render results. |
| **No raw SQL / API calls in page files** | Wrap all external access behind cached functions or `st.connection`. |
| **Session State as controlled state** | Initialize all keys in one place (top of entry point or a dedicated `init_state()` function). |
| **Forms for batch input** | Group related inputs into `st.form` to avoid partial-state reruns. |
| **Fragments for isolation** | Use `@st.fragment` for independent interactive sections on heavy pages. |
| **Type hints everywhere** | All helper functions should have typed signatures. |
| **No global mutable state** | Use `st.session_state` for user state, `@st.cache_resource` for shared singletons. |
| **Secrets never in code** | All credentials live in `secrets.toml` or environment variables. |

---

## 20. Quick Reference — Common Patterns

### Gate Expensive Work Behind a Button

```python
if st.button("Generate Report"):
    with st.spinner("Building..."):
        report = build_report(params)
    st.download_button("Download", report, "report.pdf")
```

### File Upload → Process → Download

```python
uploaded = st.file_uploader("Upload CSV")
if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df)
    processed = transform(df)
    st.download_button("Download Result", processed.to_csv(), "result.csv")
```

### Sidebar Filters → Main Content

```python
with st.sidebar:
    region = st.selectbox("Region", regions)
    date_range = st.date_input("Date range", value=(start, end))

filtered = df[(df.region == region) & (df.date.between(*date_range))]
st.bar_chart(filtered.groupby("product").revenue.sum())
```

---

## Documentation Reference

- Cheat sheet: https://docs.streamlit.io/develop/quick-reference/cheat-sheet
- Main concepts: https://docs.streamlit.io/get-started/fundamentals/main-concepts
- Advanced concepts: https://docs.streamlit.io/get-started/fundamentals/advanced-concepts
- Architecture: https://docs.streamlit.io/develop/concepts/architecture/architecture
- Secrets: https://docs.streamlit.io/develop/concepts/connections/secrets-management
- Authentication: https://docs.streamlit.io/develop/concepts/connections/authentication
- Connecting to data: https://docs.streamlit.io/develop/concepts/connections/connecting-to-data
- Security: https://docs.streamlit.io/develop/concepts/connections/security-reminders
- API reference: https://docs.streamlit.io/develop/api-reference
