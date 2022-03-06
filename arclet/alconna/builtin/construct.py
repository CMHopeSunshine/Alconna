import asyncio
from asyncio import AbstractEventLoop
import sys
import re
import inspect
from functools import partial
from types import FunctionType, MethodType, ModuleType
from typing import Dict, Any, Optional, Callable, Union, TypeVar, List, Type, FrozenSet, Literal, get_args

from arclet.alconna.types import MessageChain
from arclet.alconna.builtin.actions import store_bool, store_const
from arclet.alconna.main import Alconna
from arclet.alconna.component import Option, Subcommand
from arclet.alconna.base import Args, TAValue, ArgAction
from arclet.alconna.util import split, split_once

PARSER_TYPE = Callable[[Callable, Dict[str, Any], Optional[Dict[str, Any]], Optional[AbstractEventLoop]], Any]


def default_parser(
        func: Callable,
        args: Dict[str, Any],
        local_arg: Optional[Dict[str, Any]],
        loop: Optional[AbstractEventLoop]
) -> Any:
    return func(**args, **local_arg)


class ALCCommand:
    """
    以 click-like 方法创建的 Alconna 结构体, 可以被视为一类 CommanderHandler
    """
    command: Alconna
    parser_func: PARSER_TYPE
    local_args: Dict[str, Any]
    exec_target: Callable = None
    loop: AbstractEventLoop

    def __init__(
            self,
            command: Alconna,
            target: Callable,
            loop: AbstractEventLoop,
    ):
        self.command = command
        self.exec_target = target
        self.loop = loop
        self.parser_func = default_parser
        self.local_args = {}

    def set_local_args(self, local_args: Optional[Dict[str, Any]] = None):
        """
        设置本地参数

        Args:
            local_args (Optional[Dict[str, Any]]): 本地参数
        """
        self.local_args = local_args

    def set_parser(self, parser_func: PARSER_TYPE):
        """
        设置解析器

        Args:
            parser_func (PARSER_TYPE): 解析器, 接受的参数必须为 (func, args, local_args, loop)
        """
        self.parser_func = parser_func
        return self

    def __call__(self, message: Union[str, MessageChain]) -> Any:
        if not self.exec_target:
            raise Exception("This must behind a @xxx.command()")
        result = self.command.parse(message)
        if result.matched:
            self.parser_func(self.exec_target, result.all_matched_args, self.local_args, self.loop)

    def from_commandline(self):
        """从命令行解析参数"""
        if not self.command:
            raise Exception("You must call @xxx.command() before @xxx.from_commandline()")
        args = sys.argv[1:]
        args.insert(0, self.command.command)
        self.__call__(" ".join(args))


F = TypeVar("F", bound=Callable[..., Any])
FC = TypeVar("FC", bound=Union[Callable[..., Any], ALCCommand])


# ----------------------------------------
# click-like
# ----------------------------------------


class AlconnaDecorate:
    """
    Alconna Click-like 构造方法的生成器

    Examples:
        >>> cli = AlconnaDecorate()
        >>> @cli.build_command()
        ... @cli.option("--name|-n", Args["name":str:"your name"])
        ... @cli.option("--age|-a", Args["age":int:"your age"])
        ... def hello(name: str, age: int):
        ...     print(f"Hello {name}, you are {age} years old.")
        ...
        >>> hello("hello --name Alice --age 18")

    Attributes:
        namespace (str): 命令的命名空间
        loop (AbstractEventLoop): 事件循环
    """
    namespace: str
    loop: AbstractEventLoop
    building: bool
    __storage: Dict[str, Any]
    default_parser: PARSER_TYPE

    def __init__(
            self,
            namespace: str = "Alconna",
            loop: Optional[AbstractEventLoop] = None,
    ):
        """
        初始化构造器

        Args:
            namespace (str): 命令的命名空间
            loop (AbstractEventLoop): 事件循环
        """
        self.namespace = namespace
        self.building = False
        self.__storage = {"options": []}
        self.loop = loop or asyncio.new_event_loop()
        self.default_parser = default_parser

    def build_command(self, name: Optional[str] = None) -> Callable[[F], ALCCommand]:
        """
        开始构建命令

        Args:
            name (Optional[str]): 命令名称
        """
        self.building = True

        def wrapper(func: Callable[..., Any]) -> ALCCommand:
            if not self.__storage.get('func'):
                self.__storage['func'] = func
            command_name = name or self.__storage.get('func').__name__
            help_string = self.__storage.get('func').__doc__
            command = Alconna(
                command=command_name,
                options=self.__storage.get("options"),
                namespace=self.namespace,
                main_args=self.__storage.get("main_args"),
                help_text=help_string or command_name
            )
            self.building = False
            return ALCCommand(command, self.__storage.get('func'), self.loop).set_parser(self.default_parser)

        return wrapper

    def option(
            self,
            name: str,
            args: Optional[Args] = None,
            alias: Optional[str] = None,
            help: Optional[str] = None,
            action: Optional[Callable] = None,
            sep: str = " "
    ) -> Callable[[FC], FC]:
        """
        添加命令选项

        Args:
            name (str): 选项名称
            args (Optional[Args]): 选项参数
            alias (Optional[str]): 选项别名
            help (Optional[str]): 选项帮助信息
            action (Optional[Callable]): 选项动作
            sep (str): 参数分隔符
        """
        if not self.building:
            raise Exception("This must behind a @xxx.command()")

        def wrapper(func: FC) -> FC:
            if not self.__storage.get('func'):
                self.__storage['func'] = func
            self.__storage['options'].append(
                Option(name, args=args, alias=alias, actions=action, separator=sep, help_text=help or name)
            )
            return func

        return wrapper

    def arguments(self, args: Args) -> Callable[[FC], FC]:
        """
        添加命令参数

        Args:
            args (Args): 参数
        """
        if not self.building:
            raise Exception("This must behind a @xxx.command()")

        def wrapper(func: FC) -> FC:
            if not self.__storage.get('func'):
                self.__storage['func'] = func
            self.__storage['main_args'] = args
            return func

        return wrapper

    def set_default_parser(self, parser_func: PARSER_TYPE):
        """
        设置默认的参数解析器

        Args:
            parser_func (PARSER_TYPE): 参数解析器, 接受的参数必须为 (func, args, local_args, loop)
        """
        self.default_parser = parser_func
        return self


# ----------------------------------------
# format
# ----------------------------------------


def _from_format(
        format_string: str,
        format_args: Dict[str, Union[TAValue, Args, Option, List[Option]]]
) -> "Alconna":
    """
    以格式化字符串的方式构造 Alconna

    Examples:

    >>> from arclet.alconna import AlconnaFormat
    >>> alc1 = AlconnaFormat(
    ...     "lp user {target} perm set {perm} {default}",
    ...     {"target": str, "perm": str, "default": Args["de":bool:True]},
    ... )
    >>> alc1.parse("lp user AAA perm set admin.all False")
    """
    _key_ref = 0
    strings = split(format_string)
    command = strings.pop(0)
    options = []
    main_args = None

    _string_stack: List[str] = []
    for i, string in enumerate(strings):
        if not (arg := re.findall(r"{(.+)}", string)):
            _string_stack.append(string)
            _key_ref = 0
            continue
        _key_ref += 1
        key = arg[0]
        value = format_args[key]
        try:
            _param = _string_stack.pop(-1)
            if isinstance(value, Option):
                options.append(Subcommand(_param, [value]))
            elif isinstance(value, List):
                options.append(Subcommand(_param, value))
            elif _key_ref > 1 and isinstance(options[-1], Option):
                if isinstance(value, Args):
                    options.append(Subcommand(_param, [options.pop(-1)], args=value))
                else:
                    options.append(Subcommand(_param, [options.pop(-1)], args=Args(**{key: value})))
            elif isinstance(value, Args):
                options.append(Option(_param, args=value))
            else:
                options.append(Option(_param, Args(**{key: value})))
        except IndexError:
            if i == 0:
                if isinstance(value, Args):
                    main_args = value
                elif not isinstance(value, Option) and not isinstance(value, List):
                    main_args = Args(**{key: value})
            else:
                if isinstance(value, Option):
                    options.append(value)
                elif isinstance(value, List):
                    options[-1].options.extend(value)
                elif isinstance(value, Args):
                    options[-1].args = value
                else:
                    options[-1].args.argument.update({key: value})

    alc = Alconna(command=command, options=options, main_args=main_args)
    return alc


# ----------------------------------------
# koishi-like
# ----------------------------------------


def _from_string(
        command: str,
        *option: str,
        custom_types: Dict[str, Type] = None,
        sep: str = " "
) -> "Alconna":
    """
    以纯字符串的形式构造Alconna的简易方式, 或者说是koishi-like的方式

    Examples:

    >>> from arclet.alconna import AlconnaString
    >>> alc = AlconnaString(
    ... "test <message:str> #HELP_STRING",
    ... "--foo|-f <val:bool:True>", "--bar [134]"
    ... )
    >>> alc.parse("test abcd --foo True")
    """

    _options = []
    head, others = split_once(command, sep)
    headers = [head]
    if re.match(r"^\[(.+?)]$", head):
        headers = head.strip("[]").split("|")
    args = [re.split("[:|=]", p) for p in re.findall(r"<(.+?)>", others)]
    if not (help_string := re.findall(r"#(.+)", others)):
        help_string = headers
    if not custom_types:
        custom_types = Alconna.custom_types.copy()
    else:
        custom_types.update(Alconna.custom_types)
    custom_types.update(getattr(inspect.getmodule(inspect.stack()[1][0]), "__dict__", {}))
    _args = Args.from_string_list(args, custom_types.copy())
    for opt in option:
        if opt.startswith("--"):
            opt_head, opt_others = split_once(opt, sep)
            try:
                opt_head, opt_alias = opt_head.split("|")
            except ValueError:
                opt_alias = opt_head
            opt_args = [re.split("[:|=]", p) for p in re.findall(r"<(.+?)>", opt_others)]
            _opt_args = Args.from_string_list(opt_args, custom_types.copy())
            opt_action_value = re.findall(r"\[(.+?)]$", opt_others)
            if not (opt_help_string := re.findall(r"#(.+)", opt_others)):
                opt_help_string = [opt_head]
            if opt_action_value:
                val = eval(opt_action_value[0], {"true": True, "false": False})
                if isinstance(val, bool):
                    _options.append(Option(opt_head, alias=opt_alias, args=_opt_args, actions=store_bool(val)))
                else:
                    _options.append(Option(opt_head, alias=opt_alias, args=_opt_args, actions=store_const(val)))
            else:
                _options.append(Option(opt_head, alias=opt_alias, args=_opt_args))
            _options[-1].help_text = opt_help_string[0]
            _options[-1].__generate_help__()
    return Alconna(headers=headers, main_args=_args, options=_options, help_text=help_string[0])


config_key = Literal["headers", "raise_exception", "description", "get_subcommand", "extra", "namespace", "command"]


class AlconnaMounter(Alconna):
    mount_cls: Type
    instance: object
    config_keys: FrozenSet[str] = frozenset(get_args(config_key))

    def _instance_action(self, option_dict):
        if not self.instance:
            self.instance = self.mount_cls(**option_dict)
        else:
            for key, value in option_dict.items():
                setattr(self.instance, key, value)
        return option_dict

    def _inject_instance(self, target: Callable):
        return partial(target, self.instance)

    def _get_instance(self):
        return self.instance

    def _parse_action(self, message):
        ...

    def visit_config(self, obj: Any):
        config = inspect.getmembers(
            obj, predicate=lambda x: inspect.isclass(x) and x.__name__.endswith("Config")
        )
        result = {}
        if config:
            config = config[0][1]
            config_keys = list(filter(lambda x: not x.startswith("_"), dir(config)))
            for key in self.config_keys:
                if key in config_keys:
                    result[key] = getattr(config, key)
        return result

    def parse(self, message: Union[str, MessageChain], static: bool = True):
        message = self._parse_action(message) or message
        super(AlconnaMounter, self).parse(message, static)


class FuncMounter(AlconnaMounter):

    def __init__(self, func: Union[FunctionType, MethodType], config: Optional[dict] = None):
        config = config or self.visit_config(func)
        func_name = func.__name__
        if func_name.startswith("_"):
            raise ValueError("function name can not start with '_'")
        _args, method = Args.from_callable(func, extra=config.get("extra"))
        if method:
            self.instance = func.__self__
            func = partial(func, func.__self__)
        super(FuncMounter, self).__init__(
            headers=config.get("headers", None),
            command=config.get("command", func_name),
            main_args=_args,
            help_text=config.get("description", func.__doc__ or func_name),
            actions=func,
            is_raise_exception=config.get("raise_exception", True),
            namespace=config.get("namespace", None),
        )


class ClassMounter(AlconnaMounter):

    def __init__(self, mount_cls: Type, config: Optional[dict] = None):
        self.mount_cls = mount_cls
        self.instance: mount_cls = None
        config = config or self.visit_config(mount_cls)
        init = inspect.getfullargspec(mount_cls.__init__)
        members = inspect.getmembers(
            mount_cls, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x)
        )
        _options = []
        main_help_text = mount_cls.__doc__ or mount_cls.__init__.__doc__ or mount_cls.__name__

        if len(init.args + init.kwonlyargs) > 1:
            main_args = Args.from_callable(mount_cls.__init__, extra=config.get("extra"))[0]

            instance_handle = self._instance_action

            class _InstanceAction(ArgAction):
                def handle(self, option_dict, is_raise_exception):
                    return instance_handle(option_dict)

            inject = self._inject_instance

            class _TargetAction(ArgAction):
                origin: Callable

                def __init__(self, target: Callable):
                    self.origin = target
                    super().__init__(target)

                def handle(self, option_dict, is_raise_exception):
                    self.action = inject(self.origin)
                    return super().handle(option_dict, is_raise_exception)

                async def handle_async(self, option_dict, is_raise_exception):
                    self.action = inject(self.origin)
                    return await super().handle_async(option_dict, is_raise_exception)

            main_action = _InstanceAction()
            for name, func in members:
                if name.startswith("_"):
                    continue
                help_text = func.__doc__ or name
                _opt_args, method = Args.from_callable(func, extra=config.get("extra"))
                if method:
                    _options.append(Option(name, args=_opt_args, actions=_TargetAction(func), help_text=help_text))
                else:
                    _options.append(Option(name, args=_opt_args, actions=ArgAction(func), help_text=help_text))
            super().__init__(
                headers=config.get('headers', None),
                namespace=config.get('namespace', None),
                command=config.get('command', mount_cls.__name__),
                main_args=main_args,
                options=_options,
                help_text=config.get('description', main_help_text),
                is_raise_exception=config.get('raise_exception', True),
                actions=main_action,
            )
        else:
            for name, func in members:
                if name.startswith("_"):
                    continue
                help_text = func.__doc__ or name
                _opt_args, method = Args.from_callable(func, extra=config.get("extra"))
                if method:
                    func = partial(func, mount_cls)
                _options.append(Option(name, args=_opt_args, actions=ArgAction(func), help_text=help_text))
            super().__init__(
                headers=config.get('headers', None),
                namespace=config.get('namespace', None),
                command=config.get('command', mount_cls.__name__),
                options=_options,
                help_text=config.get('description', main_help_text),
                is_raise_exception=config.get('raise_exception', True),
            )

    def _parse_action(self, message):
        if self.instance:
            for k, a in self.args.argument.items():
                if hasattr(self.instance, k):
                    a['default'] = getattr(self.instance, k)
            self.__generate_help__()


class ModuleMounter(AlconnaMounter):

    def __init__(self, module: ModuleType, config: Optional[dict] = None):
        self.mount_cls = module.__class__
        self.instance = module
        config = config or self.visit_config(module)
        _options = []
        members = inspect.getmembers(
            module, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x)
        )
        for name, func in members:
            if name.startswith("_") or func.__name__.startswith("_"):
                continue
            help_text = func.__doc__ or name
            _opt_args, method = Args.from_callable(func, extra=config.get("extra"))
            if method:
                func = partial(func, func.__self__)
            _options.append(Option(name, args=_opt_args, actions=ArgAction(func), help_text=help_text))
        super().__init__(
            headers=config.get('headers', None),
            namespace=config.get('namespace', None),
            command=config.get('command', module.__name__),
            options=_options,
            help_text=config.get("description", module.__doc__ or module.__name__),
            is_raise_exception=config.get("raise_exception", True)
        )

    def _parse_action(self, message):
        if self.command.startswith("_"):
            if isinstance(message, str):
                message = self.command + " " + message
            else:
                message.inject(0, self.command)
        return message


class ObjectMounter(AlconnaMounter):

    def __init__(self, obj: object, config: Optional[dict] = None):
        self.mount_cls = type(obj)
        self.instance = obj
        config = config or self.visit_config(obj)
        obj_name = obj.__class__.__name__
        init = inspect.getfullargspec(obj.__init__)
        members = inspect.getmembers(
            obj, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x)
        )
        _options = []
        main_help_text = obj.__doc__ or obj.__init__.__doc__ or obj_name
        for name, func in members:
            if name.startswith("_"):
                continue
            help_text = func.__doc__ or name
            _opt_args, _ = Args.from_callable(func, extra=config.get("extra"))
            _options.append(Option(name, args=_opt_args, actions=ArgAction(func), help_text=help_text))
        if len(init.args) > 1:
            main_args = Args.from_callable(obj.__init__, extra=config.get("extra"))[0]
            for k, a in main_args.argument.items():
                if hasattr(self.instance, k):
                    a['default'] = getattr(self.instance, k)

            instance_handle = self._instance_action

            class _InstanceAction(ArgAction):

                def handle(self, option_dict: dict, is_raise_exception: bool):
                    return instance_handle(option_dict)

            main_action = _InstanceAction()
            super().__init__(
                headers=config.get('headers', None),
                command=config.get('command', obj_name),
                main_args=main_args,
                options=_options,
                help_text=config.get("description", main_help_text),
                is_raise_exception=config.get("raise_exception", True),
                actions=main_action,
                namespace=config.get('namespace', None)
            )
        else:
            super().__init__(
                headers=config.get('headers', None),
                command=config.get('command', obj_name),
                options=_options,
                namespace=config.get('namespace', None),
                help_text=config.get("description", main_help_text),
                is_raise_exception=config.get("raise_exception", True),
            )


def _from_object(
        target: Optional[Union[Type, object, FunctionType, MethodType, ModuleType]] = None,
        command: Optional[str] = None,
        config: Optional[Dict[config_key, Any]] = None,
) -> AlconnaMounter:
    """
    通过解析传入的对象，生成 Alconna 实例的方法，或者说是Fire-like的方式

    Examples:

    >>> from arclet.alconna import AlconnaFire
    >>> def test_func(a, b, c):
    ...     print(a, b, c)
    ...
    >>> alc = AlconnaFire(test_func)
    >>> alc.parse("test_func 1 2 3")
    """
    if inspect.isroutine(target):
        r = FuncMounter(target, config)
    elif inspect.isclass(target):
        r = ClassMounter(target, config)
    elif inspect.ismodule(target):
        r = ModuleMounter(target, config)
    else:
        if target:
            r = ObjectMounter(target, config)
        else:
            r = ModuleMounter(inspect.getmodule(inspect.stack()[1][0]), config)
    command = command or (sys.argv[1:] if len(sys.argv) > 1 else None)
    if command:
        r.parse(command)
    return r


AlconnaFormat = _from_format
AlconnaString = _from_string
AlconnaFire = _from_object
