from pathlib import Path
from sys import argv
from requests import HTTPError
from chat import ChatHistory, Message, Role
from interface import OllamaInterface
from tool import ToolHandler


class CLI:
    def __init__(self, model: str = "phi3:medium-128k") -> None:
        self.model = model
        self.interface = OllamaInterface()
        self.chat = ChatHistory()
        root = Path("~/OllamaTerminalIntegration/").expanduser().resolve()
        self.history_path = root / "chat_history_cli.json"
        tool_path = root / "Tools"
        self.tools = ToolHandler()

        if not root.exists():
            root.mkdir()
        
        if not tool_path.exists():
            tool_path.mkdir()

        if not self.history_path.exists():
            self.chat.save(self.history_path)

        self.tools.load_directory(tool_path)
        self.chat.load(self.history_path)

    def ask(self, prompt: str, use_chat: bool = True) -> str:
        if not use_chat:
            print("Not using chat")
            response = self.interface.generate(self.model, prompt, self.tools.data_ready(), False, True)
            return response.content

        message = Message(
            role=Role.user,
            content=prompt
        )
        self.chat.add(message)
        
        try:
            response = self.interface.chat(model=self.model, chat=self.chat.get_history(True), tools=self.tools.tools, think=False)
            self.chat.add(response)
        except HTTPError as e:
            return f"Unable to query AI, {e}"
        
        if response.tool_calls:
            results, tool_names = self._handle_tool_call(response)
            for res, name in zip(results, tool_names):
                if res == "No tool calls":
                    break
                tool_message = Message(
                    role=Role.tool,
                    content=res,
                    tool_name=name
                )
                self.chat.add(tool_message)
            self.chat.add(Message(
                role=Role.system,
                content=f"Use the output of the previous tool calls to answer the original prompt: \"{prompt}\"."
            ))
            response = self.interface.chat(model=self.model, chat=self.chat.get_history(True), tools=self.tools.tools, think=False)
            self.chat.add(response)
        
        self.chat.save(self.history_path)
        return response.content

    def _handle_tool_call(self, message: Message) -> tuple[list[str], list[str]]:
        calls = message.tool_calls

        if calls is None:
            return ["No tool calls"], [""]

        results = []
        names = []
        for call in calls:
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            names.append(name)
            results.append(self.tools.exec(name, **arguments))
        
        return results, names


if __name__ == "__main__":
    def main() -> None:
        cli = CLI("llama3.2")
        
        print(cli.chat.get_history())
        print(cli.tools.tools)
        prompt = argv[1:]
        chat = False

        if prompt == []:
            print("You must have a prompt!")
            exit(1)
        elif prompt[0] == '-c':
            prompt = prompt[1:]
            chat = True
        
        prompt = ' '.join(prompt)
        
        print(cli.ask(prompt, chat))

    main()