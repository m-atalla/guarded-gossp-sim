from attacker import AttackerNode
from node import Node, Finger
import const
import rng
from random import choice
class Swarm:
    """
    Swarm models the simulated overlay p2p network
    performs "online" requests on behalf of the peers
    ignoring network latency for simplicity.
    """
    nodes: dict[int, Node | AttackerNode]
    honest_nodes: list[int] 
    attacker_nodes: list[int]
    attacker_nodes_desc: list[int]
    sorted_nodes: list[Node]
    sorted_nodes_desc: list[Node]
    iterations: int

    def __init__(self, n, attacker_frac: float) -> None:
        """
        The assumption in GuardedGossip simulation was that 
        the chord was already bootstrapped with stabilized nodes
        and so initializing the chord up holds these assumption, 
        simplify the core chord implementation.. no need to worry about 
        stabilization, churn or concurrent joins.
        """

        self.attacker_nodes = list()
        self.attacker_nodes_desc = list()
        self.honest_nodes = list()
        self.nodes = {}
        ## malicious nodes should occupie a percentage of the network
        m_attackers = int(n * attacker_frac)
        n_honest = n - m_attackers
        for _ in range(m_attackers):
            attacker = AttackerNode()
            # self.validate_key(attacker.id)
            self.attacker_nodes.append(attacker.id)
            self.nodes[attacker.id] = attacker

        # sort for attack bootstrapping
        self.attacker_nodes = sorted(self.attacker_nodes)
        self.attacker_nodes = list(reversed(self.attacker_nodes))

        for _ in range(n_honest):
            node = Node()
            # self.validate_key(node)
            self.honest_nodes.append(node.id)
            self.nodes[node.id] = node

        # sort generated nodes desc
        self.sorted_nodes_desc = sorted(list(self.nodes.values()), key=lambda n: n.id, reverse=True)
        self.sorted_nodes = list(reversed(self.sorted_nodes_desc))
        
        # bootstrapping..
        # update nodes FT
        for node in self.nodes.values():
            self.init_finger_table(node)
            # at this point we can calculate each node density
            # since node churn is ignored anyways.
            node.set_node_density()

        for attacker_id in self.attacker_nodes:
            self.nodes[attacker_id].pool = self.attacker_nodes

        self.iterations = 0

    def pick(self) -> Node:
        return choice(list(self.nodes.values()))

    def pick_min(self) -> Node:
        return self.sorted_nodes_desc[-1]

    def pick_max(self) -> Node:
        return self.sorted_nodes_desc[0]
    def pick_honest_id(self) -> int:
        return choice(self.honest_nodes)

    def validate_key(self, node: Node):
        """
        Ensures that there are no key colisions
        """
        keys = self.nodes.keys()
        while node.id in keys:
            node.id = rng.key()

    def init_finger_table(self, new_node: Node):
        if not new_node.honest:
            self.bootstrap_malicious(new_node)
            return
        # first finger (successor) start id
        # 1 = 2^0
        # finger table start formula: (n + 2^i) % M
        # where 
        #   M: maximum number of bits in the key space (32) 
        #   i: entry index, i ∈ 0..M-1
        succ_start = new_node.id + 1
        
        # finds node responsible for succ start
        succ_node = self.find_successor(succ_start)

        # add successor to finger table. (e.g. finger[0])
        new_node.fingers.append(Finger(succ_start, succ_node.id))

        # update local references
        new_node.pred = self.find_predecessor(new_node.id).id

        # skip first entry since it was already filled above.
        for exp in const.FINGER_EXP[1:]:
            # init finger object
            next_start = new_node + exp
            finger_node = self.find_successor(next_start)
            new_node.fingers.append(Finger(next_start, finger_node.id))

    def bootstrap_malicious(self, new_node: AttackerNode) -> None:
        for exp in const.FINGER_EXP:
            start = new_node.id + exp
            attack_finger_node = self.find_attack_successor(start)
            new_node.fingers.append(Finger(start, attack_finger_node.id))
    
    def find_attack_successor(self, query: int) -> Node: 
        for attack_id in self.attacker_nodes:
            if attack_id >= query:
                return self.nodes[attack_id]
        return self.nodes[self.attacker_nodes[0]] # min value

    def find_attack_predecessor(self, query: int) -> Node: 
        for attack_id in self.attacker_nodes_desc:
            if attack_id < query:
                return self.nodes[attack_id]
        return self.nodes[self.attacker_nodes[-1]] # max value

    def find_successor(self, query: int) -> Node:
        for node in self.sorted_nodes:
            if node.id >= query:
                return node
        # failsafe: ensures chord cycling
        return self.pick_min() 

    def find_predecessor(self, query: int) -> Node:
        for node in self.sorted_nodes_desc:
            if node.id < query:
                return node
        # failsafe: ensures chord cycling
        return self.pick_max()

    ## Guarded gossip
    def iteration(self):
        self.gossip()
        self.iterations += 1
        # Protocol workflow
        for node in self.nodes.values():
            target_node = node.request_finger_table()
            node.guarded_gossip(self.nodes[target_node])

    def gossip(self):
        """
        forwards gossiping from source to destination
        """
        for src_node in self.nodes.values():
            gossip_targets = src_node.send_gossip()
            for gossip_target in gossip_targets:
                self.nodes[gossip_target].recv_gossip(src_node)

    def report(self):
        attacker_frac_in_honest = []
        for honest_id in self.honest_nodes:
            honest = self.nodes[honest_id]
            attacker_count = 0
            for guarded_id in honest.guarded:
                guarded_node = self.nodes[guarded_id]
                if not guarded_node.honest:
                    attacker_count += 1

            if len(honest.guarded) > 0:
                percentage = attacker_count / len(honest.guarded)
                attacker_frac_in_honest.append(percentage)

        if len(attacker_frac_in_honest) == 0:
            return 0
        return sum(attacker_frac_in_honest)/len(attacker_frac_in_honest)


    def __str__(self) -> str:
        fmt = ""
        for k, n in self.nodes.items():
            fmt += "{}: {}\n".format(k, n)
        return fmt
