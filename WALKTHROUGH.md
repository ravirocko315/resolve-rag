# Learn Resolve V1, statement by statement

Read the files next to this guide. Line numbers refer to the initial version; names remain useful if later edits shift lines. Blank lines separate ideas and do not execute. A `#` starts a comment. A triple-quoted string at the beginning of a module/function is its documentation, not an instruction to the AI.

## 1. The big picture

`app.py` collects a question. `core.py` loads our summaries, scores relevance, and returns evidence. If AI is explicitly enabled, it sends the question plus retrieved summaries to OpenAI. The interface displays the answer and trusted links. Draft generation is a separate local template operation.

**Retrieval** means finding relevant records. **Generation** means composing new text with a language model. Evidence mode demonstrates retrieval only. Optional AI mode combines them into RAG. We use keywords rather than vector embeddings in this version so no model download or database is necessary.

Python indentation defines which statements belong to an `if`, loop, function or exception handler. `def` declares a function; it does not call it. Type annotations such as `str` and `list[dict]` document expected types; they do not enforce them automatically. `return` exits a function with a value.

## 2. `core.py`: imports and vocabulary

| Lines | Explanation |
|---|---|
| 1 | Module description: reference IDs are not proof of correctness. |
| 3 | `http.client` supplies HTTP exception types for the fallback handler. |
| 4 | `json` converts between Python objects and JSON text. |
| 5 | `math` supplies the logarithm used in ranking. |
| 6 | `os` reads environment variables; it does not contain a hardcoded credential. |
| 7 | `re` provides regular expressions for tokens and citation validation. |
| 8 | Imports urllib's error module; errors are covered by the later OSError handler. |
| 9 | `urllib.request` makes the optional HTTPS API request. |
| 10 | `Counter` is a dictionary of occurrence counts. |
| 11 | `Path` represents filesystem paths portably. |
| 14–17 | Adjacent string literals join automatically; `.split()` separates words; `set(...)` creates a fast membership lookup for words ignored during retrieval. |
| 18–21 | `ALIASES` maps variations such as `refunds` to `refund`; dictionary colons separate keys from values. This is a tiny vocabulary, not language understanding. |
| 22–24 | `TOPICS` lists tokens accepted as consumer-related. A simple gate can make mistakes and is not robust jurisdiction classification. |
| 25 | `FIELDS` is a tuple listing mandatory fields for every source record. |
| 28 | Declares a helper returning a list of strings. An underscore marks an internal helper by convention. |
| 29–30 | Lowercases text, extracts English alphanumeric sequences, discards stopwords and normalizes aliases. A list comprehension builds the result; `.get(word, word)` uses the original word if no alias exists. |
| 33 | Declares a helper for checking a record's country. |
| 34 | Reads country safely, converts it to text, removes edge whitespace and compares case-insensitively to India. |

## 3. Loading sources: `core.py` lines 37–56

| Lines | Explanation |
|---|---|
| 37–38 | Declares `load_sources` and documents its safe empty-list fallback. |
| 39 | Begins an operation that may fail. |
| 40 | Reads UTF-8 text from the supplied path, then parses JSON into Python objects. |
| 41–42 | Catches filesystem, encoding and parsing errors; returns no sources rather than crashing. |
| 43–44 | Rejects JSON whose top level is not an array/list. |
| 45 | Creates an output list and a set for detecting duplicate IDs. Tuple assignment initializes both. |
| 46 | Iterates over source records. |
| 47–48 | Skips objects of the wrong shape and non-India records. `continue` moves to the next loop iteration. |
| 49–51 | Requires every mandatory field to be a nonempty string. `all(...)` checks each field. Short-circuit `and` avoids string operations on nonstrings. |
| 52–53 | Requires a simple citation ID and rejects duplicates. `fullmatch` checks the entire ID. |
| 54 | Appends a shallow copy so the input object need not be modified. |
| 55 | Records that the ID has been accepted. |
| 56 | Returns the accepted list. This validates structure, not factual accuracy. |

## 4. Retrieval: `core.py` lines 59–81

| Lines | Explanation |
|---|---|
| 59–60 | Declares retrieval with at most three results by default. The score is relevance, not confidence. |
| 61 | Takes at most 2,000 characters, tokenizes them and removes duplicate query tokens with `set`. |
| 62 | Keeps only India source records. |
| 63–64 | Stops when there is nothing meaningful to search or the requested limit is nonpositive. |
| 65–66 | Joins each source title and summary, tokenizes them, and counts occurrences. A missing field becomes an empty string. |
| 67 | Computes average token count; `or 1` prevents division by zero for empty documents. |
| 68 | For every query token, counts how many documents contain it. Summing booleans works because True counts as 1. |
| 69 | Initializes an empty ranked-results list. |
| 70 | `zip` pairs each source with its token counter. |
| 71 | Starts that source's score at zero. |
| 72–73 | Looks up each query term's count. A missing Counter entry returns zero. |
| 74 | Only matching terms contribute. |
| 75–76 | Computes inverse document frequency: a rare term contributes more than one found everywhere. `0.5` smooths small counts; `1 +` keeps the logarithm positive. |
| 77–78 | Adds a BM25-style term contribution. Here `k1=1.5`, `b=0.75`, `k1+1=2.5` and `1-b=0.25`. Repeated terms have diminishing returns; length normalization reduces the advantage of long documents. |
| 79–80 | Keeps positive matches and copies all source fields into a new dictionary using `**source`, adding a numeric score. |
| 81 | Sorts descending with a small anonymous `lambda` function, then slices to the requested limit. |

This searches full short summary records: they are already small, manually authored chunks. It does not split long PDFs. A matching word is not proof that the source answers the question. English aliases, negation, retailer names and other countries are important limitations.

## 5. Evidence-only answers: `core.py` lines 84–94

| Lines | Explanation |
|---|---|
| 84 | Declares a formatter for retrieved source records. |
| 85–86 | Starts a list of paragraphs with an explicit coverage limitation. |
| 87 | Visits each retrieved source. |
| 88 | Comment explains why these must not be called quotations. |
| 89 | An f-string inserts title, summary and citation ID into a paragraph. `append` adds it to the list. |
| 90–93 | Adds outcome, accuracy and legal-advice limitations. |
| 94 | Joins paragraphs with two newline characters and returns the text. No LLM is involved. |

## 6. Optional AI request: `core.py` lines 97–142

| Lines | Explanation |
|---|---|
| 97–98 | Declares the network helper; its caller handles failures. |
| 99–108 | Builds the system instruction. It limits scope, forbids invented policy details, treats source text as untrusted, specifies citation syntax and asks the model to admit insufficient evidence. This prompt is not a security boundary or accuracy guarantee. |
| 109–110 | Builds small evidence dictionaries containing only ID, title and summary, truncating each value to 4,000 characters. The comprehension's `key` is local to that comprehension; it does not overwrite the API-key argument. |
| 111 | Chooses the configured model and caps completion tokens at 600. Some models may spend tokens on internal reasoning or not support this API, so compatibility must be checked. |
| 112 | Adds the system message. |
| 113–114 | Adds a user message containing JSON with the bounded question and summaries. JSON preserves structure; it does not make text immune to prompt injection. |
| 115–118 | Creates a request to a fixed OpenAI HTTPS endpoint. JSON becomes UTF-8 bytes; providing data makes this a POST. Headers identify the body format and carry the credential. |
| 119 | Explains the reason for disabling redirects. |
| 120 | Defines a specialized redirect handler class. |
| 121–122 | Overrides redirect behavior by returning None; credentials are not deliberately forwarded to another address. |
| 124 | Builds the opener and opens the request with a 20-second socket timeout. `with` closes the response automatically. This is not a strict whole-request wall-clock deadline. |
| 125 | Reads at most 65,537 bytes. The extra byte detects a response exceeding our cap. |
| 126–127 | Rejects oversized output. `raise` signals failure to the caller. |
| 128 | Parses the response body as JSON. |
| 129–130 | Selects the first completion and extracts its text. Malformed structures will cause a caught error. |
| 131–132 | Rejects truncated/nonstandard completion endings or nontext output. |
| 133 | Extracts strings enclosed in square brackets as candidate citations. |
| 134 | Builds the set of allowed IDs from the actual retrieved records. |
| 135–136 | Requires nonempty text, at least one citation, and no unknown citation. `<=` between sets means subset. |
| 137–138 | Removes well-formed references and rejects stray brackets. |
| 139 | Comment explains that links come from our source cards, not the model. |
| 140–141 | Rejects ordinary HTTP or `www.` links in generated prose. This is a limited pattern check, not a universal URL detector. |
| 142 | Removes edge whitespace and returns the answer. |

There are no automatic retries. A provider timeout can still mean the provider processed a request; the app falls back rather than secretly issuing another paid request. Valid IDs do not establish that generated claims are supported.

## 7. Orchestration: `core.py` lines 145–178

| Lines | Explanation |
|---|---|
| 145–146 | Public answer function; AI is false by default. Its returned dictionary is the interface contract with `app.py`. |
| 147 | Removes whitespace around the question. |
| 148 | A conditional expression chooses a truncation warning for oversized questions. |
| 149 | Enforces the input limit even if a caller bypasses the UI. |
| 150 | Initializes the standard result fields: answer, sources, mode and warning. |
| 151–153 | Empty input gets a helpful prompt and returns without retrieval or network use. |
| 154–155 | Recognizes several unrelated uses of words such as “return.” `re.I` means ignore case. |
| 156–158 | Rejects those patterns or questions having no topic token. `&` intersects two sets. This is a basic scope filter, not a classifier. |
| 159 | Retrieves matching source records. |
| 160 | Includes those actual records in the result for source cards. |
| 161–163 | No evidence means an explicit unsupported-answer message, not an AI guess. |
| 164 | Prepares a usable local answer before attempting any optional network work. |
| 165 | Enters the AI branch only when requested. |
| 166 | Reads and trims the two environment variables; missing ones default to empty strings. |
| 167–168 | Missing configuration produces a fallback warning. |
| 169–170 | Otherwise begins the protected API operation. |
| 171 | Attempts generation with the question and retrieved sources. |
| 172 | Marks AI mode only after a valid response is returned. |
| 173 | Adds an accuracy limitation even for a successful API response. |
| 174–176 | Handles transport, parsing and response-shape failures without exposing raw errors; the previously prepared evidence remains available. |
| 177 | Joins existing and new nonempty warnings. `filter(None, ...)` removes empty strings. |
| 178 | Returns the same result shape for every branch. |

## 8. Local complaint draft: `core.py` lines 181–193

| Lines | Explanation |
|---|---|
| 181–182 | Declares a deterministic template function. It does not call the AI or contact a seller. |
| 183 | Normalizes retailer whitespace, limits length to 200 and supplies a placeholder when empty. |
| 184 | Does the same for the issue, with a 2,000-character limit. |
| 185 | Begins the letter with the supplied business name and an order-number placeholder. `\n` represents a newline. |
| 186–187 | Adds greeting and purchase-detail placeholders instead of inventing dates or products. |
| 188 | Inserts the user's issue explicitly as unverified user-provided information. |
| 189 | Leaves the desired resolution for the user to supply. |
| 190 | Leaves an evidence-list placeholder. |
| 191 | Requests review without asserting legal obligations or deadlines. |
| 192 | Adds name/contact placeholders; complete these outside the demo. |
| 193 | Ends with a review reminder. Adjacent strings inside parentheses become one returned string. |

## 9. Streamlit's execution model

`app.py` executes top to bottom when a browser session opens. Most interactions rerun it. Forms batch widget values until submit. `st.session_state` retains selected values for the active session across reruns; it is not a database and should not be mistaken for permanent storage.

## 10. `app.py`: setup, sidebar and source loading

| Lines | Explanation |
|---|---|
| 1 | Module description and the basic launch command. |
| 3 | Reads environment configuration. |
| 4 | Builds a data-file path relative to this file. |
| 5 | Imports URL parsing so links can be checked structurally. |
| 7 | Imports Streamlit under its conventional short name `st`. |
| 9 | Imports the three core functions used by this interface. |
| 12 | Sets browser-tab title and icon before other UI output. |
| 13 | Displays the main heading. |
| 14–17 | Displays a warning banner describing limitations. |
| 18 | Adds a small reminder to check applicable terms. |
| 20–22 | Checks whether both environment variables are nonempty. It never prints their values and does not validate credentials. |
| 24 | Sends contained UI elements into the sidebar using a context manager. |
| 25–26 | Sidebar title and description. |
| 27–31 | Displays only whether configuration is present, not the key or model value. |
| 32–36 | Explains environment setup and that `.env` files are not automatically read. |
| 37–40 | Labels private-demo scope and the remaining public-release protections. |
| 41–45 | Explains in-memory state and possible hosting/provider retention. |
| 48–49 | Declares the source-link validator and its purpose. |
| 50–51 | Rejects nontext URLs. |
| 52 | Starts protected URL parsing. |
| 53 | Parses scheme, hostname, credentials and other URL components. |
| 54 | Normalizes the hostname, with an empty default. |
| 55–59 | Allows government `.gov.in` and `.nic.in` domains. This is an intentionally narrow starter-corpus rule; future retailer sources need a reviewed allowlist change. |
| 60–61 | Requires HTTPS and no embedded username/password, then returns the original URL. |
| 62–63 | Handles malformed URL parsing without exposing an exception. `pass` does nothing. |
| 64 | Invalid URLs produce None, so no clickable button is shown. |
| 67–69 | Loads bundled sources from the script's folder and records whether any survived validation. `__file__` is this module's path. |
| 70–72 | Unexpected source-loading failures disable answering. This broad UI handler protects usability but intentionally hides diagnostic detail. |
| 74–79 | Shows an explanatory error if the corpus is absent; drafting remains available. |

## 11. `app.py`: question and sources

| Lines | Explanation |
|---|---|
| 81 | Displays the question section heading. |
| 82–85 | Warns against entering identifying or sensitive information. |
| 86–89 | Explains the optional provider data transfer before the checkbox. |
| 90 | Creates a form with a unique identifier. |
| 91–94 | Creates a multiline input, caps its length, and supplies an example placeholder that is not automatically submitted. |
| 95 | Creates the default-off AI checkbox, disabled when configuration is incomplete. |
| 96 | Creates a submit button, disabled when no corpus is available. Its return value indicates whether this run submitted the form. |
| 98–99 | On submission, removes an older result; the None default prevents an error when none existed. |
| 100–101 | Shows a warning for empty input. |
| 102–104 | Otherwise starts protected processing with a progress indicator. |
| 105 | Calls the core; AI requires both the checkbox and server configuration. |
| 106–107 | Checks the minimum answer contract before rendering. |
| 108 | Stores the result across reruns. |
| 109–110 | Shows a generic error if the core unexpectedly fails. |
| 112 | Reads a stored result if present. |
| 113–114 | Shows the answer section only with both result and loaded corpus. |
| 115 | Uses plain text, not interpreted AI-generated Markdown/HTML. |
| 116 | Displays whether output is evidence or AI. |
| 117–118 | Displays any warning as plain text. |
| 119–120 | Labels source evidence and explains review-date limitations. |
| 121 | Retrieves the source list with an empty default. |
| 122–123 | Explains when no matching sources were used. |
| 124 | Comment: model-generated links are not trusted. |
| 125 | Builds an ID-to-record dictionary from the local corpus. |
| 126 | Visits each returned source entry. |
| 127–128 | Skips non-dictionary entries. |
| 129 | Resolves the returned ID to the trusted local record. |
| 130–131 | Skips unknown IDs. |
| 132 | Creates a bordered visual source card. |
| 133 | Displays source title. |
| 134 | Displays review date, not an inferred policy effective date. |
| 135 | Displays source country. |
| 136 | Displays source kind. |
| 137 | Displays the original authored summary, clearly labeled. |
| 138 | Validates the stored URL. |
| 139–140 | Creates a navigation button only for an allowed URL. |
| 141–142 | Otherwise explains that the link is unavailable. |

## 12. `app.py`: checklist and draft

| Lines | Explanation |
|---|---|
| 144–145 | Introduces suggestions and distinguishes them from official requirements. |
| 146–151 | Displays four fixed suggestions with newline-separated bullets. This is authored guidance, not a retrieved legal rule. |
| 153–154 | Introduces drafting and warns against personal details. |
| 155 | Starts a separate form so drafting does not submit a question. |
| 156 | Bounded retailer-name input. |
| 157 | Bounded generic issue input. |
| 158 | Submit button for local drafting. |
| 160–162 | Rejects empty retailer or issue values after submission. |
| 163–165 | Calls the local draft template inside a protected block. |
| 166–167 | Requires the template function to return text. |
| 168 | Saves the draft under the widget's state key. This assignment happens before that widget is instantiated on the rerun. |
| 169–170 | Provides a generic failure message. |
| 172 | Renders the editor only after a draft exists. |
| 173 | A text area bound to the same state key lets the user edit the draft. Height controls the visible editor size. |
| 174 | Reminds the user to add personal details elsewhere and that nothing is submitted. |
| 175–178 | Creates a text-file download from the current draft, with a filename and MIME type. This downloads content to the user's browser; it does not send a complaint. |

## 13. `data/sources.json`

JSON is data, not executable Python. The opening `[` and closing `]` form an array; each `{...}` is one source object; commas separate fields and records. Double quotes enclose strings. There are no comments in this JSON file.

Every record has the same seven fields:

- `id`: stable reference identifier such as `NCH-CONTACT`; the AI must cite this exact ID.
- `title`: a readable description, also included in keyword matching.
- `url`: the official reference page, not a generated link.
- `reviewed_on`: when we reviewed the page, not a policy-effective or expiry date.
- `country`: `India`; records for other countries are excluded by retrieval.
- `kind`: tells readers this is an original factual summary, not verbatim source text.
- `text`: the short summary searched and supplied as evidence.

The first record summarizes contact channels; the second explains registration/tracking; the third explains the limits of grievance resolution. Several records may point to one page because different passages address different questions. Neither the review date nor the official domain proves our interpretation correct: review the links and keep records updated.

## 14. Dependencies and environment

`requirements.txt` contains one line, `streamlit==1.49.1`. The `==` pins the direct package version. Pip installs Streamlit's transitive dependencies too; our core itself uses Python's standard library. A fully reproducible release needs those indirect versions locked as well.

`.env.example` lines 1–3 are comments describing setup and data-transfer consent. Line 4 names `OPENAI_API_KEY`; line 5 names `OPENAI_MODEL`. Values are deliberately placeholders. Do not copy placeholders into production and expect an AI response. This app has no dotenv loader: environment variables must actually be set on the process.

### Commands in the README, explained

- `python -m venv .venv`: run Python's environment-creation module and put the isolated environment in `.venv`.
- `git clone https://github.com/ravirocko315/resolve-rag.git`: download the public repository and its history into a new `resolve-rag` folder. `cd resolve-rag` enters that folder before the remaining commands.
- `.\.venv\Scripts\python.exe`: explicitly use that Windows environment's interpreter; no activation script is required.
- `-m pip install -r requirements.txt`: run the package installer; `-r` reads requirements from the named file.
- `-m unittest discover -v`: discover `test*.py` files and run tests with verbose names/results.
- `-m streamlit run app.py`: run the interface using the same environment where dependencies were installed.
- `--server.address=127.0.0.1`: accept only local connections for this development run.
- `--browser.gatherUsageStats=false`: disable Streamlit usage-statistics collection; this is not a promise about all platform logging.
- `docker build -t resolve-v1:local .`: build the current directory's Dockerfile and name/tag the image.
- `docker run --rm -p 127.0.0.1:8501:8501 resolve-v1:local`: launch that image, remove the container after it stops, and map the local host port to the container port.
- `-e OPENAI_API_KEY -e OPENAI_MODEL`: optionally forward variables already defined in the host environment without writing values in the command.
- `docker stop resolve-v1-demo`: stop the named local preview container gracefully. Because it was launched with `--rm`, Docker then removes that container, not the image or project files. The preview used `-d` to run detached and `--name resolve-v1-demo` to give it a readable name.

## 15. `Dockerfile`, line by line

| Lines | Explanation |
|---|---|
| 1 | Starts with a Debian-based slim Python 3.11 image. The moving tag is not an immutable digest. |
| 3 | Stops Python writing `.pyc` bytecode files. A backslash continues the Docker instruction onto the next line. |
| 4 | Makes Python output unbuffered for timely process logs. |
| 5 | Disables Streamlit usage statistics via environment configuration. |
| 7 | Sets the container's working directory to `/app`; this is inside Linux, not your Windows folder. |
| 8 | Copies only requirements first, improving build-cache reuse when application code changes. |
| 9 | Installs dependencies without retaining pip's download cache. |
| 10 | `&&` runs the next command only if installation succeeds; creates a nonroot account with UID 10001 and a home directory. |
| 12 | Copies application modules and assigns their ownership to that account. |
| 13 | Copies the bundled data directory with the same ownership. |
| 15 | Runs subsequent commands and the application as the nonroot account. |
| 16 | Documents the listening port; it does not itself publish that port on the host. |
| 17 | Configures checks every 30 seconds, a 5-second check timeout, 20-second startup grace and three failures before unhealthy status. |
| 18 | Opens Streamlit's health endpoint with Python, avoiding a curl dependency. HTTP failure causes a nonzero check exit. Health proves service response, not RAG correctness or automatic recovery. |
| 19 | JSON-array command starts Streamlit. `0.0.0.0` listens on container interfaces; host publication is controlled by `docker run -p`. Port is 8501, headless mode avoids launching a browser, and telemetry is disabled. |

## 16. Ignore files

`.dockerignore`:

- Line 1 explains the policy.
- Line 2 excludes everything from the build context by default.
- Lines 3, 4 and 5 re-include `app.py`, `core.py` and `requirements.txt` respectively. Leading `!` means an exception to the exclusion rule.
- Line 6 allows the `data` parent directory; line 7 allows just its source JSON file.
- Lines 8–9 retain the build instructions and ignore rules.

Thus `.venv`, private `.env` files, tests, docs and unrelated workspace files do not belong in the image context.

`.gitignore` (applies to the project Git repository):

| Lines | Explanation |
|---|---|
| 1–2 | Ignore `.env` and its variants to reduce accidental secret commits. |
| 3 | Keep the safe placeholder example as an exception. |
| 4, 5, 6 | Ignore virtual-environment folders named `.venv`, `venv`, or `env`. |
| 7 | Ignore Python's bytecode-cache directories. |
| 8 | Ignore filenames ending `.pyc`, `.pyo`, or `.pyd`; brackets express a character choice. |
| 9 | Ignore pytest's cache if that runner is added later. |
| 10 | Ignore mypy's type-check cache. |
| 11 | Ignore Ruff's lint cache. |
| 12–13 | Ignore coverage data and generated HTML reports. |
| 14 | Ignore Streamlit's local secret configuration. |
| 15 | Ignore log files. |
| 16–17 | Ignore macOS and Windows folder metadata respectively. |

Ignore patterns do not encrypt files or remove already-tracked secrets. Never place private memory or credentials in repository files.

## 17. `test_core.py`, statement by statement

Tests use `unittest`, which ships with Python. A test passes when its assertions hold; failing assertions describe a regression. Mocks replace network operations with controlled fake values, so these tests do not spend API money or establish that a real model works.

| Lines | Explanation |
|---|---|
| 1 | Describes the offline testing policy. |
| 2 | JSON-encodes simulated responses. |
| 3 | Accesses the environment so tests can temporarily replace it. |
| 4 | Imports the test runner and assertions. |
| 5 | Builds the corpus path relative to the test file. |
| 6 | Imports fake objects and temporary patching tools. |
| 8 | Imports the module under test. |
| 11 | Creates a test class inheriting unittest assertions and lifecycle. |
| 12–13 | Before each test, load a fresh copy of the bundled corpus. `self` refers to this test instance. |
| 15–16 | First test requires exactly three starter records. Update this intentional expectation if the corpus grows. |
| 17 | Runs a tracking-related query. |
| 18 | Requires the process source to rank first. |
| 19 | Requires a positive match score. |
| 21–22 | Unknown vocabulary should produce no hits. |
| 23 | A zero limit should produce no hits. |
| 24 | An empty corpus should produce no hits. |
| 26–27 | Creates a foreign-country copy, preserving all other fields. |
| 28 | Requires country filtering to exclude it. This does not test interpretation of a user's own jurisdiction. |
| 30–31 | Iterates over blank and unrelated questions. |
| 32 | Labels each case separately in failure reports. |
| 33 | Requires no source evidence for those cases. |
| 34 | Repeats text 400 times to exceed the limit. |
| 35 | Requires a truncation notice. |
| 37–38 | Asks a question requesting a guaranteed outcome. |
| 39 | Requires evidence mode by default. |
| 40–41 | Requires explicit summary and corpus-limit wording. |
| 42 | Requires at least one starter-source citation. |
| 43 | Verifies an empty corpus does not fabricate references. |
| 45–46 | Temporarily clears environment variables for a deterministic missing-configuration test. They are restored after the block. |
| 47 | Requests AI without configuration. |
| 48–49 | Requires evidence fallback and an explanatory warning. |
| 51–52 | Supplies fake configuration during the failure test. These strings are not real credentials. |
| 53 | Replaces the AI helper with one that raises TimeoutError. |
| 54 | Runs the public answer function against that simulated failure. |
| 55–56 | Requires local fallback and a generic warning. |
| 57 | Checks the fake credential text is absent from that warning. |
| 59 | Defines a helper constructing simulated API responses; default completion status is `stop`. |
| 60 | Creates a fake response object. |
| 61–63 | Defines what reading it inside a `with` block returns: JSON bytes matching the API response structure. |
| 64–65 | Makes a fake opener return that response. |
| 66 | Returns a patch context that replaces the actual opener builder. |
| 68–69 | Supplies generated text with one allowed citation. |
| 70 | Calls the internal validation/request helper, but the opener is mocked so there is no network request. |
| 71 | Requires the valid citation to survive. |
| 73–74 | Enumerates absent, invented, URL-containing and malformed citation outputs. `evil.test` is inert fixture text, not a visited URL. |
| 75 | Labels each case and installs its simulated response. |
| 76–77 | Requires each invalid output to raise ValueError. |
| 78 | Simulates a completion stopped by a length limit. |
| 79–80 | Requires rejection even though its citation ID exists. |
| 82–83 | Makes file reading return invalid JSON without changing a real file. |
| 84 | Requires safe empty output. |
| 85 | Simulates an invalid record followed by a valid record and its duplicate. |
| 86 | Requires exactly one accepted record. |
| 88–89 | Creates a local letter using fictional input. |
| 90–91 | Requires retailer and issue text to appear. |
| 92 | Requires the order-number placeholder instead of an invented identifier. |
| 93 | Requires the draft-only warning. |
| 96–97 | Runs unittest when the file is executed directly; importing it does not trigger this block. |

## 18. `test_app.py`, statement by statement

| Lines | Explanation |
|---|---|
| 1 | Explains that the test drives the interface without publishing a server. |
| 2 | Imports unittest. |
| 3 | Imports portable paths. |
| 5 | Imports Streamlit's headless application-test driver. |
| 8–9 | Declares the test class and its end-to-end test method. |
| 10 | Loads and runs the actual app script. |
| 11 | Requires startup without an application exception. |
| 12 | Fills the first text area with a generic complaint question. Widget indexing is zero-based. |
| 13 | Clicks the first submit button and reruns the app. |
| 14 | Requires no exception after submission. |
| 15 | Checks that the stored answer contains a source citation. |
| 16 | Requires default evidence mode, so the UI test makes no provider call. |
| 17 | Fills the retailer input with a fictional name. |
| 18 | Fills the second text area with a generic issue. |
| 19 | Clicks the second form's button and reruns. |
| 20 | Requires no exception after drafting. |
| 21 | Requires the business name in the editable draft state. |
| 22 | Requires the draft-only warning. |
| 25–26 | Enables direct execution with unittest. |

These are regression and interface checks, not a complete quality, privacy or security evaluation. In particular, real-model accuracy, live provider access, browser layout, cloud hosting, load handling, and claim-by-claim source support require separate validation.

## 19. Suggested learning order

1. Run evidence mode and inspect the three JSON records.
2. Follow a question through `_tokens`, `retrieve`, `_evidence` and `answer_question`.
3. Change a fictional test question and rerun the tests.
4. Read the Streamlit form/state code and test drafting.
5. Understand the provider data transfer before configuring optional AI.
6. Run the container and compare its behavior with the virtual-environment run.
7. Only then expand the corpus, evaluations, deployment protections and retrieval sophistication.
