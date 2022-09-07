from random import choice, choices
from node import Node
import const

class AttackerNode(Node):
    pool: list[int]
    def __init__(self) -> None:
        super().__init__()
        self.honest = False
        self.pool = []

    def guarded_gossip(self, test_node: Node) -> None:
        return

    def send_gossip(self) -> list[int]:
        return choices(self.pool, k=const.M_BITS)
