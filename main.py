#!/usr/bin/env python3
import anthropic
import argparse
import os
from typing import Optional
from termcolor import colored
import re
from datetime import datetime as dt
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound
from auth import get_api_key
from progress_tracker import ProgressTracker, render_text_smoothly


def setup_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Call Anthropic API with a prompt')
    parser.add_argument('prompt', type=str,
                        help='The prompt to send to Claude')
    parser.add_argument('-c', '--concise', action='store_true',
                        help='Format the response as an ordered list')
    parser.add_argument('-s', '--short', action='store_true',
                        help='Request a short response (paragraph or less)')
    parser.add_argument('--model', type=str,
                        help='The model to use (auto-selected based on query)')
    parser.add_argument('--max-tokens', type=int, default=1000,
                        help='Maximum number of tokens in response (default: 1000)')
    return parser


def select_model(prompt: str, args) -> str:
    """Select the most appropriate model based on the query and flags."""
    if args.model:  # If user explicitly specified a model, use that
        return args.model

    # Use Haiku for short/simple queries
    if args.short or len(prompt.split()) < 20:
        return 'claude-3-haiku-20240307'
    
    # Default to Sonnet for medium complexity
    return 'claude-3-sonnet-20240229'


def modify_prompt(prompt: str, concise: bool, short: bool) -> str:
    modifications = []

    if concise:
        modifications.append("Please format your response as a numbered list.")

    if short:
        modifications.append(
            "Please keep your response to one paragraph or less.")

    if modifications:
        prompt = prompt + "\n\nAdditional instructions: " + \
            " ".join(modifications)

    return prompt


def highlight_code_blocks(text: str) -> str:
    """Highlight code blocks in the text using Pygments."""
    pattern = r"```(\w+)?\n(.*?)\n```"

    def replace_code_block(match):
        language = match.group(1) or ''
        code = match.group(2)

        try:
            if language:
                lexer = get_lexer_by_name(language)
            else:
                lexer = guess_lexer(code)
            return "\n" + highlight(code, lexer, TerminalFormatter()) + "\n"
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
                return "\n" + highlight(code, lexer, TerminalFormatter()) + "\n"
            except ClassNotFound:
                return "\n" + code + "\n"

    return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)


def get_conversation_summary(client: anthropic.Anthropic, messages: list) -> str:
    """Get a three word summary of the conversation using Claude."""
    try:
        summary_prompt = {
            "role": "user",
            "content": "Please provide a three-word summary of this conversation. Use hyphens between words and only alphanumeric characters. Example format: useful-python-discussion"
        }

        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Use faster model for summary
            max_tokens=30,
            messages=messages + [summary_prompt]
        )

        summary = response.content[0].text.strip().lower()
        words = [word for word in summary.split('-') if word][:3]
        return '-'.join(words)
    except Exception as e:
        print(f"Error getting summary: {e}")
        return "general-chat-log"


def save_conversation(client: anthropic.Anthropic, messages: list) -> None:
    """Save the conversation to a file in the history folder."""
    try:
        os.makedirs('history', exist_ok=True)

        summary = get_conversation_summary(client, messages)
        timestamp = dt.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = f"history/{timestamp}-{summary}.txt"

        content = []
        for msg in messages:
            role = "You" if msg["role"] == "user" else "Claude"
            content.append(f"{role}: {msg['content']}\n")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        print(colored(f"\nConversation saved to: {filename}", "green"))
    except Exception as e:
        print(colored(f"\nError saving conversation: {e}", "red"))


def handle_conversation(client: anthropic.Anthropic, messages: list, model: str, max_tokens: int, concise: bool, short: bool) -> None:
    print(colored("\nConversation started. Enter 'exit' or 'quit' at any time to end the conversation.", "white"))

    while True:
        user_input = input(colored("\nYou: ", "blue", attrs=["bold"]))

        if user_input.lower() in ['exit', 'quit']:
            print(colored("\nEnding conversation.", "yellow"))
            save_prompt = input(
                colored("Do you want to save this conversation? (y/n): ", "yellow"))
            if save_prompt.lower() == 'y':
                save_conversation(client, messages)
            print(colored("Goodbye!", "yellow"))
            break

        modified_input = modify_prompt(user_input, concise, short)
        messages.append({"role": "user", "content": user_input})

        try:
            print("\n" + "=" * 50)
            print(colored("CLAUDE'S RESPONSE", "green", attrs=[
                  "bold"]) + colored(":", "white") + "\n")

            # Use progress tracking for the response
            tracker = ProgressTracker()
            tracker.start()

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages
            )

            tracker.stop()
            response_text = response.content[0].text

            # Apply formatting and render smoothly
            formatted_text = enhance_text_formatting(response_text)
            formatted_text = highlight_code_blocks(formatted_text)
            render_text_smoothly(formatted_text)

            messages.append({"role": "assistant", "content": response_text})
            print("=" * 50)

        except Exception as e:
            print(f"Error: {e}")
            break

def enhance_text_formatting(text: str) -> str:
    """Enhance text with additional formatting while preserving code blocks."""
    # First find all code blocks and replace them with placeholders
    code_blocks = {}
    placeholder_pattern = 'CODE_BLOCK_PLACEHOLDER_{}'
    triple_code_pattern = r'```(?:\w+)?\n.*?\n```'

    def store_code_block(match):
        placeholder = placeholder_pattern.format(len(code_blocks))
        code_blocks[placeholder] = match.group(0)
        return placeholder

    text = re.sub(triple_code_pattern, store_code_block, text, flags=re.DOTALL)

    # Handle lists first (before other inline formatting)
    # Numbered lists
    number_pattern = r'^(\s*)(\d+\.)(\s+)(.+)$'

    def number_replace(match):
        indent, number, spacing, content = match.groups()
        return f"{indent}{colored(number, 'yellow', attrs=['bold'])}{spacing}{colored(content, 'white')}"
    text = re.sub(number_pattern, number_replace, text, flags=re.MULTILINE)

    # Bullet points
    bullet_pattern = r'^(\s*)[•\-\*](\s+)(.+)$'

    def bullet_replace(match):
        indent, spacing, content = match.groups()
        bullet = colored('•', 'yellow')
        return f"{indent}{colored(bullet, 'yellow', attrs=['bold'])}{spacing}{colored(content, 'white')}"
    text = re.sub(bullet_pattern, bullet_replace, text, flags=re.MULTILINE)

    # Handle inline code (text wrapped in single backticks)
    inline_code_pattern = r'`([^`]+)`'

    def code_replace(match):
        content = match.group(1)
        return colored(content, 'green', 'on_grey', attrs=['bold'])
    text = re.sub(inline_code_pattern, code_replace, text)

    # Handle bold text
    bold_pattern = r'\*\*([^*]+)\*\*'

    def bold_replace(match):
        content = match.group(1)
        return colored(content, attrs=['bold'])
    text = re.sub(bold_pattern, bold_replace, text)

    # Handle italics
    italic_pattern = r'\*([^*]+)\*'

    def italic_replace(match):
        content = match.group(1)
        return colored(content, attrs=['dark'])
    text = re.sub(italic_pattern, italic_replace, text)

    # Handle URLs
    url_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'

    def url_replace(match):
        text, url = match.group(1), match.group(2)
        return colored(text, 'blue', attrs=['underline'])
    text = re.sub(url_pattern, url_replace, text)

    # Handle headers
    header_pattern = r'^(#{1,6})\s+(.+)$'

    def header_replace(match):
        level = len(match.group(1))
        content = match.group(2)
        return '\n' + colored(content, 'white', attrs=['bold', 'underline']) + '\n'
    text = re.sub(header_pattern, header_replace, text, flags=re.MULTILINE)

    # Restore code blocks
    for placeholder, code_block in code_blocks.items():
        text = text.replace(placeholder, code_block)

    return text


def call_anthropic_api(prompt: str, args, api_key: str) -> None:
    client = anthropic.Anthropic(api_key=api_key)
    model = select_model(prompt, args)

    try:
        modified_prompt = modify_prompt(prompt, args.concise, args.short)
        messages = [{"role": "user", "content": modified_prompt}]

        # Print the prompt section
        print("\n" + "=" * 50)
        print(colored("PROMPT", "blue", attrs=[
              "bold"]) + colored(":", "white") + "\n")
        print(colored(modified_prompt, "white"))
        print("\n" + "=" * 50)
        print(colored("CLAUDE'S RESPONSE", "green", attrs=[
              "bold"]) + colored(":", "white") + "\n")

        # Use progress tracking for the response
        tracker = ProgressTracker()
        tracker.start()

        response = client.messages.create(
            model=model,
            max_tokens=args.max_tokens,
            messages=messages
        )

        tracker.stop()
        response_text = response.content[0].text

        # Apply formatting and render smoothly
        formatted_text = enhance_text_formatting(response_text)
        formatted_text = highlight_code_blocks(formatted_text)
        render_text_smoothly(formatted_text)

        messages.append({"role": "assistant", "content": response_text})
        print("=" * 50 + "\n")

        should_continue = input(
            colored("Would you like to continue the conversation? (y/n): ", "yellow"))
        if should_continue.lower() == 'y':
            handle_conversation(client, messages, model,
                                args.max_tokens, args.concise, args.short)

    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    parser = setup_argument_parser()
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        return

    call_anthropic_api(args.prompt, args, api_key)


if __name__ == "__main__":
    main()
