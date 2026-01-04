# Sales AI Assistant Profile Builder

**Automatically generate AI sales agent configurations from any website.**

> Turn hours of manual configuration into minutes of automated generation.

---

## Why I Built This

When building AI sales agents, the biggest bottleneck isn't the AI—it's the **onboarding**. Every new customer requires:

- Writing detailed persona files (tone, features, objections)
- Mapping the entire site navigation
- Describing every screen
- Creating demo playbooks with exact button names

This doesn't scale. A single customer onboarding could take hours of manual YAML writing.

**This tool solves that.** Point it at any website, and it generates production-ready configuration files in minutes. The vision is simple: **make AI sales agents accessible to any company, instantly.**

This CLI is a proof of concept. The next step is a full web interface where companies can onboard themselves with zero technical knowledge.

---

## What It Does

```
Website URL  →  Scrape  →  GPT-4  →  Ready-to-use YAML files
```

1. **Scrapes** the website using Playwright (handles SPAs, dynamic content)
2. **Extracts** all text, buttons, navigation, and page structure
3. **Generates** two YAML files via GPT-4:
   - `persona_*.yaml` — AI identity, product knowledge, site map
   - `*_playbook.yaml` — Demo flow with click targets and narration

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/mbouassa/SalesAIAssistantProfileBuilder.git
cd SalesAIAssistantProfileBuilder

pip install -r requirements.txt
playwright install chromium
```

### 2. Set your OpenAI key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 3. Run

```bash
python main.py https://your-app.com/dashboard --company "YourCompany"
```

### 4. Output

```
output/
├── persona_yourcompany.yaml    # AI personality + product knowledge
└── yourcompany_playbook.yaml   # Demo script with navigation steps
```

---

## Example

```bash
python main.py https://notion.so --company "Notion"
```

Generates:
- A persona that understands Notion's features, tone, and navigation
- A playbook that demos the product with real button clicks

---

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--company`, `-c` | Company name (required) | — |
| `--openai-key`, `-k` | OpenAI API key | `$OPENAI_API_KEY` |
| `--max-pages`, `-m` | Max pages to scrape | 10 |
| `--output-dir`, `-o` | Where to save files | `output/` |

---

## How It Works

### Scraping
- Navigates to the URL, waits for full load
- Extracts all visible text from the page
- Finds every button, link, and navigation element
- Clicks through nav items to discover additional pages

### Generation
- Sends all scraped content to GPT-4
- Infers brand voice, features, and site structure
- Creates persona with accurate button names and screen descriptions
- Builds a logical demo flow that uses real UI elements

---

## Limitations

- **Auth-protected pages** — Can't scrape behind login walls
- **Complex SPAs** — Some heavy client-side apps may not fully capture
- **Manual review** — Generated files are 90% there; expect minor tweaks

---

## What's Next

This CLI proves the concept works. The roadmap:

1. **Web interface** — Upload a URL, get YAML files instantly
2. **Self-service onboarding** — Companies configure their own AI agents
3. **Live preview** — See the AI demo before deploying
4. **One-click deploy** — Push to production directly

---

## License

MIT
