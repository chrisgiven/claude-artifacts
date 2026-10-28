"""Provider contract. One implementation per platform (Docker, Azure ASR, ...).

The engine only talks to this interface, so scenarios, measurement and the
evidence pack are identical whichever platform the twin runs on.
"""
from abc import ABC, abstractmethod


class Provider(ABC):
    name = "abstract"

    def __init__(self, manifest, root):
        self.manifest, self.root = manifest, root

    @abstractmethod
    def up(self, healthy):
        """Build the twin from recovery artifacts; return once `healthy()` is true."""

    @abstractmethod
    def isolation_proof(self):
        """Return {'passed': bool, 'checks': [...]}. Must run before any fault."""

    @abstractmethod
    def inventory(self):
        """Observed state for the drift check: services, replication, backup age."""

    @abstractmethod
    def teardown(self):
        """Destroy the twin and its data. Return an attestation dict."""

    @abstractmethod
    def actions(self):
        """Map of action name -> callable(step_args, ctx) -> optional detail str."""
