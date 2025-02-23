import threading
import itertools
import time
import sys
import anthropic

class ProgressTracker:
    def __init__(self):
        self.done = False
        self.elapsed_time = 0
        self.spinner_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        self.response_text = ""
        self.printed_chars = 0

    def start(self):
        """Start the progress tracking animation"""
        self.done = False
        self.elapsed_time = 0

        # Start spinner and timer thread
        threading.Thread(target=self._animate, daemon=True).start()

    def stop(self):
        """Stop the animation"""
        self.done = True
        # Clear the line and move cursor to start
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()

    def _animate(self):
        """Animate the spinner and timer"""
        spinner = itertools.cycle(self.spinner_chars)
        start_time = time.time()

        while not self.done:
            self.elapsed_time = int(time.time() - start_time)
            spinner_char = next(spinner)
            sys.stdout.write(
                f'\rClaude is thinking {spinner_char} {self.elapsed_time}s')
            sys.stdout.flush()
            time.sleep(0.1)


def render_text_smoothly(text: str, delay: float = 0.002):
    """Render text with a smooth typing animation"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write('\n')

# Modified stream_response function to use the progress tracker


async def stream_response(client: anthropic.Anthropic, messages: list, model: str, max_tokens: int) -> str:
    """Stream the response from Claude and return the full response text."""
    full_response = []
    tracker = ProgressTracker()
    tracker.start()

    try:
        with client.messages.stream(
            messages=messages,
            model=model,
            max_tokens=max_tokens
        ) as stream:
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    text = chunk.delta.text
                    full_response.append(text)
                    render_text_smoothly(
                        text[tracker.printed_chars:], delay=0.001)
                    tracker.printed_chars = len(text)
    finally:
        tracker.stop()

    return "".join(full_response)
