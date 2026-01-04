"""
YAML Generator Module
Uses GPT-4 to generate persona and playbook YAML files from scraped website data.
"""

import yaml
import re
from typing import Dict, Tuple, Optional
from openai import OpenAI


class YAMLGenerator:
    """Generates persona and playbook YAML from scraped website data."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, scraped_data: Dict, company_name: str) -> Tuple[str, str]:
        """
        Generate persona and playbook YAML files.
        
        Returns:
            Tuple of (persona_yaml, playbook_yaml)
        """
        # Build the content from all pages
        pages_content = self._format_pages_content(scraped_data)
        
        # Generate both YAMLs in one call for better context
        prompt = self._build_prompt(pages_content, company_name, scraped_data['home_url'])
        
        print("🤖 Generating YAML with GPT-4...")
        
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing websites and creating configuration files for AI sales demo agents. 
You output ONLY valid YAML with no additional explanation or markdown formatting.
You're great at inferring product features, navigation structure, and brand voice from website content.

CRITICAL YAML SYNTAX RULES:
- For dictionary keys, ALWAYS include a colon after the key name
- Example for screens section:
  screens:
    dashboard:      # ← colon required after screen ID
      name: "Dashboard"
    features:       # ← colon required after screen ID  
      name: "Features"
- NEVER write a dict key without a colon - this breaks YAML parsing entirely"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=8000
        )
        
        content = response.choices[0].message.content
        
        # Parse the response to extract the two YAML sections
        persona_yaml, playbook_yaml = self._parse_response(content, company_name, scraped_data['home_url'])
        
        return persona_yaml, playbook_yaml
    
    def _format_pages_content(self, scraped_data: Dict) -> str:
        """Format all scraped pages into a single string for the LLM."""
        parts = []
        
        for i, page in enumerate(scraped_data.get('pages', []), 1):
            url = page.get('url', 'Unknown URL')
            title = page.get('title', 'Untitled')
            text = page.get('text', '')
            
            # Get clickable elements
            clickables = page.get('clickables', [])
            buttons = [c['text'] for c in clickables if c.get('type') == 'button']
            links = [c['text'] for c in clickables if c.get('type') == 'link']
            
            tab_info = f" (Tab: {page.get('tab_name')})" if page.get('is_tab') else ""
            
            part = f"""
=== PAGE {i}{tab_info} ===
URL: {url}
Title: {title}

BUTTONS/CLICKABLES: {', '.join(buttons[:20]) if buttons else 'None found'}

LINKS: {', '.join(links[:15]) if links else 'None found'}

PAGE CONTENT:
{text[:8000]}
"""
            parts.append(part)
        
        return "\n".join(parts)
    
    def _build_prompt(self, pages_content: str, company_name: str, home_url: str) -> str:
        """Build the prompt for GPT-4."""
        
        company_id = company_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        return f"""I scraped a website for a product/company called "{company_name}". 
Here's the raw text content from each page I found:

{pages_content}

---

Based on this website content, generate TWO YAML configuration files for an AI sales demo agent.

**FILE 1: PERSONA YAML**
This defines the AI agent's personality and knowledge about the product.

Required fields:
- name: A friendly first name that matches the brand vibe (e.g., "Maya", "Alex", "Jordan")
- company: "{company_name}"
- role: A role that fits the product (e.g., "Product Guide", "Success Coach")
- tone: Describe the voice style inferred from the website copy
- speaking_style: How the AI should talk (conversational, professional, etc.)
- greeting_template: A welcome message using {{user_name}} placeholder that MUST offer a demo/tour. Example: "Hey {{user_name}}! I'm [name]. Do you want me to give you a quick tour of [product]?" This is critical - the greeting must invite the user to take a tour so they can respond "Sure" or "Yes" to trigger the demo.
- product_name: The actual product name from the website
- product_description: 2-3 sentence summary of what the product does
- key_features: List of 5-7 main features
- value_propositions: List of 3-5 benefits/outcomes
- demo_intro: Opening line for starting a demo
- demo_outro: Closing line after demo
- home_url: "{home_url}"
- home_page_description: Detailed description of what the main page looks like
- site_map: List of sections with:
  - section: section_id
  - keywords: list of related words
  - description: what this section contains
  - button_text: the actual button/link text to click
- screens: Dict of screen IDs with:
  - name: Display name
  - description: What appears on this screen
  - purpose: Why users would go here
  - key_actions: List of main buttons/actions
- closing:
  - founder_name: "Founder" (placeholder)
  - calendly_url: "" (empty placeholder)
  - closing_message: A friendly closing message

**FILE 2: PLAYBOOK YAML**
This defines the demo flow - which screens to visit and what to say.

CRITICAL PLAYBOOK RULES:
- ONLY use button text and navigation items that you saw in the scraped content above
- Do NOT invent or guess button names - use EXACT text from the BUTTONS/CLICKABLES lists
- Create an engaging demo flow: start with a warm welcome, build excitement through key features, end with a compelling close
- Each step should have a clear purpose and smooth transition to the next
- The narrate_intent should highlight value and benefits, not just describe what's on screen

Required structure:
meta:
  company_id: "persona_{company_id}"
  name: "Full {company_name} Demo"
  description: Brief description of the demo
  estimated_duration: "2-3 minutes"
  start_url: "{home_url}"

triggers:
  - "give me a demo"
  - "show me everything"
  - "full tour"
  - "walk me through"

steps:
  - id: unique_step_id
    screen: screen_id_from_persona
    action:
      type: "click" or "navigate" or "scroll"
      target: "Exact Button Text" or URL
    narrate_intent: what the AI should explain at this step

fallback_narration:
  action_failed: "Hmm, that didn't work. Let me try another way."
  element_not_found: "I'm having trouble finding that. Let me describe it instead."
  demo_interrupted: "Got it — I'll pause here. What would you like to know?"

---

IMPORTANT FORMATTING RULES:
1. Output the persona YAML first, then the playbook YAML
2. Separate them with a line containing only: ---SPLIT---
3. Output ONLY valid YAML - no markdown code blocks, no explanations
4. ONLY use button/link text that appears in the scraped BUTTONS/CLICKABLES lists - never invent button names
5. Create an amazing demo flow: hook them with value upfront, show 3-5 killer features, end with a call to action
6. The persona should match the brand voice from the website copy
7. Each playbook step should feel like a natural conversation, not a feature list

OUTPUT FORMAT:
[persona yaml content here]
---SPLIT---
[playbook yaml content here]
"""

    def _parse_response(self, content: str, company_name: str, home_url: str) -> Tuple[str, str]:
        """Parse the LLM response to extract persona and playbook YAML."""
        
        # Try to split by the marker
        if '---SPLIT---' in content:
            parts = content.split('---SPLIT---')
            persona_yaml = parts[0].strip()
            playbook_yaml = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Try to find the split by looking for 'meta:' which starts the playbook
            match = re.search(r'\n(meta:\s*\n\s+company_id:)', content)
            if match:
                split_pos = match.start()
                persona_yaml = content[:split_pos].strip()
                playbook_yaml = content[split_pos:].strip()
            else:
                # Fallback: return all as persona, empty playbook
                persona_yaml = content.strip()
                playbook_yaml = self._generate_fallback_playbook(company_name, home_url)
        
        # Clean up any markdown code blocks
        persona_yaml = self._clean_yaml(persona_yaml)
        playbook_yaml = self._clean_yaml(playbook_yaml)
        
        # Validate YAML
        try:
            yaml.safe_load(persona_yaml)
        except yaml.YAMLError as e:
            print(f"⚠️  Warning: Persona YAML may have issues: {e}")
        
        try:
            yaml.safe_load(playbook_yaml)
        except yaml.YAMLError as e:
            print(f"⚠️  Warning: Playbook YAML may have issues: {e}")
        
        return persona_yaml, playbook_yaml
    
    def _clean_yaml(self, content: str) -> str:
        """Remove markdown formatting from YAML content."""
        # Remove ```yaml and ``` markers
        content = re.sub(r'^```ya?ml?\s*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
        content = content.strip()
        return content
    
    def _generate_fallback_playbook(self, company_name: str, home_url: str) -> str:
        """Generate a minimal playbook if parsing fails."""
        company_id = company_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        return f"""meta:
  company_id: "persona_{company_id}"
  name: "Full {company_name} Demo"
  description: "Walk through the core features"
  estimated_duration: "2-3 minutes"
  start_url: "{home_url}"

triggers:
  - "give me a demo"
  - "show me everything"
  - "full tour"

steps:
  - id: "intro"
    screen: "dashboard"
    narrate_intent: "welcome the user and introduce the product"

  - id: "closing"
    narrate_intent: "wrap up and ask if they have questions"

fallback_narration:
  action_failed: "Hmm, that didn't work. Let me try another way."
  element_not_found: "I'm having trouble finding that. Let me describe it instead."
  demo_interrupted: "Got it — I'll pause here. What would you like to know?"
"""


def generate_yamls(scraped_data: Dict, company_name: str, api_key: str) -> Tuple[str, str]:
    """Convenience function to generate YAML files."""
    generator = YAMLGenerator(api_key)
    return generator.generate(scraped_data, company_name)

