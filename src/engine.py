from typing import Protocol
from plugin import Status


class Conversation(Protocol):
    def read(self, prompt): ...

    def write(self, message): ...


class StdioConversation:
    def read(self, prompt=""):
        return input(prompt + "\n")

    def write(self, message):
        print(message)


class FakeConversation:
    red = "\033[93m"
    end = "\033[0m"
    script = [
        "How long does it take to drive from 321 ASKASD st, ADSAC City to EWR",
        "Sorry, it is actually Jersey City",
        "What is the current travel duration by car between Filoli Historic House & Garden, Woodside, CA to Pulgas Water Temple, Redwood City, CA?",
        "I want to bike from Shoreline Amphitheatre in Mountain View to the Computer History Museum. How long will it take?",
        "How long will it take me to bike from the Ferry Building in San Francisco to Walgreens?",
        "time to travel from Chez Panisse to Mezzo in Berkeley",
        "How much is a car",
        "OK, how is the weather in LA",
    ]

    def __init__(self):
        self._index = 0

    def read(self, prompt=""):
        if prompt:
            print(f"{self.red}System:{self.end} {prompt}")
        result = None if self._index >= len(self.script) else self.script[self._index]
        self._index = self._index + 1
        print(f"{self.red}User:{self.end} {result}")
        return result

    def write(self, message):
        print(f"{self.red}System:{self.end} {message}")


class Engine:
    system = """
    You have access to tools, and should only use those tools unless you need to clarify tool inputs.
    When users asking unrelated topic, tell them all the available tools and ask them to pick.
    No need to mention the function name when answer the question using function.
    """

    def __init__(self, client, plugins, conversation):
        self._client = client
        self._plugins = plugins
        self._conversation = conversation

        self._tools = []
        for plugin in plugins:
            self._tools.append(
                {
                    "name": plugin.name(),
                    "description": plugin.description(),
                    "input_schema": plugin.input_schema(),
                }
            )

    def run_plugin(self, name, input):
        return next(filter(lambda x: x.name() == name, self._plugins)).run(input)

    def get_tool_use(self, messages):
        # looping until the LLM model find the right tool to use.
        while True:
            response = self._client.create(
                messages=messages,
                tools=self._tools,
                system=self.system,
            )
            match response.stop_reason:
                case "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    return next(
                        filter(lambda x: x.type == "tool_use", response.content)
                    )
                case "end_turn" | "max_tokens":
                    message = response.content[0].text
                    messages.append({"role": "assistant", "content": message})
                    question = self._conversation.read(message)
                    messages.append({"role": "user", "content": question})
                case _:
                    raise RuntimeError(
                        f"Unsupported {response.stop_reason}. Need improve this in the future"
                    )

    def answer(self, question):
        messages = [{"role": "user", "content": question}]

        while True:
            tool_use = self.get_tool_use(messages)
            result = self.run_plugin(tool_use.name, tool_use.input)
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result.details,
                        }
                    ],
                }
            )
            match result.status:
                case Status.INVALID_INPUT:
                    # continue the loop and wait for LLM to clarify the input.
                    pass
                case Status.OK:
                    response = self._client.create(
                        messages=messages,
                        tools=self._tools,
                        system=self.system,
                    )
                    self._conversation.write(response.content[0].text)
                    return
