import typing as t

from django.utils.module_loading import import_string
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core.core_schema import CoreSchema, with_info_plain_validator_function

from ninja_extra.lazy import LazyStrImport
from ninja_extra.shortcuts import fail_silently


class AllowTypeOfSource:
    def __init__(
        self,
        schema: t.Optional[t.Dict[str, t.Any]] = None,
        validator: t.Optional[t.Callable[..., bool]] = None,
        error_message: t.Optional[t.Callable[..., str]] = None,
    ) -> None:
        self._schema = schema
        self.validator = validator
        self.error_message = error_message

    def __get_pydantic_core_schema__(
        self,
        source: t.Type[t.Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def validate(value: t.Any, *args: t.Any) -> t.Any:
            if isinstance(value, str):
                try_import_value = fail_silently(import_string, value)
                if try_import_value is not None:
                    value = try_import_value
                else:
                    value = LazyStrImport(value)

            if (self.validator and not self.validator(source, value)) or (
                not self.validator and not isinstance(value, source)
            ):
                self._handle_error(source, value)
            return value

        return with_info_plain_validator_function(validate)

    def _handle_error(self, source: t.Any, value: t.Any) -> None:
        error_message = (
            f"Expected an instance of {source}, got an instance of {type(value)}"
            if self.error_message is None
            else self.error_message(source, value)
        )
        raise ValueError(error_message)

    def __get_pydantic_json_schema__(
        self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:  # pragma: no cover
        return self._schema  # type:ignore[return-value]
