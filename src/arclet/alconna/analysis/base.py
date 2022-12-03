from collections import namedtuple
from typing import TYPE_CHECKING, Union, Callable, List, Any, Tuple, Dict
import traceback

from .analyser import Analyser, TAnalyser
from .parts import analyse_args as ala, analyse_header as alh, analyse_option as alo, analyse_subcommand as als
from ..typing import DataCollection, TDataCollection
from ..base import Option, Subcommand, Sentence
from ..args import Args
from ..config import config

if TYPE_CHECKING:
    from ..arparma import Arparma
    from ..core import Alconna


def _compile_opts(option: Option, data: Dict[str, Union[Sentence, List[Option]]]):
    for alias in option.aliases:
        if (li := data.get(alias)) and isinstance(li, list):
            li.append(option)  # type: ignore
            li.sort(key=lambda x: x.priority, reverse=True)
        else:
            data[alias] = [option]


def default_params_parser(analyser: "Analyser"):
    require_len = 0
    for opts in analyser.alconna.options:
        if isinstance(opts, Option):
            _compile_opts(opts, analyser.command_params)  # type: ignore
            analyser.param_ids.update(opts.aliases)
        elif isinstance(opts, Subcommand):
            sub_require_len = 0
            analyser.command_params[opts.name] = opts
            analyser.param_ids.add(opts.name)
            for sub_opts in opts.options:
                _compile_opts(sub_opts, opts.sub_params)
                if sub_opts.requires:
                    sub_require_len = max(len(sub_opts.requires), sub_require_len)
                    for k in sub_opts.requires:
                        opts.sub_params.setdefault(k, Sentence(name=k))
                analyser.param_ids.update(sub_opts.aliases)
            opts.sub_part_len = range(len(opts.options) + (1 if opts.nargs else 0) + sub_require_len)
        if not set(analyser.separators).issuperset(opts.separators):
            analyser.default_separate &= False
        if opts.requires:
            analyser.param_ids.update(opts.requires)
            require_len = max(len(opts.requires), require_len)
            for k in opts.requires:
                analyser.command_params.setdefault(k, Sentence(name=k))
        analyser.part_len = range(
            len(analyser.alconna.options) + analyser.need_main_args + require_len
        )


def compile(alconna: "Alconna", params_parser: Callable[[TAnalyser], None] = default_params_parser) -> TAnalyser:
    _analyser = alconna.analyser_type(alconna)
    params_parser(_analyser)
    return _analyser


def analyse(alconna: "Alconna", command: TDataCollection) -> "Arparma[TDataCollection]":
    return compile(alconna).process(command).analyse().execute()


class AnalyseError(Exception):
    """分析时发生错误"""


class _DummyAnalyser(Analyser):
    filter_out = []

    class _DummyALC:
        options = []
        meta = namedtuple("Meta", ["keep_crlf", "fuzzy_match"])(False, False)
        namespace_config = config.default_namespace

    def __new__(cls, *args, **kwargs):
        cls.alconna = cls._DummyALC()  # type: ignore
        cls.command_params = {}
        cls.param_ids = set()
        cls.default_separate = True
        cls.context = None
        cls.message_cache = False
        cls.filter_crlf = True
        cls.special = {}
        for i in config.default_namespace.builtin_option_name.values():
            cls.special.fromkeys(i, True)  # noqa
        return super().__new__(cls)

    def analyse(self, message=None, interrupt=False):
        pass


def analyse_args(args: Args, command: DataCollection[Union[str, Any]], raise_exception: bool = True):
    _analyser = _DummyAnalyser.__new__(_DummyAnalyser)
    _analyser.reset()
    _analyser.separators = (' ', )
    _analyser.need_main_args = True
    _analyser.raise_exception = True
    try:
        _analyser.process(command)
        return ala(_analyser, args, len(args))
    except Exception as e:
        if raise_exception:
            traceback.print_exception(AnalyseError, e, e.__traceback__)
        return


def analyse_header(
        headers: Union[List[Union[str, Any]], List[Tuple[Any, str]]],
        command_name: str,
        command: DataCollection[Union[str, Any]],
        sep: str = " ",
        raise_exception: bool = True
):
    _analyser = _DummyAnalyser.__new__(_DummyAnalyser)
    _analyser.reset()
    _analyser.separators = (sep, )
    _analyser.need_main_args = False
    _analyser.raise_exception = True
    _analyser.__init_header__(command_name, headers)
    try:
        _analyser.process(command)
        return alh(_analyser)
    except Exception as e:
        if raise_exception:
            traceback.print_exception(AnalyseError, e, e.__traceback__)
        return


def analyse_option(option: Option, command: DataCollection[Union[str, Any]], raise_exception: bool = True):
    _analyser = _DummyAnalyser.__new__(_DummyAnalyser)
    _analyser.reset()
    _analyser.separators = (" ", )
    _analyser.need_main_args = False
    _analyser.raise_exception = True
    _analyser.alconna.options.append(option)
    default_params_parser(_analyser)
    _analyser.alconna.options.clear()
    try:
        _analyser.process(command)
        return alo(_analyser, option)
    except Exception as e:
        if raise_exception:
            traceback.print_exception(AnalyseError, e, e.__traceback__)
        return


def analyse_subcommand(subcommand: Subcommand, command: DataCollection[Union[str, Any]], raise_exception: bool = True):
    _analyser = _DummyAnalyser.__new__(_DummyAnalyser)
    _analyser.reset()
    _analyser.separators = (" ", )
    _analyser.need_main_args = False
    _analyser.raise_exception = True
    _analyser.alconna.options.append(subcommand)
    default_params_parser(_analyser)
    _analyser.alconna.options.clear()
    try:
        _analyser.process(command)
        return als(_analyser, subcommand)
    except Exception as e:
        if raise_exception:
            traceback.print_exception(AnalyseError, e, e.__traceback__)
        return
