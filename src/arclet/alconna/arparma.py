from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar, overload, Generic, Mapping, Callable
from types import MappingProxyType
from contextlib import suppress
from typing_extensions import Self

from nepattern import Empty
from .util import get_signature
from .typing import TDataCollection
from .config import config
from .manager import command_manager
from .model import SubcommandResult, OptionResult, HeadResult
from .exceptions import BehaveCancelled, OutBoundsBehave
from .components.behavior import T_ABehavior, requirement_handler
from .components.duplication import Duplication, generate_duplication

T = TypeVar('T')
T_Duplication = TypeVar('T_Duplication', bound=Duplication)


@dataclass
class Arparma(Generic[TDataCollection]):
    """
    承载解析结果与操作数据的接口类
    """
    _source: str
    origin: TDataCollection
    matched: bool = field(default=False)
    header_match: HeadResult = field(default=HeadResult())
    error_data: list[str | Any] = field(default_factory=list)
    error_info: str | BaseException | type[BaseException] = field(default='')
    main_args: dict[str, Any] = field(default_factory=dict)
    other_args: dict[str, Any] = field(default_factory=dict)
    options: dict[str, OptionResult] = field(default_factory=dict)
    subcommands: dict[str, SubcommandResult] = field(default_factory=dict)

    def _clr(self):
        ks = list(self.__dict__.keys())
        for k in ks:
            delattr(self, k)

    @property
    def source(self):
        return command_manager.get_command(self._source)

    @property
    def header(self) -> dict[str, str]:
        """返回可能解析到的命令头中的信息"""
        return self.header_match.groups

    @property
    def header_matched(self):
        return self.header_match.matched

    @property
    def header_result(self):
        return self.header_match.result

    @property
    def non_component(self) -> bool:
        return not self.subcommands and not self.options

    @property
    def components(self) -> dict[str, OptionResult | SubcommandResult]:
        return {**self.options, **self.subcommands}

    @property
    def all_matched_args(self) -> dict[str, Any]:
        """返回 Alconna 中所有 Args 解析到的值"""
        return {**self.main_args, **self.other_args}

    def get_duplication(self, dup: type[T_Duplication] | None = None) -> T_Duplication:
        return (dup(self.source) if dup else generate_duplication(self.source)).set_target(self)  # type: ignore

    def encapsulate_result(
        self,
        main_args: dict[str, Any],
        options: dict[str, OptionResult],
        subcommands: dict[str, SubcommandResult]
    ) -> None:
        """处理 Arparma 中的数据"""
        self.main_args = main_args.copy()
        self.options = options.copy()
        self.subcommands = subcommands.copy()
        for v in options.values():
            self.other_args = {**self.other_args, **v.args}
        for k in subcommands:
            v = subcommands[k]
            self.other_args = {**self.other_args, **v.args}
            if sub_opts := v.options:
                for vv in sub_opts.values():
                    self.other_args = {**self.other_args, **vv.args}

    @staticmethod
    def behave_cancel():
        raise BehaveCancelled

    @staticmethod
    def behave_fail():
        raise OutBoundsBehave

    def execute(self, behaviors: list[T_ABehavior] | None = None) -> Self:
        if behaviors := (self.source.behaviors[1:] + (behaviors or [])):
            exc_behaviors = []
            for behavior in behaviors:
                exc_behaviors.extend(requirement_handler(behavior))
            for b in exc_behaviors:
                try:
                    b.operate(self)  # type: ignore
                except BehaveCancelled:
                    continue
                except OutBoundsBehave as e:
                    return self._fail(e)
        return self

    def call(self, target: Callable[..., T], **additional):
        if self.matched:
            names = tuple(p.name for p in get_signature(target))
            return target(**{k: v for k, v in {**self.all_matched_args, **additional}.items() if k in names})
        raise RuntimeError

    def _fail(self, exc: type[BaseException] | BaseException | str):
        return Arparma(self._source, self.origin, matched=False, error_info=exc)

    def __require__(self, parts: list[str]) -> tuple[dict[str, Any] | OptionResult | SubcommandResult | None, str]:
        """如果能够返回, 除开基本信息, 一定返回该path所在的dict"""
        if len(parts) == 1:
            part = parts[0]
            for src in (self.main_args, self.other_args, self.options, self.subcommands):
                if part in src:
                    return src, part
            if part in {"options", "subcommands", "main_args", "other_args"}:
                return getattr(self, part, {}), ''
            return (self.all_matched_args, '') if part == "args" else (None, part)
        prefix = parts.pop(0)  # parts[0]
        if prefix in {"options", "subcommands"} and prefix in self.components:
            raise RuntimeError(config.lang.arpamar_ambiguous_name.format(target=prefix))

        def _handle_opt(_pf: str, _parts: list[str], _opts: dict[str, OptionResult]):
            if _pf == "options":
                _pf = _parts.pop(0)
            if not _parts:  # options.foo or foo
                return _opts, _pf
            elif not (__src := _opts.get(_pf)):  # options.foo.bar or foo.bar
                return _opts, _pf
            if _end := _parts.pop(0) == "value":
                return __src, _end
            if _end == 'args':
                return (__src.args, _parts.pop(0)) if _parts else (__src, _end)
            return __src.args, _end

        if prefix == "options" or prefix in self.options:
            return _handle_opt(prefix, parts, self.options)
        if prefix == "subcommands" or prefix in self.subcommands:
            if prefix == "subcommands":
                prefix = parts.pop(0)
            if not parts: # subcommands.foo or foo
                return self.subcommands, prefix
            elif not (_src := self.subcommands.get(prefix)):  # subcommands.foo.bar or foo.bar
                return self.subcommands, prefix
            if (end := parts.pop(0)) == "value":
                return _src, end
            if end == 'args':
                return (_src.args, parts.pop(0)) if parts else (_src, end)
            if end == "options" and (end in _src.options or not parts):
                raise RuntimeError(config.lang.arpamar_ambiguous_name.format(target=f"{prefix}.{end}"))
            if end == "options" or end in _src.options:
                return _handle_opt(end, parts, _src.options)
            return _src.args, end
        prefix = prefix.replace("$main", "main_args").replace("$other", "other_args")
        if prefix in {"main_args", "other_args"}:
            return getattr(self, prefix, {}), parts.pop(0)
        return None, prefix

    @overload
    def query(self, path: str) -> Mapping[str, Any] | Any | None:
        ...

    @overload
    def query(self, path: str, default: T) -> T | Mapping[str, Any] | Any:
        ...

    def query(self, path: str, default: T | None = None) -> Any | Mapping[str, Any] | T | None:
        """根据path查询值"""
        source, endpoint = self.__require__(path.split('.'))
        if source is None:
            return default
        return source.get(endpoint, default) if endpoint else MappingProxyType(source)

    # def update(self, path: str, value: Any):
    #     """根据path更新值"""
    #     parts = path.split('.')
    #     source, endpoint = self.__require__(parts)
    #     if source is None:
    #         return
    #     if endpoint:
    #         self._record.add(path)
    #         source[endpoint] = value
    #     elif isinstance(value, dict):
    #         source.update(value)  # type: ignore
    #         self._record.update([f"{path}.{k}" for k in value])

    def query_with(self, arg_type: type[T], path: str | None = None, default: T | None = None) -> T | None:
        """根据类型查询参数"""
        if path:
            return res if isinstance(res := self.query(path, Empty), arg_type) else default
        with suppress(IndexError):
            return [v for v in self.all_matched_args.values() if isinstance(v, arg_type)][0]
        return default

    def find(self, path: str) -> bool:
        """查询路径是否存在"""
        return self.query(path, Empty) != Empty

    # def clean(self):
    #     if not self._record:
    #         return
    #     for path in self._record:
    #         parts = path.split('.')
    #         source, _ = self.__require__(parts[:-1])
    #         if not source:
    #             return
    #         source.pop(parts[-1], None)

    @overload
    def __getitem__(self, item: type[T]) -> T | None:
        ...

    @overload
    def __getitem__(self, item: str) -> Any:
        ...

    def __getitem__(self, item: str | type[T]) -> T | Any | None:
        if isinstance(item, str):
            return self.query(item)
        if data := self.query_with(item):
            return data

    def __getattr__(self, item):
        return self.all_matched_args.get(item)

    def __repr__(self):
        if self.error_info:
            attrs = ((s, getattr(self, s, None)) for s in ["matched", "head_matched", "error_data", "error_info"])
            return ", ".join(f"{a}={v}" for a, v in attrs if v is not None)
        else:
            attrs = [(s, getattr(self, s, None)) for s in ["matched", "header", "options", "subcommands"]]
            margs = self.main_args.copy()
            margs.pop('$varargs', None)
            margs.pop('$kwargs', None)
            margs.pop('$kwonly', None)
            attrs.append(("main_args", margs))
            other_args = self.other_args.copy()
            other_args.pop('$varargs', None)
            other_args.pop('$kwargs', None)
            other_args.pop('$kwonly', None)
            attrs.append(("other_args", other_args))
            return ", ".join(f"{a}={v}" for a, v in attrs if v)
