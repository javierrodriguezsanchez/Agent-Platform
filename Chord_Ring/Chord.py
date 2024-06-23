class Chord:
    def __init__(self, agent_id, m):
        self.agent_id = agent_id
        self.m = m
        self.ring = [None] * (2 ** m)

    def hash(self, key):
        return hash(key) % (2 ** self.m)

    def add_agent(self, agent):
        position = self.hash(agent)
        while self.ring[position] is not None:
            position = (position + 1) % (2 ** self.m)
        self.ring[position] = agent

    def find_successor(self, key):
        position = self.hash(key)
        for i in range(self.m):
            next_position = (position + 2 ** i) % (2 ** self.m)
            if self.ring[next_position] and self.ring[next_position] != self.agent_id:
                return self.ring[next_position]
        return None