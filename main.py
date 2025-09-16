from inspect import signature
from pathlib import Path
from time import time
# from pprint import pprint
from tool import load, json_type_to_python_type
from interface import OllamaInterface
from chat import Message, Role, ChatHistory


ollama = OllamaInterface()
registry, tools = load(Path("./tools"))
model = "phi3:medium-128k"

with open("systemprompt.txt", "r") as sysprompt:
    systemprompt = sysprompt.read()


history_file = Path("chat_history.json")
chat_history = ChatHistory()
chat_history.load(history_file)


print(f"Using System Prompt:\n{systemprompt}")

chat_history.add(
    Message(
        role=Role.system,
        content=systemprompt
    )
)


print("Loaded!")
# print("Tools Loaded:")
# pprint(tools)
# print("Registry:") 
# pprint(registry)


session_start = time()
while True:
    # pprint(chat_history)
    prompt = input(">>> ")
    if prompt == "exit":
        print("Goodbye!")
        break
    msg = Message(
        role=Role.user,
        content=prompt
    )
    chat_history.add(msg)
    assistant_response = ollama.chat(model, chat_history.get_history(True)) # , tools=tools)
    chat_history.add(assistant_response)
    if not assistant_response.tool_calls:
        print(f"Assistant: {assistant_response.content}")
        continue

    calls = assistant_response.tool_calls

    for call in calls:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        func = registry[name]
        func_sig = signature(func)
        tool_schema = next(t for t in tools if t["function"]["name"] == name)
        props = tool_schema["function"]["parameters"]["properties"]

        cast_args = {}
        for k, v in args.items():
            if k in props:
                try:
                    cast_args[k] = json_type_to_python_type(props[k]["type"], v)
                except Exception:
                    cast_args[k] = v  # fallback

        cast_args = {k: v for k, v in cast_args.items() if k in func_sig.parameters}

        print(f"The AI wants to run \"{name}\" with args {cast_args}. Actual Params: {func_sig.parameters}")
        result = func(**cast_args)
        print(f"Result: {result}")
        tool_message = Message(
            role=Role.tool,
            content=str(result),
            tool_name=name
        )
        chat_history.add(tool_message)
    
    followup = ollama.chat(model, chat_history.get_history(True))  # , tools)
    chat_history.add(followup)

    print(f"Assistant: {followup.content}")

chat_history.add(Message(
    role=Role.system,
    content=f"End of Session. Session lasted {time() - session_start:.2f} seconds. Do not refer to past sessions unless expicitly stated."
))

chat_history.save(history_file)