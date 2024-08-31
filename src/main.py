from dotenv import load_dotenv
from client import create_client
from plugin import get_plugins
from engine import Engine, FakeConversation as Conversation

load_dotenv()

if __name__ == "__main__":
    conversation = Conversation()
    engine = Engine(
        client=create_client(), plugins=get_plugins(), conversation=conversation
    )

    question = conversation.read("What can I help?")
    while question is not None:
        engine.answer(question)
        question = conversation.read()
