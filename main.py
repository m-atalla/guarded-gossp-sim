from swarm import Swarm

def main():
    swarm = Swarm(100, attacker_frac=0.2)

    itera=0
    for _ in range(200):
        swarm.iteration()
        itera += 1

    print(int(swarm.report()*100))


if __name__ == '__main__':
    main()
