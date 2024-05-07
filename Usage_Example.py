import os
import importlib

Agents = [file for file in os.listdir(f"Agents") if file != '__pycache__' and not file.endswith(".py")]

os.system("cls")

print(f"Select an Agent:")
print("----------------")
for i,name in enumerate(Agents):
    print(f"[{i}] {name}")
print("----------------")

choice = int(input())

selected_Agent = Agents[choice]
module = importlib.import_module(f"Agents.{selected_Agent}.execute")
module.Execute()