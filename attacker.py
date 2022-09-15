from random import choice, choices
from node import Node
import const

class AttackerNode(Node):
    pool: list[int]
    def __init__(self) -> None:
        super().__init__()
        self.honest = False
        self.pool = []

    def guarded_gossip(self, test_node: Node, iteration: int, use_guarded_gossip: bool) -> None:
        return

    def recv_gossip(self, gossip_node_id: int, iteration: int):
        return

    def send_gossip(self) -> list[int]:
        return choices(self.pool, k=3)

    def __str__(self) -> str:
        return f"AttackerNode#{self.id}"
