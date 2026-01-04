#!/usr/bin/env python3
"""
Karumi Onboarding Tool
CLI tool that scrapes websites and generates persona + playbook YAML files.

Usage:
    python main.py <url> --company <company_name>
    
Example:
    python main.py https://healing-path.vercel.app/dashboard --company "HealingPath"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from scraper import scrape_website
from generator import generate_yamls


def main():
    """Main entry point for the CLI."""
    
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate Karumi persona and playbook YAML from a website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://myapp.com/dashboard --company "MyApp"
  python main.py https://example.com --company "Example" --max-pages 5
  
The tool will:
  1. Scrape the website using Playwright
  2. Extract all visible text and navigation elements
  3. Use GPT-4 to generate persona and playbook YAML files
  4. Save them to the output/ folder
"""
    )
    
    parser.add_argument(
        "url",
        help="The URL to start scraping from (usually the main dashboard or landing page)"
    )
    
    parser.add_argument(
        "--company", "-c",
        required=True,
        help="Company name (used for file naming and persona)"
    )
    
    parser.add_argument(
        "--openai-key", "-k",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=10,
        help="Maximum number of pages to scrape (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory for YAML files (default: output/)"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.openai_key:
        print("❌ Error: OpenAI API key required")
        print("   Set OPENAI_API_KEY environment variable or use --openai-key flag")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate clean company ID for filenames
    company_id = args.company.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🚀 Karumi Onboarding Tool                     ║
╠══════════════════════════════════════════════════════════════════╣
║  URL:     {args.url[:50]:<50} ║
║  Company: {args.company:<50} ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Scrape the website
    print("🔍 Step 1: Scraping website...")
    try:
        scraped_data = asyncio.run(scrape_website(args.url, args.max_pages))
    except Exception as e:
        print(f"❌ Failed to scrape website: {e}")
        sys.exit(1)
    
    pages_count = len(scraped_data.get('pages', []))
    if pages_count == 0:
        print("❌ No pages could be scraped. The website might require authentication.")
        sys.exit(1)
    
    # Count clickables
    total_clickables = sum(
        len(p.get('clickables', [])) 
        for p in scraped_data.get('pages', [])
    )
    
    print(f"   ✅ Found {pages_count} pages, {total_clickables} clickable elements")
    
    # Step 2: Generate YAML files
    print("\n🤖 Step 2: Generating YAML with GPT-4...")
    try:
        persona_yaml, playbook_yaml = generate_yamls(
            scraped_data, 
            args.company, 
            args.openai_key
        )
    except Exception as e:
        print(f"❌ Failed to generate YAML: {e}")
        sys.exit(1)
    
    # Step 3: Save files
    print("\n💾 Step 3: Saving files...")
    
    persona_path = output_dir / f"persona_{company_id}.yaml"
    playbook_path = output_dir / f"{company_id}_playbook.yaml"
    
    with open(persona_path, 'w') as f:
        f.write(persona_yaml)
    print(f"   ✅ Saved: {persona_path}")
    
    with open(playbook_path, 'w') as f:
        f.write(playbook_yaml)
    print(f"   ✅ Saved: {playbook_path}")
    
    # Success message
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                         ✨ Complete!                             ║
╠══════════════════════════════════════════════════════════════════╣
║  Generated files:                                                ║
║    📄 {str(persona_path):<55} ║
║    📄 {str(playbook_path):<55} ║
╠══════════════════════════════════════════════════════════════════╣
║  Next steps:                                                     ║
║    1. Review and tweak the generated YAML files                  ║
║    2. Copy them to your Karumi backend:                          ║
║                                                                  ║
║    cp {str(persona_path)} ../Karumi/backend/app/personas/       ║
║    cp {str(playbook_path)} ../Karumi/backend/app/playbooks/     ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()

