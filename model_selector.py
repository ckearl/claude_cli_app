class ModelSelector:
    HAIKU = 'claude-3-haiku-20240307'
    SONNET = 'claude-3-sonnet-20240229'
    OPUS = 'claude-3-opus-20240229'

    @staticmethod
    def select_model(prompt: str, args) -> str:
        """Select the most appropriate model based on the query and flags."""
        if args.model:  # If user explicitly specified a model, use that
            return args.model

        # Use Haiku for short/simple queries
        if args.short or len(prompt.split()) < 20:
            return ModelSelector.HAIKU

        # Default to Sonnet for medium complexity
        return ModelSelector.SONNET

    @staticmethod
    def modify_prompt(prompt: str, concise: bool, short: bool) -> str:
        """Modify the prompt based on flags."""
        modifications = []

        if concise:
            modifications.append(
                "Please format your response as a numbered list.")

        if short:
            modifications.append(
                "Please keep your response to one paragraph or less.")

        if modifications:
            prompt = prompt + "\n\nAdditional instructions: " + \
                " ".join(modifications)

        return prompt
