from swarm import Swarm

def main():
    swarm = Swarm(100, attacker_frac=0.3, use_guarded_gossip=True)

    for _ in range(300):
        swarm.iteration()
    print("Attacker fraction: {}%".format(int(swarm.report()*100)))

if __name__ == '__main__':
    main()
