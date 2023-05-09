from dataclasses import dataclass


@dataclass
class Prompt:
    """A prompt for the GPT-3 review task.
    Attributes:
        prompt_prefix (str): The prefix of the prompt.
        prompt_suffix (str): The suffix of the prompt.
        system_message (str): The system message to display.
        examples (list): The examples to include in the message.
    """

    prompt_prefix: str = ""
    prompt_suffix: str = ""
    system_message: str = ""
    examples: list = []
    history: list = []

    def get_messages(self, prompt_contents: str):
        """Get the messages of the prompt.
        Returns:
            list: The messages of the prompt.
        """
        messages = []
        if self.system_message != "":
            messages += [{"role": "system", "content": self.system_message}]

        messages += self.examples
        messages += self.history

        return messages + [
            {"role": "user", "content": self.prompt_prefix + "\n" + prompt_contents + "\n" + self.prompt_suffix}
        ]
