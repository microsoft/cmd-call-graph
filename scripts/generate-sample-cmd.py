# Generate some sample CMD scripts to aid with debugging.

import random
import sys

# Number of functions to generate.
NUM_FUNCTIONS = 30

# Maximum number of LoC to generate.
MAX_LENGTH = 100

# Probability for any line of code to be a call to a random function.
CALL_PROBABILITY = 0.05

# Probability for any function to not terminate with "exit /b 0", which
# results in a "nested" link in cmd-call-graph
NESTED_PROBABILITY = 0.01

functions = [u"function{}".format(i) for i in range(NUM_FUNCTIONS)]

code = [u"@echo off", u"call :function0", u"exit /b 0"]

for function in functions:
    code.append(":{}".format(function))
    loc = random.randint(1, MAX_LENGTH)
    
    for i in range(loc):
        if random.random() < CALL_PROBABILITY:
            target = random.choice(functions)
            code.append(u"  call :{}".format(target))
        else:
            code.append(u"  ; some code goes here.")
    
    if random.random() > NESTED_PROBABILITY:
        code.append(u"exit /b 0")

if len(sys.argv) > 1:
    with open(sys.argv[1], "w") as f:
        f.write(u"\n".join(code))
else:
    print(u"\n".join(code))
