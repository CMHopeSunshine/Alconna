import sys
from typing import Dict, Any
import re
import json

from arclet.alconna import Alconna, Args, Arpamar, Option, AnyUrl, AnyIP, AnyDigit, AnyFloat, AllParam, Email, Bool, \
    command_manager, all_command_help, alconna_version
from arclet.alconna.types import ArgPattern, PatternToken

cache_data: Dict[str, Any] = {}

list_type = ArgPattern(
    r"\[(.*?)]",
    token=PatternToken.REGEX_TRANSFORM,
    type_mark=list,
    transform_action=lambda x: x.split(",")
)

args_type = ArgPattern(
    r"(\[.+])*",
    token=PatternToken.REGEX_TRANSFORM,
    type_mark=list,
    transform_action=lambda x: [re.split("[:|=]", p) for p in re.findall(r"\[(.*?)]", x)]
)


create = Alconna(
    command="create",
    options=[
        Option("--command|-C", Args["command_name":str]).help("指定命令名称"),
        Option("--header|-H", Args["command_header":list_type]).help("传入命令头"),
        Option("--option|-O", Args["option_name":str]["option_args":args_type:[]]).help("创建命令选项"),
        Option("--analysed|-A").help("从已经分析的命令结构中创建Alconna")
    ],
    namespace="ALCLI"
).help("开始创建 Alconna 命令")

analysis = Alconna(
    command="analysis",
    main_args=Args["command":AllParam],
    namespace="ALCLI"
).help("分析命令并转换为 Alconna 命令结构")

help_find = Alconna(
    command="help",
    main_args=Args["target":str],
    namespace="ALCLI"
).help("展示指定Alconna组件的帮助信息")

using = Alconna(
    command="using",
    main_args=Args["command":AllParam],
    namespace="ALCLI"
).help("依据创建的 Alconna 来解析输入的命令")


def command_create(result: Arpamar):
    global cache_data
    analysed = result.has("analysed")
    command = result.get('command')
    option = result.get('option')
    header = result.get('header')
    if analysed:
        try:
            analysed_args = cache_data['ALCLI::analysis']
        except KeyError:
            print("请先分析命令")
            return
        header_text = analysed_args.get("header")
        options = analysed_args.get("options")
        command_name = analysed_args.get("command")
        option_text = ""
        if options:
            option_text = "\n    options=[\n"
            for option in options:
                _opt_name = option.get("name")
                _opt_args = option.get("args")
                if _opt_args:
                    _opt_args_text = "Args["
                    for _opt_arg_name, _opt_arg_value in _opt_args.items():
                        _opt_args_text += f"\"{_opt_arg_name}\": {_opt_arg_value.split('%')[1]}, "
                    _opt_args_text = _opt_args_text[:-2] + "]"
                    _opt = f"\tOption(\"{_opt_name}\", {_opt_args_text}),\n"
                else:
                    _opt = f"\tOption(\"{_opt_name}\"),\n"
                option_text += _opt
            option_text = option_text[:-2] + "\n    ],"

        if header_text:
            construct_command = f"Alconna(\n" \
                                f"    header={header_text},\n" \
                                f"    command=\"{command_name}\"," \
                                f"    {option_text}\n" \
                                f")"
        else:
            construct_command = f"Alconna(\n" \
                                f"    command=\"{command_name}\"," \
                                f"    {option_text}\n" \
                                f")"
        print(construct_command)
        cache_data['ALCLI::create'] = construct_command
        return
    if not command:
        print("你没有指定命令名称")
        return
    option_texts = []
    if option:
        if isinstance(option, list):
            for o in option:
                opt_name = o['option_name']
                if o['option_args']:
                    arg_text = "["
                    for arg in o['option_args']:
                        arg[1] = f'"{arg[1]}"' if arg[1] not in ["str", "int", "float", "bool", "..."] else arg[1]
                        arg_text += f'"{arg[0]}":{arg[1]}' + ", "
                    arg_text = arg_text[:-2] + "]"
                    option_texts.append(f'Option("{opt_name}", Args{arg_text}),')
                else:
                    option_texts.append(f'Option("{opt_name}"),')
        else:
            opt_name = option['option_name']
            if option['option_args']:
                arg_text = "["
                for arg in option['option_args']:
                    arg[1] = f'"{arg[1]}"' if arg[1] not in ["str", "int", "float", "bool", "..."] else arg[1]
                    arg_text += f'"{arg[0]}":{arg[1]}' + ", "
                arg_text = arg_text[:-2] + "]"
                option_texts.append(f'Option("{opt_name}", Args{arg_text}),')
            else:
                option_texts.append(f'Option("{opt_name}"),')
    option_text = ("\n    options=[\n\t" + "\n\t".join(option_texts) + "\n    ],") if option_texts else ""
    if header:
        header_text = "["
        for h in header:
            header_text += f'"{h}", '
        header_text = header_text[:-2] + "]"
        construct_command = f"Alconna(\n" \
                            f"    header={header_text},\n" \
                            f"    command=\"{command['command_name']}\"," \
                            f"    {option_text}\n" \
                            f") "
    else:
        construct_command = f"Alconna(\n" \
                            f"    command=\"{command['command_name']}\"," \
                            f"    {option_text}\n" \
                            f")"
    print(construct_command)
    cache_data['ALCLI::create'] = construct_command
    return


def command_help(result: Arpamar):
    target = result.target
    try:
        print(eval(target).__doc__)
    except NameError:
        print("没有找到指定的组件")


def command_analysis(arpamar: Arpamar):
    global cache_data
    command = arpamar.command
    result = {}
    command_parts = command[0].split(" ")
    command_headers = command_parts.pop(0)
    if re.match(r"\W.*?", command_headers):
        result['header'] = [command_headers[0]]
        result['command'] = command_headers[1:]
    else:
        result['command'] = command_headers
    if command_parts:
        result['options'] = []
        for i, part in enumerate(command_parts):
            if part.startswith("--"):
                _option = {"type": "Option", "name": part}
                _args = {}
                _arg_index = 0
                while i < len(command_parts) - 1:
                    i += 1
                    _arg_index += 1
                    if command_parts[i].startswith("--"):
                        break
                    _arg_key = f"{part[2:]}_arg_{_arg_index}"
                    if AnyDigit.find(command_parts[i]):
                        command_parts[i] += "%int"
                    elif AnyFloat.find(command_parts[i]):
                        command_parts[i] += "%float"
                    elif Bool.find(command_parts[i]):
                        command_parts[i] += "%bool"
                    elif AnyIP.find(command_parts[i]):
                        command_parts[i] += "%\"ip\""
                    elif AnyUrl.find(command_parts[i]):
                        command_parts[i] += "%\"url\""
                    elif Email.find(command_parts[i]):
                        command_parts[i] += "%\"email\""
                    else:
                        command_parts[i] += "%str"
                    _args[_arg_key] = command_parts[i]
                if _args:
                    _option['args'] = _args
                result['options'].append(_option)
    cache_data['ALCLI::analysis'] = result
    print(result)


def command_using(arpamar: Arpamar):
    global cache_data
    command = arpamar.command
    try:
        construct_command = cache_data['ALCLI::create']
    except KeyError:
        print("请先创建命令")
        return
    using_result = {}
    exec(
        "alc = " + construct_command,
        globals(),
        using_result
    )
    alc = using_result['alc']
    alc.set_namespace("ALCLI/USING")
    result = alc.analyse_message(command[0])
    if result.matched:
        print(
            f"Your command is successfully matched!"
            f"\nThe results："
            f"\n - Header: {result.header}"
            f"\n - Command: {result.main_args}"
            f"\n - Options: {result.options}"
            f"\n - Arguments: {result.all_matched_args}"
        )
    else:
        print(
            f"Your command matched failed."
            f"\nError Data: {result.error_data}"
        )


def main(args=None):
    """
    Main entry point for the application.

    :param args: command line arguments
    :type args: list
    """
    global cache_data
    if args is None:
        args = sys.argv[1:]
    if not args:
        print("* Alconna CLI %d.%d.%d\n" % alconna_version + all_command_help(namespace="ALCLI"))
        return
    try:
        with open('alconna_cache.json', 'r+', encoding='UTF-8') as f_obj:
            cache_data = json.load(f_obj)
    except FileNotFoundError:
        cache_data = {}
    text = " ".join(args)
    if text == "--help":
        print("* Alconna CL\n" + all_command_help("ALCLI"))
        return
    for alc in command_manager.get_commands("ALCLI"):
        result = alc.analyse_message(text)
        if result.matched:
            eval("command_" + alc.command)(result)
    with open('alconna_cache.json', 'w+', encoding='UTF-8') as f_obj:
        json.dump(cache_data, f_obj, ensure_ascii=False)