from math import sqrt

# Key space bits
M_BITS = 32

# maximum value in key space
UPPER_BOUND = 2 ** M_BITS 

# maximum length of gossiped nodes list
MAX_GOSSIPS = M_BITS

# maximum length of guarded nodes list
MAX_GUARDS = M_BITS

# Percentage of attacker nodes
ATTACKER_FRACT = 0.1


# Optimal density tolerance factor
D_TOLERANCE = sqrt(1/ATTACKER_FRACT)

FINGER_EXP = [2**i for i in range(M_BITS)]
