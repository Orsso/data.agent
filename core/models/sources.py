from dataclasses import dataclass, field

from core.profiler import format_profile
from core.state import DataProfile


@dataclass
class DataSource:
    name: str
    profile: DataProfile
    origin: str = "csv"
    row_count: int = 0
    columns: list[str] = field(default_factory=list)
    sample_text: str = ""  # head(3).to_string(), computed once at upload


class SourceRegistry:
    """Manages multiple named DataSources for a project."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}
        self._primary_name: str | None = None

    def add(self, name: str, source: DataSource) -> None:
        self._sources[name] = source
        if self._primary_name is None:
            self._primary_name = name

    def remove(self, name: str) -> bool:
        if name not in self._sources:
            return False
        del self._sources[name]
        if self._primary_name == name:
            self._primary_name = next(iter(self._sources), None)
        return True

    def get(self, name: str) -> DataSource | None:
        return self._sources.get(name)

    def get_all(self) -> dict[str, DataSource]:
        return dict(self._sources)

    @property
    def primary(self) -> DataSource | None:
        if self._primary_name is None:
            return None
        return self._sources.get(self._primary_name)

    @property
    def is_empty(self) -> bool:
        return len(self._sources) == 0

    @property
    def count(self) -> int:
        return len(self._sources)

    def combined_context(self) -> str:
        """Build a multi-source context string for prompts."""
        if not self._sources:
            return "No data sources loaded."

        parts = []
        for name, src in self._sources.items():
            profile_str = format_profile(src.profile)
            parts.append(
                f"### DataFrame `{name}` ({src.row_count} rows)\n"
                f"Columns: {', '.join(src.columns)}\n\n"
                f"{profile_str}\n\n"
                f"Sample data:\n{src.sample_text}"
            )
        return "\n\n---\n\n".join(parts)
