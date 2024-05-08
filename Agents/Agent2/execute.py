from Agents.Utils import Choose_Action
import importlib

def Execute():
    Choose_Action(2)

def Execute_Action(action):
    module = importlib.import_module(f"Agents.Agent{2}.Actions.{action}.Run")
    module.Run()