import platform
import socket
import psutil
import GPUtil
from sys import argv, stderr, stdout
from os import environ
from datetime import datetime
from requests import post


class OllamaInterface:
    def __init__(self) -> None:
        self._routes = {
            "generate": "/api/generate"
        }
        self._domain = "http://127.0.0.1:11434"

    def generate(self, model: str, prompt: str) -> str:
        url = self._domain + self._routes["generate"]
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        try:
            resp = post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", "No response field in API output")
            return response
        except Exception as e:
            return f"Error: Failed to get response from Ollama: {e}"


def get_system_info() -> str:
    """Gather system information to include in the prompt."""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

        os_name = platform.system()
        os_version = platform.release()
        os_architecture = platform.machine()

        hostname = socket.gethostname()

        gpus = GPUtil.getGPUs()
        if not gpus:
            return "No GPU detected"
        gpu_info = ", ".join([f"{gpu.name}, {gpu.memoryTotal/1024:.2f} GB VRAM" for gpu in gpus])

        shell = environ.get("SHELL", "Unknown")

        cpu_info = f"{psutil.cpu_count(logical=True)} logical CPUs, {psutil.cpu_count(logical=False)} physical CPUs"
        memory = psutil.virtual_memory()
        memory_info = f"{memory.total / (1024**3):.2f} GB total, {memory.available / (1024**3):.2f} GB available"
        disk = psutil.disk_usage('/')
        disk_info = f"{disk.total / (1024**3):.2f} GB total, {disk.free / (1024**3):.2f} GB free"

        system_info = (
            f"System Information:\n"
            f"- Shell: {shell}\n"
            f"- Date and Time: {current_time}\n"
            f"- Hostname: {hostname}\n"
            f"- OS: {os_name} {os_version} ({os_architecture})\n"
            f"- GPU: {gpu_info}\n"
            f"- CPU: {cpu_info}\n"
            f"- Memory: {memory_info}\n"
            f"- Disk: {disk_info}"
        )
        return system_info
    except Exception as e:
        return f"System Information: Unable to gather details ({e})\n\n"


if __name__ == "__main__":
    oi = OllamaInterface()
    model = "llama3.2"
    parts = argv[1:]
    if parts == []:
        print("You must have a prompt!", file=stderr)
        exit(1)
    
    if parts[0] == "-q":
        quiet = True
        parts = parts[1:]
    else:
        quiet = False
    user_prompt = ' '.join(parts)

    # Prepend system information to the user's prompt
    full_prompt = f"{get_system_info()}\n\nInstructions: You should respond in short, consise answers. Your output is inside a console. Do not use markdown formatting. Do not apologize for not being able to do something.\n\nUser Prompt: {user_prompt}"
    
    print(oi.generate(model, full_prompt), file=stderr if quiet else stdout)
