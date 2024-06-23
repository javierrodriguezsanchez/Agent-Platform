class Chord:
    def init(self, agent_id, m):
        self.agent_id = agent_id
        self.m = m
        self.ring = [None] * (2 ** m)

    def hash(self, key):
        return hash(key) % (2 ** self.m)

    def add_agent(self):
        position = self.hash(self.agent_id)
        self.ring[position] = self.agent_id

    def find_successor(self, key):
        position = self.hash(key)
        for i in range(self.m):
            next_position = (position + 2 ** i) % (2 ** self.m)
            if self.ring[next_position]:
                return self.ring[next_position]
        return None