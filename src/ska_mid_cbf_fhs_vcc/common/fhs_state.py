
import enum

class FhsState(enum.IntEnum):

    IDLE = 0

    CONFIGURING = 1

    DECONFIGURING = 2

    STARTING = 3

    RUNNING = 4

    STOPPING = 5

    RESETTING = 6

    RESET = 7

    FAULT = 9