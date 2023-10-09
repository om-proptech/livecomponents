import abc
import datetime

from redis import Redis

from livecomponents.types import StateAddress

PATH_SEP = "/"


class IStateStore(abc.ABC):
    @abc.abstractmethod
    def restore(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        ...


class IHierarchyStore(abc.ABC):
    @abc.abstractmethod
    def init_component(
        self,
        session_id: str,
        component_type: str,
        component_id: str,
        parent_id: str | None = None,
        component_name: str | None = None,
    ):
        ...

    @abc.abstractmethod
    def get_children(self, session_id: str, component_id: str) -> list[str]:
        ...

    @abc.abstractmethod
    def get_descendants(self, session_id: str, component_id: str) -> list[str]:
        ...

    @abc.abstractmethod
    def get_ancestors(self, session_id: str, component_id: str) -> list[str]:
        ...

    @abc.abstractmethod
    def get_parent(self, session_id: str, component_id: str) -> str | None:
        ...

    @abc.abstractmethod
    def get_component_type(self, session_id: str, component_id: str) -> str:
        ...

    @abc.abstractmethod
    def get_by_component_name(self, session_id: str, component_name: str) -> str | None:
        ...


class RedisStateStore(IStateStore):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "LC:",
        ttl: datetime.timedelta = datetime.timedelta(days=1),
    ):
        self.client = Redis.from_url(redis_url)  # type: ignore
        self.key_prefix = key_prefix
        self.ttl = ttl

    def restore(self, state_addr: StateAddress) -> bytes | None:
        key_name = self._get_key_name(state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hget(key_name, state_addr.component_id)
            pipe.expire(key_name, self.ttl)
            raw_state, _ = pipe.execute()
        return raw_state

    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        key_name = self._get_key_name(state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hset(key_name, state_addr.component_id, raw_state)
            pipe.expire(key_name, self.ttl)
            pipe.execute()

    def _get_key_name(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"


class RedisHierarchyStore(IHierarchyStore):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        hierarchy_key_prefix: str = "LCH:",
        type_key_prefix: str = "LCT:",
        name_key_prefix: str = "LCN:",
        reverse_name_key_prefix: str = "LCRN:",
        ttl: datetime.timedelta = datetime.timedelta(days=1),
    ):
        self.client = Redis.from_url(  # type: ignore
            redis_url,
            decode_responses=True,
        )
        self.hierarchy_key_prefix = hierarchy_key_prefix
        self.type_key_prefix = type_key_prefix
        self.name_key_prefix = name_key_prefix
        self.reverse_name_key_prefix = reverse_name_key_prefix
        self.ttl = ttl

    def init_component(
        self,
        session_id: str,
        component_type: str,
        component_id: str,
        parent_id: str | None = None,
        component_name: str | None = None,
    ):
        """Init the component.

        The tree structure is stored in a hash map, where the hash key is the
        component_id, and the hash value is the full path of the component.
        """
        self._ensure_id_valid(component_id)
        if parent_id:
            self._ensure_id_valid(parent_id)

        if parent_id:
            parent_path = self._get_component_path(session_id, parent_id)
            component_path = f"{parent_path}{PATH_SEP}{component_id}"
        else:
            component_path = component_id

        hier_key_name = self._get_hierarchy_key_name(session_id)
        type_key_name = self._get_type_key_name(session_id)
        name_key_name = self._get_name_key_name(session_id)
        reverse_name_key_name = self._get_reverse_name_key_name(session_id)
        with self.client.pipeline() as pipe:
            # Hierarchy
            pipe.hset(hier_key_name, component_id, component_path)
            pipe.expire(hier_key_name, self.ttl)
            # Type mapping
            pipe.hset(type_key_name, component_id, component_type)
            pipe.expire(type_key_name, self.ttl)
            # Name and reverse name mapping (if necessary)
            if component_name:
                pipe.hset(name_key_name, component_id, component_name)
                pipe.expire(name_key_name, self.ttl)
                pipe.hset(reverse_name_key_name, component_name, component_id)
                pipe.expire(reverse_name_key_name, self.ttl)
            pipe.execute()

    def get_children(self, session_id: str, component_id: str) -> list[str]:
        """Return all direct children of the component."""
        self._ensure_id_valid(component_id)
        key_name = self._get_hierarchy_key_name(session_id)
        children = []
        component_path = self._get_component_path(session_id, component_id)
        for child_id, child_path in self.client.hscan_iter(
            key_name, f"{component_path}{PATH_SEP}*"
        ):
            path_without_prefix = child_path[len(component_path) + 1 :]
            if PATH_SEP not in path_without_prefix:
                children.append(child_id)
        return children

    def get_descendants(self, session_id: str, component_id: str) -> list[str]:
        """Return all descendants of the component."""
        self._ensure_id_valid(component_id)
        key_name = self._get_hierarchy_key_name(session_id)
        component_path = self._get_component_path(session_id, component_id)
        return [
            child_id
            for child_id, child_path in self.client.hscan_iter(
                key_name, f"{component_path}{PATH_SEP}*"
            )
        ]

    def get_ancestors(self, session_id: str, component_id: str) -> list[str]:
        """Return the list of ancestors of the current component."""
        self._ensure_id_valid(component_id)
        component_path = self._get_component_path(session_id, component_id)
        return component_path.split(PATH_SEP)[:-1]

    def get_parent(self, session_id: str, component_id: str) -> str | None:
        """Return the parent of the current component."""
        self._ensure_id_valid(component_id)
        ancestors = self.get_ancestors(session_id, component_id)
        if not ancestors:
            return None
        return ancestors[-1]

    def get_component_type(self, session_id: str, component_id: str) -> str:
        """Return the component type."""
        self._ensure_id_valid(component_id)
        key_name = self._get_type_key_name(session_id)
        component_type = self.client.hget(key_name, component_id)
        if not component_type:
            raise ValueError(f"Component not found: {component_id}")
        return component_type

    def get_by_component_name(self, session_id: str, component_name: str) -> str | None:
        """Return the component_id by component_name."""
        key_name = self._get_reverse_name_key_name(session_id)
        return self.client.hget(key_name, component_name)

    def _get_component_path(self, session_id: str, component_id: str) -> str:
        key_name = self._get_hierarchy_key_name(session_id)
        path = self.client.hget(key_name, component_id)
        if not path:
            raise ValueError(f"Component not found: {component_id}")
        return path

    def _ensure_id_valid(self, value: str):
        if PATH_SEP in value:
            raise ValueError(
                f"Invalid character {PATH_SEP!r} in component_id {value!r}"
            )

    def _get_hierarchy_key_name(self, session_id: str) -> str:
        return f"{self.hierarchy_key_prefix}{session_id}"

    def _get_type_key_name(self, session_id: str) -> str:
        return f"{self.type_key_prefix}{session_id}"

    def _get_name_key_name(self, session_id: str) -> str:
        return f"{self.name_key_prefix}{session_id}"

    def _get_reverse_name_key_name(self, session_id: str) -> str:
        return f"{self.reverse_name_key_prefix}{session_id}"
