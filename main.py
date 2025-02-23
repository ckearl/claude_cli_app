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
    if args.short or args.concise or len(prompt.split()) < 20:
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

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages
            )
            response_text = response.content[0].text
            print(colored(highlight_code_blocks(response_text), "white"))
            messages.append({"role": "assistant", "content": response_text})
            print("=" * 50)

        except Exception as e:
            print(f"Error: {e}")
            break


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

        response = client.messages.create(
            model=model,
            max_tokens=args.max_tokens,
            messages=messages
        )
        response_text = response.content[0].text
        print(colored(highlight_code_blocks(response_text), "white"))
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
