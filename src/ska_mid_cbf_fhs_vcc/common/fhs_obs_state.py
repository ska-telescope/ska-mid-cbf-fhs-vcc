# -*- coding: utf-8 -*-
#
# This file is part of the SKA Mid CBF FHS VCC project
#
# Copied from the SKA Control System project but updated to provide state transitions for low level fhs vcc devices
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE.txt for more info.
"""This module defines an enumerated type for observing state."""

import enum
import logging
from typing import Any, Callable, Final, Optional

from ska_control_model import ObsState
from transitions.extensions import LockedMachine as Machine

from ska_control_model.faults import StateModelError
from ska_control_model.utils import for_testing_only


# class ObsState(enum.IntEnum):
#     """Python enumerated type for observing state."""

#     IDLE = 0

#     CONFIGURING = 1

#     DECONFIGURING = 2

#     STARTING = 3

#     RUNNING = 4

#     STOPPING = 5

#     RESETTING = 6

#     RESET = 7

#     RESETTING = 8

#     FAULT = 9

class FhsObsStateMachine(Machine):
    """
    The observation state machine used by a generic FHS base class sub-element ObsDevice.

    NOTE: entirely taken from ska-mid-cbd-mcs which in turn was taken from ska-csp-lmc-base CspSubElementObsStateMachine,
    to decouple FSH-VCC from their ska-tango-base version dependency

    """

    def __init__(
        self, callback: Optional[Callable] = None, **extra_kwargs: Any
    ) -> None:
        """
        Initialise the model.

        :param callback: A callback to be called when the state changes
        :param extra_kwargs: Additional keywords arguments to pass to super class
            initialiser (useful for graphing)
        """
        self._callback = callback

        states = [
            "IDLE",
            "CONFIGURING",  # device CONFIGURING but component is unconfigured
            "DECONFIGURING",  # device CONFIGURING but component is unconfigured
            "STARTING",
            "RUNNING",
            "STOPPING",
            "RESETTING",
            "RESET",
            "FAULT",
        ]
        transitions = [
            {
                "source": "*",
                "trigger": "component_obsfault",
                "dest": "FAULT",
            },
            {
                "source": "IDLE",
                "trigger": "configure_invoked",
                "dest": "CONFIGURING",
            },                
            {
                "source": "IDLE",
                "trigger": "deconfigure_invoked",
                "dest": "DECONFIGURING",
            },
            {
                "source": "CONFIGURING",
                "trigger": "configure_completed",
                "dest": "IDLE",
            },
            {
                "source": "DECONFIGURING",
                "trigger": "deconfigure_completed",
                "dest": "IDLE",
            },
            {
                "source": "IDLE",
                "trigger": "starting_invoked",
                "dest": "STARTING",
            },
            {
                "source": "STARTING",
                "trigger": "starting_completed",
                "dest": "RUNNING",
            },
            {
                "source": "RUNNING",
                "trigger": "stopping_invoked",
                "dest": "STOPPING",
            },
            {
                "source": "STOPPING",
                "trigger": "stopping_completed",
                "dest": "IDLE",
            },
            {
                "source": "FAULT",
                "trigger": "reset_completed",
                "dest": "RESET",
            },
            {
                "source": "RESET",
                "trigger": "reset_completed",
                "dest": "IDLE",
            },
        ]
        super().__init__(
            states=states,
            initial="IDLE",
            transitions=transitions,
            after_state_change=self._state_changed,
            **extra_kwargs,
        )
        self._state_changed()

    def _state_changed(self) -> None:
        """
        State machine callback that is called every time the obs_state changes.

        Responsible for ensuring that callbacks are called.
        """
        if self._callback is not None:
            self._callback(self.state)

class FhsObsStateModel:
    """
    Implements the observation state model for subarray.

    The model supports all of the states of the
    :py:class:`~ska_control_model.obs_state.ObsState` enum:

    * **EMPTY**: the subarray is unresourced
    * **RESOURCING**: the subarray is performing a resourcing operation
    * **IDLE**: the subarray is resourced but unconfigured
    * **CONFIGURING**: the subarray is performing a configuring
      operation
    * **READY**: the subarray is resourced and configured
    * **SCANNING**: the subarray is scanning
    * **ABORTING**: the subarray is aborting
    * **ABORTED**: the subarray has aborted
    * **RESETTING**: the subarray is resetting from an ABORTED or FAULT
      state back to IDLE
    * **RESTARTING**: the subarray is restarting from an ABORTED or
      FAULT state back to EMPTY
    * **FAULT**: the subarray has encountered a observation fault.

    A diagram of the subarray observation state model is shown below.
    This model is non-deterministic as diagrammed, but the underlying
    state machines has extra states and transitions that render it
    deterministic. This class simply maps those extra classes onto
    valid ObsState values.

    .. uml:: obs_state_model.uml
       :caption: Diagram of the subarray observation state model
    """

    _OBS_STATE_MAPPING: Final = {
            "IDLE": ObsState.IDLE,
            "CONFIGURING": ObsState.CONFIGURING,  
            "DECONFIGURING": ObsState.CONFIGURING, 
            "STARTING": ObsState.READY,
            "RUNNING": ObsState.READY,
            "STOPPING": ObsState.READY,
            "RESETTING": ObsState.CONFIGURING,
            "RESET": ObsState.READY,
            "FAULT": ObsState.FAULT,
    }

    def __init__(
        self,
        logger: logging.Logger,
        callback: Callable[[ObsState], None] | None = None,
        state_machine_factory: Callable[..., Machine] = FhsObsStateMachine,
    ) -> None:
        """
        Initialise the model.

        :param logger: the logger to be used by this state model.
        :param callback: A callback to be called when a transition
            causes a change to device obs_state
        :param state_machine_factory: a callable that returns a
            state machine for this model to use
        """
        self.logger = logger

        self._obs_state: ObsState | None = None
        self._callback = callback

        self._obs_state_machine = state_machine_factory(
            callback=self._obs_state_changed
        )

    @property
    def obs_state(self) -> ObsState | None:
        """
        Return the obs_state.

        :returns: obs_state of this state model
        """
        return self._obs_state

    def _obs_state_changed(self, machine_state: str) -> None:
        """
        Handle change in observation state.

        This is a helper method that updates obs_state, ensuring that
        the callback is called if one exists.

        :param machine_state: the new state of the observation state
            machine
        """
        obs_state = self._OBS_STATE_MAPPING[machine_state]
        if self._obs_state != obs_state:
            self._obs_state = obs_state
            if self._callback is not None:
                self._callback(obs_state)

    def is_action_allowed(self, action: str, raise_if_disallowed: bool = False) -> bool:
        """
        Return whether a given action is allowed in the current state.

        :param action: an action, as given in the transitions table
        :param raise_if_disallowed: whether to raise an exception if the
            action is disallowed, or merely return False (optional,
            defaults to False)

        :raises StateModelError: if the action is unknown to the state
            machine

        :return: whether the action is allowed in the current state
        """
        if action in self._obs_state_machine.get_triggers(
            self._obs_state_machine.state
        ):
            return True

        if raise_if_disallowed:
            raise StateModelError(
                f"Action {action} is not allowed in obs state "
                f"{'None' if self.obs_state is None else self.obs_state.name}."
            )
        return False

    def perform_action(self, action: str) -> None:
        """
        Perform an action on the state model.

        :param action: an action, as given in the transitions table
        """
        _ = self.is_action_allowed(action, raise_if_disallowed=True)
        self._obs_state_machine.trigger(action)

    @for_testing_only
    def _straight_to_state(self, obs_state_name: ObsState) -> None:
        """
        Take this model straight to the specified state.

        This method exists to simplify testing; for example, if testing
        that a command may be run in a given ObsState, one can push this
        state model straight to that ObsState, rather than having to
        drive it to that state through a sequence of actions. It is not
        intended that this method would be called outside of test
        setups. A warning will be raised if it is.

        For example, to test that a device transitions from SCANNING to
        ABORTING when the Abort() command is called:

        .. code-block:: py

            model = ObservationStateModel(logger)
            model._straight_to_state("SCANNING")
            assert model.obs_state == ObsState.SCANNING
            model.perform_action("abort_invoked")
            assert model.obs_state == ObsState.ABORTING

        :param obs_state_name: the target obs_state
        """
        getattr(self._obs_state_machine, f"to_{obs_state_name}")()