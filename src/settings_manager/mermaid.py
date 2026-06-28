import re
from typing import Any, Callable, Dict, Optional


class UnsupportedMermaidFeatureError(Exception):
    """Exception raised when a Mermaid diagram contains unsupported features."""
    pass


class MermaidTransition:
    """Represents a transition between states in a Mermaid diagram."""

    def __init__(self, source: str, target: str, label: Optional[str] = None):
        self.source = source
        self.target = target
        self.label = label
        # Executable function for the transition
        self.func: Callable = self._placeholder_function

    def _placeholder_function(self, *args: Any, **kwargs: Any) -> None:
        """Default placeholder function."""
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the transition function."""
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        return f"MermaidTransition(source='{self.source}', target='{self.target}', label='{self.label}')"


class MermaidDiagram:
    """Object containing states and transitions from a Mermaid diagram."""

    def __init__(self):
        self.states: Dict[str, Callable] = {}
        self.transitions: Dict[str, MermaidTransition] = {}

    def add_state(self, state_id: str) -> None:
        """Add a state as a callable placeholder function if it doesn't exist."""
        if state_id not in self.states:
            def state_placeholder(*args: Any, **kwargs: Any) -> None:
                """Placeholder for state {state_id}."""
                pass

            # Use a safe name for the function
            safe_name = state_id.replace('[*]', 'start_end').replace(' ', '_')
            state_placeholder.__name__ = safe_name
            self.states[state_id] = state_placeholder

    def add_transition(self, source: str, target: str, label: Optional[str] = None) -> None:
        """Add a transition and its key based on label or source/target."""
        self.add_state(source)
        self.add_state(target)

        if label:
            # Convert label in quotes to snake_case
            clean_label = label.strip('" ')
            key = re.sub(r'[^a-zA-Z0-9]', '_', clean_label).lower()
            key = re.sub(r'_+', '_', key).strip('_')
        else:
            # Source or target might be [*], which is fine for dict key but we make it clean
            clean_source = source.replace('[*]', 'start')
            clean_target = target.replace('[*]', 'end')
            key = f"{clean_source}_{clean_target}"

        self.transitions[key] = MermaidTransition(source, target, label)

    def __repr__(self) -> str:
        return f"MermaidDiagram(states={list(self.states.keys())}, transitions={list(self.transitions.keys())})"


class MermaidParser:
    """Parser for Mermaid state diagrams."""

    UNSUPPORTED_PATTERNS = {
        'composite_state': r'state\s+\w+\s*\{',
        'choice_node': r'<<choice>>',
        'fork_node': r'<<fork>>',
        'join_node': r'<<join>>'
    }

    def parse(self, text: str) -> MermaidDiagram:
        """
        Parse Mermaid text and convert it to a MermaidDiagram object.

        Args:
            text: Mermaid diagram text.

        Returns:
            MermaidDiagram containing parsed states and transitions.

        Raises:
            UnsupportedMermaidFeatureError: If the diagram contains unsupported features.
        """
        # Clean text: remove comments and notes
        # Comments starting with %%
        text = re.sub(r'%%.*', '', text)
        # Notes: note [right|left] of State ... end note
        text = re.sub(r'(?s)note\s+(?:right|left)\s+of\s+.*?\s+end\s+note', '', text)
        # Floating notes: note "..." as N1
        text = re.sub(r'note\s+".*?"\s+as\s+\w+', '', text)

        # Check for unsupported features
        for feature, pattern in self.UNSUPPORTED_PATTERNS.items():
            if re.search(pattern, text):
                raise UnsupportedMermaidFeatureError(f"Unsupported Mermaid feature detected: {feature}")

        diagram = MermaidDiagram()

        lines = text.splitlines()

        # Transition pattern: State1 --> State2 [: "Label"]
        # Allows for spaces and various characters in state IDs
        # Also handles [*]
        transition_pattern = re.compile(r'([\w\[\]\*]+)\s*-->\s*([\w\[\]\*]+)(?:\s*:\s*(.*))?')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('stateDiagram') or line.startswith('direction'):
                continue

            # Ignore styling lines like: class State1 someClass
            if line.startswith('class ') or line.startswith('style '):
                continue

            match = transition_pattern.match(line)
            if match:
                source = match.group(1)
                target = match.group(2)
                label = match.group(3)
                diagram.add_transition(source, target, label)
            else:
                # Handle single state definitions or aliases: state "Some Name" as State1
                alias_match = re.match(r'state\s+"(.*?)"\s+as\s+(\w+)', line)
                if alias_match:
                    diagram.add_state(alias_match.group(2))
                    continue

                # Handle simple state definition: state State1
                state_def_match = re.match(r'state\s+(\w+)', line)
                if state_def_match:
                    diagram.add_state(state_def_match.group(1))
                    continue

                # Just a word on a line might be a state
                if re.match(r'^\w+$', line):
                    diagram.add_state(line)

        return diagram
