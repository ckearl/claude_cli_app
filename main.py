#!/usr/bin/env python3
import anthropic
import argparse
from termcolor import colored
from auth import get_api_key
from model_selector import ModelSelector
from conversation import ConversationManager
from text_formatter import TextFormatter
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


def call_anthropic_api(prompt: str, args, api_key: str) -> None:
    client = anthropic.Anthropic(api_key=api_key)
    model = ModelSelector.select_model(prompt, args)
    formatter = TextFormatter()

    try:
        modified_prompt = ModelSelector.modify_prompt(
            prompt, args.concise, args.short)
        messages = [{"role": "user", "content": modified_prompt}]
        conversation = ConversationManager(client, messages)

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
        formatted_text = formatter.enhance_text_formatting(response_text)
        formatted_text = formatter.highlight_code_blocks(formatted_text)
        render_text_smoothly(formatted_text)

        messages.append({"role": "assistant", "content": response_text})
        print("=" * 50 + "\n")

        should_continue = input(
            colored("Would you like to continue the conversation? (y/n): ", "yellow"))
        if should_continue.lower() == 'y':
            conversation.handle_conversation(
                model, args.max_tokens, args.concise, args.short)

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
