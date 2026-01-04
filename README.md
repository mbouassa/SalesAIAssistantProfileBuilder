# 🚀 Karumi Onboarding Tool

A CLI tool that scrapes any website and automatically generates **persona** and **playbook** YAML files for the [Karumi AI Sales Agent](https://github.com/your-org/karumi).

## What It Does

1. **Scrapes** the target website using Playwright (handles SPAs and dynamic content)
2. **Extracts** all visible text, navigation, buttons, and page structure
3. **Generates** persona + playbook YAML using GPT-4
4. **Outputs** ready-to-use configuration files

Turn hours of manual YAML writing into minutes of automated generation!

## Installation

```bash
# Clone the repo
git clone https://github.com/your-org/karumi-onboarding.git
cd karumi-onboarding

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Usage

### Basic Usage

```bash
python main.py <url> --company "<CompanyName>"
```

### Examples

```bash
# Scrape a dashboard and generate files
python main.py https://healing-path.vercel.app/dashboard --company "HealingPath"

# Limit the number of pages to scrape
python main.py https://myapp.com/dashboard --company "MyApp" --max-pages 5

# Specify output directory
python main.py https://example.com --company "Example" --output-dir ./configs
```

### Environment Variables

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or create a `.env` file:

```
OPENAI_API_KEY=sk-your-key-here
```

Or pass it directly:

```bash
python main.py https://myapp.com --company "MyApp" --openai-key "sk-..."
```

## Output

The tool generates two files in the `output/` folder:

```
output/
├── persona_myapp.yaml      # AI persona configuration
└── myapp_playbook.yaml     # Demo playbook with steps
```

### Persona YAML

Contains the AI agent's identity and product knowledge:

- Name, tone, and speaking style
- Product description and features
- Site map with navigation structure
- Screen descriptions for each page
- Common objections and responses

### Playbook YAML

Contains the demo flow:

- Trigger phrases to start the demo
- Step-by-step navigation through features
- Click targets matching actual button text
- Narration intents for each step

## Integrating with Karumi

After generating the files:

```bash
# Copy to your Karumi backend
cp output/persona_myapp.yaml ../Karumi/backend/app/personas/
cp output/myapp_playbook.yaml ../Karumi/backend/app/playbooks/

# Review and tweak as needed
# The generated files are a great starting point but may need minor adjustments
```

## Options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--company` | `-c` | Company name (required) | - |
| `--openai-key` | `-k` | OpenAI API key | `$OPENAI_API_KEY` |
| `--max-pages` | `-m` | Max pages to scrape | 10 |
| `--output-dir` | `-o` | Output directory | `output/` |

## How It Works

### Step 1: Scrape Website

The scraper uses Playwright to:
- Navigate to the URL and wait for content to load
- Extract all visible text (`document.body.innerText`)
- Find buttons, links, and navigation elements
- Click through main navigation to discover pages
- Handle tabs and dynamic content

### Step 2: Generate YAML

All scraped content is sent to GPT-4 with a structured prompt that:
- Analyzes the brand voice and tone
- Identifies product features and benefits
- Maps the navigation structure
- Creates logical demo flows
- Uses actual button text for click targets

### Step 3: Output Files

The generated YAML is validated and saved, ready to use with Karumi.

## Limitations

- **Auth-protected pages**: The scraper can't access pages behind login. Provide a URL to a publicly accessible page or dashboard.
- **Complex SPAs**: Some single-page apps with heavy client-side routing may not be fully captured.
- **Accuracy**: Generated YAML is a strong starting point but may need human review for edge cases.

## Tips for Best Results

1. **Start with the main dashboard** - Point to where users land after login
2. **Review button names** - Verify the generated click targets match actual UI
3. **Check screen descriptions** - The AI infers from content; adjust if needed
4. **Customize the playbook** - Reorder steps or add additional demo flows

## Development

```bash
# Run tests
pytest tests/

# Test scraper only
python scraper.py https://example.com

# Test with verbose output
python main.py https://example.com --company "Test" -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

