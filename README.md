# eBook Agent — AI-Powered eBook Generator

A professional web application that autonomously researches, writes, and formats PDF eBooks on any topic.

## 🚀 Features
- **Multi-LLM Support**: Supports Google Gemini, OpenAI, Anthropic Claude, Groq, and OpenRouter.
- **Sequential Content Generation**: Generates 10+ depth-focused chapters using professional authorship prompts.
- **Real-Time Progress**: Live updates via Server-Sent Events (SSE).
- **Premium Design**: Dark-mode glassmorphism UI with animated progress tracking.
- **Dynamic PDF Generation**: Professional title pages, table of contents, and headers/footers.

## 🛠️ Tech Stack
- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML/JS + Custom CSS
- **PDF Engine**: fpdf2
- **APIs**: google-generativeai, openai, anthropic

## 📦 Setup & Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd "EBOOK AGENT MAIN"
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser to `http://localhost:5000`

## 📖 How to Use
1. Enter your eBook topic.
2. Select your preferred AI Provider and Model.
3. Paste your API Key (never stored, used per-session).
4. Click **Generate eBook** and watch your book come to life.
5. Download the final PDF once complete.

## 📄 License
MIT
