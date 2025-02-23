# Claude CLI

A command-line interface for interacting with Claude AI, featuring smart model selection, conversation saving, and rich text formatting.

## Features

- **Smart Model Selection**: Automatically chooses between Claude-3 models based on query complexity
- **Rich Text Formatting**: Syntax highlighting for code blocks, formatted lists, and Markdown support
- **Progress Tracking**: Visual feedback while waiting for responses
- **Conversation Management**: Save conversations with auto-generated summaries
- **Interactive Mode**: Continue conversations with context preservation

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ckearl/claude_cli_app.git
cd claude_cli_app
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

You can add this line to your `.bashrc` or `.bash_profile` to persist the key across sessions.

> [! NOTE]
> You can obtain an API key by signing up at [Anthropic](https://anthropic.com/). Many forums say that you can use the API for free for a limited number of queries, but I wasn't able to figure it out. I ended up depositing $5 into my account and I've made sure to stay within the free tier so I haven't been charged anything.

## Usage

Basic usage:

```bash
python3 claude.py "What is quantum computing?"
```

With flags:

```bash
# Get a short response
python3 claude.py -s "What is quantum computing?"

# Get a concise, numbered list
python3 claude.py -c "List the main features of Python"

# Specify a model
python3 claude.py --model claude-3-opus-20240229 "Explain neural networks"
```

### Available Options

- `-s, --short`: Request a short response (one paragraph or less)
- `-c, --concise`: Format the response as a numbered list
- `--model`: Manually specify the Claude model to use
- `--max-tokens`: Set maximum response length (default: 1000)

### Conversation History

Conversations are automatically saved in the `history` folder with filenames following the format:

```
YYYY-MM-DD-HH:MM:SS-three-word-summary.txt
```

## Requirements

- Python 3.7+
- anthropic
- termcolor
- pygments
