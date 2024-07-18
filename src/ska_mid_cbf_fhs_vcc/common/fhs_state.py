
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
    
    fsh_action_map = {
        CONFIGURING: "configure_invoked",
        DECONFIGURING: "deconfigure_completed",
        STARTING: "starting_invoked",
        RUNNING: "starting_completed",
        STOPPING: "stopping_invoked",
        RESETTING: "reset_invoked",
        FAULT: "component_obsfault"
    }