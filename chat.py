from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError, dump, load
from pathlib import Path


class Role(Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


@dataclass
class Message:
    role: Role
    content: str | None = None
    tool_calls: list[dict] | None = None
    tool_name: str | None = None

    def to_dict(self) -> dict:
        msg = {"role": self.role.name}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_calls is not None:
            msg["tool_calls"] = self.tool_calls
        if self.tool_name is not None:
            msg["tool_name"] = self.tool_name
        return msg


class ChatHistory:
    """Helper class to manage chat history with LLMs."""
    def __init__(self) -> None:
        self._history = []

    def add(self, message: Message | dict) -> None:
        """Adds a message to the history."""
        if isinstance(message, Message):
            self._history.append(message)
        elif isinstance(message, dict):
            self._history.append(dict_to_message(message))

    def save(self, file: Path) -> None:
        """Save the current history to a file. THIS OVERRIDES ANY CONTENT INSIDE THE FILE!"""
        with open(file, "w") as save_file:
            dump(self.get_history(True), save_file, indent=2)

    def load(self, file: Path) -> None:
        """Loads a file and extends the current chat history."""
        if not file.exists():
            raise OSError(f"{file} does not exist!")
        elif not file.is_file():
            raise IsADirectoryError(f"{file} should be a file!")
        
        file = file.resolve()

        with open(file, "r") as history_file:
            try:
                saved_chat_history = load(history_file)
            except JSONDecodeError:
                saved_chat_history = []
        
        if not isinstance(saved_chat_history, list):
            raise Exception("Bad Chat History Format! It should be a list!")
        
        chat_history = []

        for message in saved_chat_history:
            chat_history.append(dict_to_message(message))
        
        self._history.extend(chat_history)

    def clear(self, file: Path | None = None) -> None:
        """Clears the current chat history and optionally the file."""
        self._history = []
        if file:
            with open(file, "w") as history_file:
                dump([], history_file)

    def get_history(self, json: bool = False):
        """Get all chat history"""
        if json:
            return [message.to_dict() for message in self._history]
        return self._history

    def assistant(self, json: bool = False):
        """Get only assistant messages"""
        if json:
            return [message.to_dict() for message in self._history if message.role == Role.assistant]
        return [message for message in self._history if message.role == Role.assistant]

    def user(self, json: bool = False):
        """Get only user messages"""
        if json:
            return [message.to_dict() for message in self._history if message.role == Role.user]
        return [message for message in self._history if message.role == Role.user]

    def system(self, json: bool = False):
        """Get only system messages"""
        if json:
            return [message.to_dict() for message in self._history if message.role == Role.system]
        return [message for message in self._history if message.role == Role.system]

    def tool(self, json: bool = False):
        """Get only tool messages"""
        if json:
            return [message.to_dict() for message in self._history if message.role == Role.tool]
        return [message for message in self._history if message.role == Role.tool]


def dict_to_message(dictionary: dict) -> Message:
    """Converts a message dictionary (from Message) and converts back into a Message object."""
    role = dictionary["role"]
    if role == 'user':
        dictionary["role"] = Role.user
    elif role == 'assistant':
        dictionary["role"] = Role.assistant
    elif role == 'system':
        dictionary["role"] = Role.system
    elif role == 'tool':
        dictionary["role"] = Role.tool
    role = dictionary["role"]
    content = dictionary.get("content")
    tool_calls = dictionary.get("tool_calls")
    tool_name = dictionary.get("tool_name")
    return Message(
        role,
        content,
        tool_calls,
        tool_name
    )
