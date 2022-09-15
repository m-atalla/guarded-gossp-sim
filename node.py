from __future__ import annotations
from random import choice, choices
import rng
import const
from time import time_ns


class Node:
    """
    lists and offline parts of the guarded gossip protocol
    """
    ip: str
    id: int
    pred: int | None
    fingers: list[Finger]
    witnesses: dict[int, int] # key: node ID, value: timestamp
    gossiped: set[int]
    guarded: set[int]
    honest: bool
    expected_node_density: float
    def __init__(self) -> None:
        self.ip, self.id = rng.ip()
        self.pred: int | None = None
        self.fingers: list[Finger] = list()
        self.witnesses = dict() 
        self.guarded = set()
        self.gossiped = set()
        self.expected_node_density = 0
        self.honest = True

        # ideal finger table ids based on the assgined
        # node id
        self.ideal_finger_ids = [(self.id + exp) % const.UPPER_BOUND for exp in const.FINGER_EXP]

    def succ(self) -> int:
        return self.fingers[0].node

    def update_succ(self, new_succ: Node):
        self.fingers[0].node = new_succ.id

    def pick_finger(self) -> Finger:
        """
        Pick a random finger, excluding successor finger. (first entry, index = 0)
        pick range [1..M-1]
        """
        return self.fingers[rng.finger_idx()]

    def recv_gossip(self, gossip_node_id: int, iteration: int):
        """
        GuardedGossip invariant: Never trust your gossip
        """

        # if gossiping node was seen in the last 10 iterations it is ignored
        if gossip_node_id in self.witnesses and self.witnesses[gossip_node_id] > (iteration - 10):
            return

        self.gossiped.add(gossip_node_id)
        self.witnesses[gossip_node_id] = iteration

    def send_gossip(self) -> list[int]:
        return [f.node for f in self.fingers]

    def gossip_picks(self) -> list[int]:
        if len(self.gossiped) == 0:
            return []

        picks = []
        pick_range = rng.random.randint(0,3)
        for _ in range(pick_range):
            if len(self.gossiped) == 0:
                continue
            # pick a node from gossip list
            gossip_src_id = choice(list(self.gossiped))

            # remove it from gossip list
            self.gossiped.remove(gossip_src_id)
            picks.append(gossip_src_id)
        return picks

    def guarded_gossip(self, test_node: Node, iteration: int, use_guarded_gossip) -> None:
        # update witness entry 
        self.witnesses[test_node.id] = time_ns()

        if not self.bound_checking(test_node.fingers, test_node.ideal_finger_ids) and use_guarded_gossip:
            return

        if not self.witness_list_checking(test_node) and use_guarded_gossip:
            return

        ft_nodes = list(set(test_node.fingers))

        for node in ft_nodes:
            self.guarded.add(node.id)
            self.witnesses[node.id] = iteration

        self.maintain(self.guarded, const.MAX_GUARDS)
        self.maintain(self.gossiped, const.MAX_GOSSIPS)

    def request_finger_table(self) -> list[Finger]:
        return self.fingers

    def maintain(self, protocol_list: set[int], n_max: int) -> None:
        if len(protocol_list) > n_max:
            delete_limit = len(self.guarded) - n_max
            for _ in range(delete_limit):
                protocol_list.remove(choice(list(self.guarded)))

    def ft_density(self, finger_table: list[Finger], ideal_finger_ids: list[int]) -> float:
        # Distance deviation
        distance_sum = 0
        for i, finger in enumerate(finger_table):
            distance = finger.node - ideal_finger_ids[i]
            # moves negative values to fall in id space
            if distance < 0:
                distance += const.UPPER_BOUND

            distance_sum += distance
        # Finger table density
        return (distance_sum / const.M_BITS)
        
    def set_node_density(self) -> None:
        self.expected_node_density = self.ft_density(self.fingers, self.ideal_finger_ids)

    def bound_checking(self, presented_finger_table: list[Finger], ideal_finger_ids: list[int]) -> bool:
        """
        One of the checks needed to consider other nodes' finger tables (ft)
        attempts to estimate if the received finger table was manipulated
        """
        node_density = self.ft_density(presented_finger_table, ideal_finger_ids)
        
        tolerance_density = self.expected_node_density * const.D_TOLERANCE
        # d_g < t*d
        return (node_density <= tolerance_density)

    def best_witness(self, query: int) -> int:
        return min(self.witnesses.keys(), key=lambda w: abs(w - query))

    def witness_list_checking(self, test_node: Node) -> bool:
        """
        Checks if a node that previously sent this node gossip (witness) was purposely
        omitted by an attacker (or a node with an outdated FT.. although this case is ignored in this simulation)
        """
        for i, presented_finger in enumerate(test_node.fingers):
            # best finger for the presented finger from current node witness list
            witness_finger_id = self.best_witness(presented_finger.id)

            if presented_finger.id != witness_finger_id:
                # calculate witness distance to the idea finger id
                witness_distance = witness_finger_id - test_node.ideal_finger_ids[i]

                if witness_distance < 0:
                    witness_distance += const.UPPER_BOUND

                # same for the presented finger 
                presented_distance = presented_finger.id - test_node.ideal_finger_ids[i]

                if presented_distance < 0:
                    presented_distance += const.UPPER_BOUND

                # if presented finger violates the average distance 
                # its most likely that the other peer have either
                # manipulated their FT or has a severly outdated FT
                # either way it should be discarded.
                if witness_distance < presented_distance:
                    return False

        # Check passes only when all presented fingers pass witness checks
        return True


    def rhs(self, other):
        """
        Extracting the right hand side for overloaded arithematic operations
        """
        if isinstance(other, self.__class__):
            return other.id
        elif isinstance(other, int):
            return other
        else:
            raise TypeError(
                    "In right hand side provided: `{}`\nExpected type: `{}` or `int`"
                    .format(other, self.__class__)
                )

    def __add__(self, other):
        return (self.id + self.rhs(other)) % const.UPPER_BOUND

    def __sub__(self, other):
        return (self.id - self.rhs(other)) % const.UPPER_BOUND

    def __str__(self) -> str:
        return "Node -> pred: {}, id: {}, succ: {}".format(self.pred, self.id, self.succ())

"""
Auxilary class
"""
class Finger:
    start: int
    node: int 
    def __init__(self, start: int, node: int) -> None:
        self.start = start
        self.node = node
        self.id = node # node is a bit confusing and im too lazy to fix it.

    def __str__(self) -> str:
        return "Finger: Start={}, Node={}".format(self.start, self.node)
