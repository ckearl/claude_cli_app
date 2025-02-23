import os
from datetime import datetime as dt
from termcolor import colored
from text_formatter import TextFormatter
from progress_tracker import ProgressTracker, render_text_smoothly
from model_selector import ModelSelector


class ConversationManager:
    def __init__(self, client, messages=None):
        self.client = client
        self.messages = messages or []
        self.formatter = TextFormatter()

    def handle_conversation(self, model: str, max_tokens: int, concise: bool, short: bool, no_animation: bool = True) -> None:
        print(colored(
            "\nConversation started. Enter 'exit' or 'quit' at any time to end the conversation.", "white"))

        while True:
            user_input = input(colored("\nYou: ", "blue", attrs=["bold"]))

            if user_input.lower() in ['exit', 'quit']:
                print(colored("\nEnding conversation.", "yellow"))
                save_prompt = input(
                    colored("Do you want to save this conversation? (y/n): ", "yellow"))
                if save_prompt.lower() == 'y':
                    self.save_conversation()
                print(colored("Goodbye!", "yellow"))
                break

            self.process_message(
                user_input, model, max_tokens, concise, short, no_animation)

    def process_message(self, user_input: str, model: str, max_tokens: int, concise: bool, short: bool, no_animation: bool) -> None:
        try:
            modified_input = ModelSelector.modify_prompt(
                user_input, concise, short)
            self.messages.append({"role": "user", "content": user_input})

            print("\n" + "=" * 50)
            print(colored("CLAUDE'S RESPONSE", "green", attrs=[
                  "bold"]) + colored(":", "white") + "\n")

            if no_animation:
                tracker = ProgressTracker()
                tracker.start()

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=self.messages
            )

            tracker.stop()
            response_text = response.content[0].text

            # Apply formatting
            formatted_text = self.formatter.enhance_text_formatting(
                response_text)
            formatted_text = self.formatter.highlight_code_blocks(
                formatted_text)
            
            # Render the response
            if no_animation:
                print(formatted_text)
            else:
                render_text_smoothly(formatted_text)

            self.messages.append(
                {"role": "assistant", "content": response_text})
            print("=" * 50)

        except Exception as e:
            print(f"Error: {e}")
            raise

    def get_conversation_summary(self) -> str:
        """Get a three word summary of the conversation using Claude."""
        try:
            summary_prompt = {
                "role": "user",
                "content": "Please provide a three-word summary of this conversation. Use hyphens between words and only alphanumeric characters. Example format: useful-python-discussion"
            }

            response = self.client.messages.create(
                model=ModelSelector.HAIKU,  # Use faster model for summary
                max_tokens=30,
                messages=self.messages + [summary_prompt]
            )

            summary = response.content[0].text.strip().lower()
            words = [word for word in summary.split('-') if word][:3]
            return '-'.join(words)
        except Exception as e:
            print(f"Error getting summary: {e}")
            return "general-chat-log"

    def save_conversation(self) -> None:
        """Save the conversation to a file in the history folder."""
        try:
            os.makedirs('history', exist_ok=True)

            summary = self.get_conversation_summary()
            timestamp = dt.now().strftime("%Y-%m-%d-%H:%M:%S")
            filename = f"history/{timestamp}-{summary}.txt"

            content = []
            for msg in self.messages:
                role = "You" if msg["role"] == "user" else "Claude"
                content.append(f"{role}: {msg['content']}\n")

            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            print(colored(f"\nConversation saved to: {filename}", "green"))
        except Exception as e:
            print(colored(f"\nError saving conversation: {e}", "red"))
