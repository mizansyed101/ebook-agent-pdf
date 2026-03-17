import os
import re
import json
import uuid
from flask import Flask, render_template, request, Response, send_file, jsonify

# LLM SDKs
import google.generativeai as genai

from scripts.convert_to_pdf import create_pdf

app = Flask(__name__)

# Directory to store generated ebooks
# On Vercel, we MUST use /tmp as the rest of the filesystem is read-only
if os.environ.get('VERCEL'):
    OUTPUT_DIR = "/tmp"
else:
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# LLM PROVIDER ABSTRACTION
# ============================================================

PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-pro-exp"],
        "placeholder": "Enter your Google Gemini API key",
        "api_key_url": "https://aistudio.google.com/app/apikey"
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "placeholder": "Enter your OpenAI API key (sk-...)",
        "api_key_url": "https://platform.openai.com/api-keys"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "placeholder": "Enter your Anthropic API key (sk-ant-...)",
        "api_key_url": "https://console.anthropic.com/settings/keys"
    },
    "groq": {
        "name": "Groq",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b", "gemma2-9b-it"],
        "placeholder": "Enter your Groq API key (gsk_...)",
        "api_key_url": "https://console.groq.com/keys"
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free", "deepseek/deepseek-r1:free", "deepseek/deepseek-chat", "anthropic/claude-3.5-sonnet", "openai/o3-mini"],
        "placeholder": "Enter your OpenRouter API key (sk-or-...)",
        "api_key_url": "https://openrouter.ai/keys"
    }
}


def call_llm(provider, api_key, model, prompt):
    """
    Unified LLM call interface. Returns the generated text.
    """
    if provider == "gemini":
        return _call_gemini(api_key, model, prompt)
    elif provider == "openai":
        return _call_openai(api_key, model, prompt)
    elif provider == "anthropic":
        return _call_anthropic(api_key, model, prompt)
    elif provider == "groq":
        return _call_groq(api_key, model, prompt)
    elif provider == "openrouter":
        return _call_openrouter(api_key, model, prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _call_gemini(api_key, model, prompt):
    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model)
    response = gen_model.generate_content(prompt)
    return response.text


def _call_openai(api_key, model, prompt):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content


def _call_anthropic(api_key, model, prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def _call_groq(api_key, model, prompt):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content


def _call_openrouter(api_key, model, prompt):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content


# ============================================================
# CONTENT GENERATION
# ============================================================

def generate_outline(provider, api_key, model, topic):
    """Phase 1: Generate a detailed eBook outline."""
    prompt = f"""You are an expert eBook architect. Create a detailed outline for an eBook on the topic: "{topic}"

Requirements:
- Introduction with a compelling hook  
- 10 depth-focused chapters, each with a clear psychological or functional angle
- Conclusion that ties everything together
- Each chapter should have a title and 3-4 bullet points describing what it covers

Format your response EXACTLY like this (no extra text before or after):

# [Book Title]

## Introduction: [Subtitle]
- [point 1]
- [point 2]
- [point 3]

## Chapter 1: [Title]
- [point 1]
- [point 2]
- [point 3]

(continue for all 10 chapters)

## Conclusion: [Title]
- [point 1]
- [point 2]
- [point 3]
"""
    return call_llm(provider, api_key, model, prompt)


def generate_chapter(provider, api_key, model, topic, book_title, chapter_info, chapter_num, total_chapters):
    """Phase 2: Generate a single chapter."""
    if chapter_num == 0:
        chapter_type = "Introduction"
    elif chapter_num == total_chapters - 1:
        chapter_type = "Conclusion"
    else:
        chapter_type = f"Chapter {chapter_num}"

    prompt = f"""You are an expert author writing an eBook titled "{book_title}" on the topic "{topic}".

Write {chapter_type} with the following outline:
{chapter_info}

Requirements:
- Minimum 500 words
- Professional, engaging, and authoritative tone
- Use Markdown formatting: ## for the chapter title, ### for subsections
- Include 2-3 subsections with ### headers
- Make it insightful with real examples or thought experiments
- Do NOT use any Unicode smart quotes or em-dashes. Use straight quotes (" and ') and double hyphens (--) only.
- Do NOT include any text before the ## chapter title
- End the chapter content naturally (do NOT add --- separators)

Write the chapter now:"""

    return call_llm(provider, api_key, model, prompt)


def parse_outline_sections(outline_text):
    """Parse the outline into individual chapter sections."""
    sections = []
    current_section = []
    
    for line in outline_text.strip().split('\n'):
        if line.startswith('## '):
            if current_section:
                sections.append('\n'.join(current_section))
            current_section = [line]
        elif line.startswith('# '):
            continue
        else:
            current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections


def extract_book_title(outline_text):
    """Extract the book title from the outline."""
    for line in outline_text.strip().split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled eBook"


def sanitize_content(content):
    """Replace Unicode characters with ASCII equivalents."""
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2014': '--', '\u2013': '-',
        '\u2026': '...',
        '\u00a0': ' ',
        '\u2022': '-',
        '\u00e9': 'e', '\u00e8': 'e',
        '\u00e0': 'a',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    content = content.encode('ascii', 'ignore').decode('ascii')
    return content


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html', providers=PROVIDERS)


@app.route('/api/providers')
def get_providers():
    """Return available providers and their models."""
    return jsonify(PROVIDERS)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get('topic', '').strip()
    api_key = data.get('api_key', '').strip()
    provider = data.get('provider', 'gemini').strip()
    model = data.get('model', '').strip()

    if not topic:
        return jsonify({'error': 'Please provide a topic'}), 400
    if not api_key:
        return jsonify({'error': 'Please provide an API key'}), 400
    if provider not in PROVIDERS:
        return jsonify({'error': f'Unknown provider: {provider}'}), 400

    # Default to first model if none specified
    if not model:
        model = PROVIDERS[provider]['models'][0]

    def stream():
        try:
            job_id = str(uuid.uuid4())[:8]
            safe_name = sanitize_filename(topic)

            # Phase 1: Generate Outline
            provider_name = PROVIDERS[provider]["name"]
            yield f"data: {json.dumps({'phase': 'outline', 'status': 'generating', 'message': 'Generating outline via ' + provider_name + '...'})}\n\n"
            
            outline = generate_outline(provider, api_key, model, topic)
            book_title = extract_book_title(outline)
            sections = parse_outline_sections(outline)

            yield f"data: {json.dumps({'phase': 'outline', 'status': 'done', 'message': f'Outline ready: {len(sections)} sections', 'title': book_title, 'total': len(sections)})}\n\n"

            # Phase 2: Generate Chapters
            full_content = f"# {book_title}\n\n"
            
            for i, section_outline in enumerate(sections):
                section_title = section_outline.split('\n')[0].replace('## ', '')
                yield f"data: {json.dumps({'phase': 'writing', 'status': 'generating', 'message': f'Writing: {section_title}', 'current': i + 1, 'total': len(sections)})}\n\n"

                chapter_text = generate_chapter(
                    provider, api_key, model, topic, book_title, section_outline, i, len(sections)
                )
                chapter_text = sanitize_content(chapter_text)
                
                # Clean up markdown code fences from AI
                chapter_text = chapter_text.strip()
                if chapter_text.startswith('```'):
                    lines = chapter_text.split('\n')
                    chapter_text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

                full_content += chapter_text + "\n\n---\n\n"
                
                yield f"data: {json.dumps({'phase': 'writing', 'status': 'done', 'message': f'Completed: {section_title}', 'current': i + 1, 'total': len(sections)})}\n\n"

            # Phase 3: Save Markdown
            md_path = os.path.join(OUTPUT_DIR, f"{safe_name}_{job_id}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            # Phase 4: Convert to PDF
            yield f"data: {json.dumps({'phase': 'pdf', 'status': 'generating', 'message': 'Converting to PDF...'})}\n\n"

            pdf_filename = f"{safe_name}_{job_id}.pdf"
            pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
            
            create_pdf(md_path, pdf_path, book_title)

            yield f"data: {json.dumps({'phase': 'pdf', 'status': 'done', 'message': 'PDF ready!', 'filename': pdf_filename})}\n\n"

            # Done
            yield f"data: {json.dumps({'phase': 'complete', 'status': 'done', 'message': 'eBook generated successfully!', 'filename': pdf_filename, 'title': book_title})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'phase': 'error', 'status': 'error', 'message': str(e)})}\n\n"

    return Response(stream(), mimetype='text/event-stream')


@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({'error': 'File not found'}), 404


def sanitize_filename(topic):
    """Convert topic to a safe filename."""
    clean = re.sub(r'[^\w\s-]', '', topic).strip()
    clean = re.sub(r'[\s-]+', '_', clean)
    return clean[:60]


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
