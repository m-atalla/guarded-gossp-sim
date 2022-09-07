from __future__ import annotations
from math import dist
from random import choice, choices
import rng
import const
from time import time_ns
import matplotlib.pyplot as plt


class Node:
    """
    Node holds offline node information as well as guarded gossip
    lists and offline parts of the guarded gossip protocol
    """
    ip: str
    id: int
    pred: int | None
    fingers: list[Finger]
    witnesses: dict[int, int] # key: node ID, value: timestamp
    gossiped: set[int]
    picked_gossip: set[int]
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
        self.picked_gossip = set()
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

    def recv_gossip(self, gossip_node: Node):
        """
        GuardedGossip invariant: Never trust your gossip
        """

        # when len exceeds max limit delete random nodes
        # TODO: I think this should be move to seperate procedure exclusive
        # for guarded gossip lists maintaince.. 
        # while len(self.gossiped) > const.MAX_GOSSIPS:
            # self.gossiped.remove(choice(list(self.gossiped)))

        # add to gossip set and witnesses
        for gossip in gossip_node.gossiped:
            if gossip not in self.picked_gossip:
                self.gossiped.add(gossip)
        self.gossiped.add(gossip_node.id)
        self.witnesses[gossip_node.id] = time_ns()

    def send_gossip(self) -> list[int]:
        return [finger.node for finger in self.fingers]

    def guarded_gossip(self, test_node: Node) -> None:
        # update witness entry 
        self.witnesses[test_node.id] = time_ns()

        """
        if any([self.witness_list_checking(test_node), self.bound_checking(test_node.fingers)]):
            print("Witness check=", self.witness_list_checking(test_node), end="\t")
            print("Bound check=", self.bound_checking(test_node.fingers), end="\t\n")
        """
        # if test node failed any of the protocol checks its FT
        # is discarded
        if not self.bound_checking(test_node.fingers):
            return

        if not self.witness_list_checking(test_node):
            return

        ft_nodes = list(set(test_node.fingers))
        for guard_node in choices(ft_nodes, k=rng.sample_size()):
            self.guarded.add(guard_node.id)
        

    def request_finger_table(self) -> int:
        if len(self.gossiped) != 0:
            rand_gossip_node = choice(list(self.gossiped))
            self.gossiped.remove(rand_gossip_node)
            self.picked_gossip.add(rand_gossip_node)
            return rand_gossip_node
        else:
            if len(self.picked_gossip) > 0:
                self.gossiped = set(list(self.picked_gossip))
                return self.request_finger_table()
            else:
                return self.pick_finger().id


    def ft_density(self, finger_table: list[Finger]) -> float:
        # Distance deviation
        distance_sum = 0
        for i, finger in enumerate(finger_table):
            distance = finger.node - self.ideal_finger_ids[i]
            # moves negative values to fall in id space
            if distance < 0:
                distance += const.UPPER_BOUND

            distance_sum += distance
        # Finger table density
        return (distance_sum / const.M_BITS)
        
    def set_node_density(self) -> None:
        self.expected_node_density = self.ft_density(self.fingers)

    def bound_checking(self, presented_finger_table: list[Finger]) -> bool:
        """
        One of the checks needed to consider other nodes' finger tables (ft)
        attempts to estimate if the received finger table was manipulated
        """
        node_density = self.ft_density(presented_finger_table)

        # d_g <= t*d
        return (node_density <= self.expected_node_density * const.D_TOLERANCE)

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
Auxilary classes
"""
class Finger:
    start: int
    node: int 
    def __init__(self, start: int, node: int) -> None:
        self.start = start
        self.node = node
        self.id = node # node is a bit confusing and im too lazy to fix it.
