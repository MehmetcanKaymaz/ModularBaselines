from typing import Any, Callable, Dict, List, Optional, Union, Type


class DataLog():

    def __init__(self, formatting: Optional[Callable[[Any], str]] = None) -> None:
        self.value = None
        self.formatting = formatting

    def push(self, value: Any) -> None:
        self.value = value

    def dump(self) -> Any:
        value = self.value
        self.value = None
        return value


class ListLog(DataLog):

    def __init__(self, formatting: Optional[Callable[[List[Any]], str]] = None) -> None:
        self.values = []
        self.formatting = formatting

    def push(self, value: Any) -> None:
        self.values.append(value)

    def dump(self) -> List[Any]:
        values = self.values
        self.values = []
        return values

    def _reduce(self, reduction_fn: Callable[[List[Any]], Any]) -> Any:
        return reduction_fn(self.value)


class QueueLog(DataLog):

    def __init__(self) -> None:
        raise NotImplementedError


class DictLog(DataLog):

    def __init__(self) -> None:
        raise NotImplementedError


class DataLogger():

    def __init__(self, **data_logs: Optional[DataLog]) -> None:
        for name, data_log in data_logs.items():
            self.__setattr__(name, data_log)

    def dump(self) -> None:
        return {name: value.dump() for name, value in self.__dict__.items() if isinstance(value, DataLog)}

    def __setattr__(self, __name: str, __value: Any) -> None:
        if isinstance(__value, DataLog):
            self.__dict__[__name] = __value
        else:
            raise ValueError("Only DataLogs are supported for assignments")

    def check_attributes(self, names: List[str]) -> bool:
        for name in names:
            if name not in self.__dict__.keys():
                raise ValueError(f"Missing Data logger attribute: {name}")
        return True

    def add_if_not_exists(self, loggers: Dict[str, DataLog]):
        for name, data_logger in loggers.items():
            if name not in self.__dict__.keys():
                setattr(self, name, data_logger)
