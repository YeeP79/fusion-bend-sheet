"""Python-JavaScript bridge for BrowserCommandInput communication.

This module provides type-safe handling of messages between the Python
add-in and the HTML tree view component.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import adsk.core

from ...lib import fusionAddInUtils as futil
from ...models import Bender


# Action types for incoming messages (JS -> Python)
IncomingAction = Literal[
    'requestBenders',
    'addBender',
    'editBender',
    'deleteBender',
    'addDie',
    'editDie',
    'deleteDie',
]

# Action types for outgoing messages (Python -> JS)
OutgoingAction = Literal[
    'loadBenders',
    'updateBender',
    'addBenderToList',
    'removeBender',
    'removeDie',
]


@dataclass(slots=True)
class HTMLMessage:
    """Parsed message from JavaScript."""

    action: str
    bender_id: str | None = None
    die_id: str | None = None

    def __repr__(self) -> str:
        parts = [f"action={self.action!r}"]
        if self.bender_id:
            parts.append(f"bender_id={self.bender_id!r}")
        if self.die_id:
            parts.append(f"die_id={self.die_id!r}")
        return f"HTMLMessage({', '.join(parts)})"


class HTMLBridge:
    """Handles Python-JavaScript communication for BrowserCommandInput.

    This class provides type-safe methods for:
    - Parsing incoming messages from JavaScript
    - Sending data updates to the HTML tree view
    """

    def __init__(self, browser_input: 'adsk.core.BrowserCommandInput') -> None:
        """
        Initialize the bridge.

        Args:
            browser_input: The BrowserCommandInput to communicate with
        """
        self._browser_input = browser_input

    def parse_message(self, args: 'adsk.core.HTMLEventArgs') -> HTMLMessage:
        """
        Parse an incoming HTML event into a typed message.

        Args:
            args: The HTMLEventArgs from the incomingFromHTML event

        Returns:
            Parsed HTMLMessage with action and optional IDs
        """
        action = args.action
        data: dict[str, str] = {}

        if args.data:
            try:
                parsed = json.loads(args.data)
                if isinstance(parsed, dict):
                    data = parsed
                else:
                    futil.log(
                        f'HTMLBridge: Expected dict, got {type(parsed).__name__}'
                    )
            except json.JSONDecodeError as e:
                futil.log(f'HTMLBridge: JSON decode error: {e}')

        return HTMLMessage(
            action=action,
            bender_id=data.get('bender_id'),
            die_id=data.get('die_id'),
        )

    def send_benders(self, benders: list[Bender]) -> None:
        """
        Send the full bender list to the HTML view.

        Args:
            benders: List of all benders to display
        """
        data = json.dumps([b.to_dict() for b in benders])
        self._browser_input.sendInfoToHTML('loadBenders', data)

    def send_bender_added(self, bender: Bender) -> None:
        """
        Notify HTML that a new bender was added.

        Args:
            bender: The newly created bender
        """
        data = json.dumps(bender.to_dict())
        self._browser_input.sendInfoToHTML('addBenderToList', data)

    def send_bender_update(self, bender: Bender) -> None:
        """
        Send a single bender update to the HTML view.

        Args:
            bender: The updated bender
        """
        data = json.dumps(bender.to_dict())
        self._browser_input.sendInfoToHTML('updateBender', data)

    def send_bender_removed(self, bender_id: str) -> None:
        """
        Notify HTML that a bender was removed.

        Args:
            bender_id: ID of the removed bender
        """
        self._browser_input.sendInfoToHTML('removeBender', bender_id)

    def send_die_removed(self, bender_id: str, die_id: str) -> None:
        """
        Notify HTML that a die was removed.

        Args:
            bender_id: ID of the bender containing the die
            die_id: ID of the removed die
        """
        data = json.dumps({'bender_id': bender_id, 'die_id': die_id})
        self._browser_input.sendInfoToHTML('removeDie', data)
