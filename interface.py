from requests import HTTPError, post
from chat import Message, Role


class OllamaInterface:
    def __init__(self, port: int = 11434) -> None:
        self._routes = {
            "generate": "/api/generate",
            "chat": "/api/chat"
        }

        self._domain = f"http://127.0.0.1:{port}"

    def generate(self, model: str, prompt: str, tools: str = "", think: bool = False, raw: bool = False) -> Message:
        url = self._domain + self._routes["generate"]
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        if raw:
            if tools is None:
                raise ValueError("You must provide tools.")
            prompt = f"[AVAILABLE_TOOLS] {tools}[/AVAILABLE_TOOLS][INST] {prompt} [/INST]"
            payload["prompt"] = prompt
            payload["raw"] = True
        
        resp = post(url, json=payload)
        
        if resp.status_code == 400:
            raise HTTPError(resp.json()['error'])

        data = resp.json()
        message_content = data["response"]
        calls = data.get("tool_calls")

        return Message(
            role=Role.assistant,
            content=message_content,
            tool_calls=calls
        )

    def chat(self, model: str, chat: list[dict], tools: list[dict] = list(), think: bool = False) -> Message:
        url = self._domain + self._routes["chat"]
        payload = {
            "model": model,
            "messages": chat,
            "think": think,
            "tools": tools,
            "stream": False
        }

        resp = post(url, json=payload)

        if resp.status_code == 400:
            raise HTTPError(resp.json()['error'])
        
        data = resp.json()
        message_content = data["message"]
        calls = message_content.get("tool_calls")
        return Message(
            role=Role.assistant,
            content=message_content["content"],
            tool_calls=calls
        )