from typing import Protocol
import anthropic


class LLMClient(Protocol):
    """
    An interface for different API provider.
    """

    def create(self, messages, system=None, tools=[]): ...


class AnthropicClient:

    model = "claude-3-5-sonnet-20240620"
    max_tokens = 500
    # LLM is mostly used for extracting inputs for tools,
    # prefer more predictability result.
    temperature = 0

    def __init__(self):
        self._client = anthropic.Anthropic()

    def create(self, messages, system=None, tools=[]):
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
            system=system,
            tools=tools,
        )
        return response


def create_client():
    # use claude for now.
    return AnthropicClient()
