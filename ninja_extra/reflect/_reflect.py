import logging
import typing as t
import weakref
from contextlib import asynccontextmanager, contextmanager
from weakref import WeakKeyDictionary, WeakValueDictionary

from .utils import ensure_target, fail_silently, get_original_target

logger = logging.getLogger("ellar")


def _try_hash(item: t.Any) -> bool:
    """
    Try to hash an item.

    :param item: The item to try and hash.
    :return: True if the item is hashable, False otherwise.
    """
    try:
        hash(item), weakref.ref(item)
        return True
    except TypeError:
        return False


class _Hashable:
    """
    A wrapper class to make unhashable items hashable by using their ID and string representation.
    """

    def __init__(self, item_id: int, item_repr: str) -> None:
        self.item_id = item_id
        self.item_repr = item_repr
        # self._item_repr = item_repr

    def __hash__(self) -> int:
        # Combine the hash values of the attributes
        attrs = self.item_id, self.item_repr
        return hash(attrs)

    def __eq__(self, other: t.Any) -> bool:
        # Check if another object is equal based on attributes
        if isinstance(other, _Hashable):
            return self.item_id == other.item_id
        return False

    def __repr__(self) -> str:
        return self.item_repr

    @classmethod
    def force_hash(cls, item: t.Any) -> t.Union[t.Any, "_Hashable"]:
        """
        Force an item to be hashable. If it's already hashable, return it.
        If not, return a _Hashable wrapper or retrieve an existing one.

        :param item: The item to hash.
        :return: The item or its _Hashable wrapper.
        """
        if not _try_hash(item):
            hashable = fail_silently(
                lambda: reflect._un_hashable[hash((id(item), repr(item)))]
            )
            if hashable:
                return hashable

            new_target = cls(item_id=id(item), item_repr=repr(item))
            return reflect.add_un_hashable_type(new_target)
        return item


def _get_actual_target(
    target: t.Any,
) -> t.Any:
    """
    Get the actual target for metadata operations.
    Resolves proxies and ensures the target is hashable.

    :param target: The target to resolve.
    :return: The resolved, hashable target.
    """
    target = get_original_target(target)
    return _Hashable.force_hash(ensure_target(target))


class _Reflect:
    """
    Metadata manager class for storage and retrieval of metadata associated with types and callables.
    Use `reflect` instance for all operations.
    """

    __slots__ = ("_meta_data",)

    _un_hashable: t.Dict[int, _Hashable] = {}
    _data_type_update_callbacks: t.MutableMapping[t.Type, t.Callable] = (
        WeakValueDictionary()
    )

    def __init__(self) -> None:
        self._meta_data: t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict] = (
            WeakKeyDictionary()
        )

    def add_type_update_callback(self, type_: t.Type, func: t.Callable) -> None:
        """
        Register a callback to handle updates for a specific metadata type.

        :param type_: The type of the metadata value.
        :param func: The call back function to handle the update.
        """
        self._data_type_update_callbacks[type_] = func

    def add_un_hashable_type(self, value: _Hashable) -> _Hashable:
        """
        Store an unhashable item wrapper.

        :param value: The _Hashable wrapper.
        :return: The stored _Hashable wrapper.
        """
        self._un_hashable[hash(value)] = value
        return value

    def _default_update_callback(
        self, existing_value: t.Any, new_value: t.Any
    ) -> t.Any:
        return new_value

    def define_metadata(
        self,
        metadata_key: str,
        metadata_value: t.Any,
        target: t.Any,
    ) -> t.Any:
        """
        Define metadata for a target.

        :param metadata_key: The key for the metadata.
        :param metadata_value: The value of the metadata.
        :param target: The target object to associate the metadata with.
        :return: The value returned by type update callback or new value.
        """
        if target is None:
            raise Exception("`target` is not a valid type")
        # if (
        #     not isinstance(target, type)
        #     and not callable(target)
        #     and not ismethod(target)
        #     or target is None
        # ):
        #     raise Exception("`target` is not a valid type")

        target_metadata = self._get_or_create_metadata(target, create=True)
        if target_metadata is not None:
            existing = target_metadata.get(metadata_key)
            if existing is not None:
                update_callback: t.Callable[[t.Any, t.Any], t.Any] = (
                    self._data_type_update_callbacks.get(
                        type(existing), self._default_update_callback
                    )
                )
                metadata_value = update_callback(existing, metadata_value)
            target_metadata[metadata_key] = metadata_value

    def metadata(self, metadata_key: str, metadata_value: t.Any) -> t.Any:
        """
        Decorator to define metadata on a class or function.

        :param metadata_key: The key for the metadata.
        :param metadata_value: The value of the metadata.
        :return: A decorator function.
        """

        def _wrapper(target: t.Any) -> t.Any:
            self.define_metadata(metadata_key, metadata_value, target)
            return target

        return _wrapper

    def has_metadata(self, metadata_key: str, target: t.Any) -> bool:
        """
        Check if metadata key exists for a target.

        :param metadata_key: The key to check.
        :param target: The target object.
        :return: True if metadata key exists, False otherwise.
        """
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        return metadata_key in target_metadata

    def get_metadata(self, metadata_key: str, target: t.Any) -> t.Optional[t.Any]:
        """
        Retrieve metadata value for a target.

        :param metadata_key: The key to retrieve.
        :param target: The target object.
        :return: The metadata value or None if not found.
        """
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        value = target_metadata.get(metadata_key)
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def get_metadata_search_safe(self, metadata_key: str, target: t.Any) -> t.Any:
        """
        Retrieve metadata value safely. Raises KeyError if key is not found in the target's metadata.
        This behaves like `dict[key]`.

        :param metadata_key: The key to retrieve.
        :param target: The target object.
        :return: The metadata value.
        """
        _target_actual = _get_actual_target(target)
        meta = self._meta_data[_target_actual]

        value = meta[metadata_key]
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def get_metadata_or_raise_exception(
        self, metadata_key: str, target: t.Any
    ) -> t.Any:
        """
        Retrieve metadata or raise an Exception if not found.

        :param metadata_key: The key to retrieve.
        :param target: The target object.
        :return: The metadata value.
        :raises Exception: If metadata key is not found.
        """
        value = self.get_metadata(metadata_key=metadata_key, target=target)
        if value is not None:
            return value
        raise Exception("MetaData Key not Found")

    def get_metadata_keys(self, target: t.Any) -> t.KeysView[t.Any]:
        """
        Get all metadata keys for a target.

        :param target: The target object.
        :return: A view of the metadata keys.
        """
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        return target_metadata.keys()

    def get_all_metadata(self, target: t.Any) -> t.Dict:
        """
        Get all metadata for a target as a dictionary.

        :param target: The target object.
        :return: A dictionary containing all metadata.
        """
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}
        return type(target_metadata)(target_metadata)

    def delete_all_metadata(self, target: t.Any) -> None:
        """
        Delete all metadata for a target.

        :param target: The target object.
        """
        _target = _get_actual_target(target)
        if _target in self._meta_data:
            self._meta_data.pop(_target)

    def delete_metadata(self, metadata_key: str, target: t.Any) -> t.Any:
        """
        Delete a specific metadata key for a target.

        :param metadata_key: The key to delete.
        :param target: The target object.
        :return: The deleted value or None.
        """
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        if target_metadata and metadata_key in target_metadata:
            value = target_metadata.pop(metadata_key)
            if isinstance(value, (list, set, tuple, dict)):
                # return immutable value
                return type(value)(value)
            return value

    def _get_or_create_metadata(
        self, target: t.Any, create: bool = False
    ) -> t.Optional[t.Dict]:
        _target = _get_actual_target(target)
        if _target in self._meta_data:
            return self._meta_data[_target]

        if create:
            self._meta_data[_target] = {}
            return self._meta_data[_target]
        return None

    def _clone_meta_data(
        self,
    ) -> t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict]:
        _meta_data: t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict] = (
            WeakKeyDictionary()
        )
        for k, v in self._meta_data.items():
            _meta_data[k] = dict(v)
        return _meta_data

    @asynccontextmanager
    async def async_context(self) -> t.AsyncGenerator[None, None]:
        """
        Async context manager that isolates metadata changes within the context.
        Metadata changes made inside the context are discarded after exit.
        """
        cached_meta_data = self._clone_meta_data()
        yield
        reflect._meta_data.clear()
        reflect._meta_data = WeakKeyDictionary(dict=cached_meta_data)

    @contextmanager
    def context(self) -> t.Generator:
        """
        Context manager that isolates metadata changes within the context.
        Metadata changes made inside the context are discarded after exit.
        """
        cached_meta_data = self._clone_meta_data()
        yield
        reflect._meta_data.clear()
        reflect._meta_data = WeakKeyDictionary(dict=cached_meta_data)


def _list_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    """
    Update callback for list/tuple types. Concatenates the new value to the existing value.

    :param existing_value: The existing list or tuple.
    :param new_value: The new list or tuple.
    :return: The concatenated list or tuple.
    """
    if isinstance(existing_value, (list, tuple)) and isinstance(
        new_value, (list, tuple)
    ):
        return existing_value + type(existing_value)(new_value)  # type: ignore
    return new_value


def _set_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    """
    Update callback for set types. Unions the new value with the existing value.

    :param existing_value: The existing set.
    :param new_value: The new set.
    :return: The union of the sets.
    """
    if isinstance(existing_value, set) and isinstance(new_value, set):
        existing_combined = list(existing_value) + list(new_value)
        return type(existing_value)(existing_combined)
    return new_value


def _dict_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    """
    Update callback for dict types. Updates the existing dictionary with new values.

    :param existing_value: The existing dictionary.
    :param new_value: The new dictionary.
    :return: The updated dictionary.
    """
    if isinstance(
        existing_value, (dict, WeakKeyDictionary, WeakValueDictionary)
    ) and isinstance(new_value, (dict, WeakKeyDictionary, WeakValueDictionary)):
        existing_value.update(new_value)
        return type(existing_value)(existing_value)
    return new_value


reflect = _Reflect()

reflect.add_type_update_callback(tuple, _list_update)
reflect.add_type_update_callback(list, _list_update)
reflect.add_type_update_callback(set, _set_update)
reflect.add_type_update_callback(dict, _dict_update)
reflect.add_type_update_callback(WeakKeyDictionary, _dict_update)
reflect.add_type_update_callback(WeakValueDictionary, _dict_update)
