import os
import importlib

def Choose_Action(Agent: int):
    """Choose one of the Agent actions and execute it"""
    
    actions = os.listdir(f"Agents/Agent{Agent}/Actions")
    os.system("cls")

    print(f"Agent {Agent} Actions:")
    print("----------------")
    for i,name in enumerate(actions):
        print(f"[{i}] {name}")
    print("----------------")

    choice = int(input())

    selected_action = actions[choice]
    module = importlib.import_module(f"Agents.Agent{Agent}.Actions.{selected_action}.Run")
    module.Run()