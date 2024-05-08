import os
import importlib

class DNS:
    def __init__(self):
        self.agents = self.search_agents()

        self.agent_actions = dict()
        for agent in self.agents:
            self.agent_actions[agent]=self.search_actions_for_agent(agent)

    def search_agents(self):
        #Change for distributed
        agents = os.listdir(f"Agents")
        agents.pop()
        return agents
    
    def search_actions_for_agent(self,agent):
        #Change for distributed
        actions = os.listdir(f"Agents/{agent}/Actions")
        return actions

    def get_agent_actions(self, agent):
        return self.agent_actions[agent]

    def get_agents(self):
        return self.agents
    
    def Update(self):
        #Change for distributed
        self.agents = self.search_agents()
        self.agent_actions = dict()
        for agent in self.agents:
            self.agent_actions[agent]=self.search_actions_for_agent(agent)
