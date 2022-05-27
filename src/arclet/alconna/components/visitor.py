"""
Alconna 负责命令节点访问与帮助文档生成的部分
"""
from typing import List, Dict, Optional, Any, Literal, Union, TYPE_CHECKING, Set
from ..exceptions import DuplicateCommand
from ..lang import lang_config
from ..base import CommandNode, Subcommand, Option
from .output import AbstractTextFormatter

if TYPE_CHECKING:
    from ..core import Alconna


class _BaseNode:
    """
    存储命令节点信息的基础类
    """
    node_id: int
    type: str
    name: str
    parameters: List[Dict[str, Any]]
    description: str
    separators: Set[str]
    param_separators: Set[str]
    sub_nodes: List[int]
    additional_info: Dict[str, Any]

    def __init__(self, nid: int, target: CommandNode, node_type: Literal['command', 'subcommand', 'option']):
        self.node_id = nid
        self.type = node_type
        self.separators = target.separators
        self.param_separators = target.args.separators
        self.additional_info = {'dest': target.dest}
        self.name = target.name
        self.description = target.help_text
        self.parameters = [
            {'name': key, **arg} for key, arg in target.args.argument.items()
        ]

        self.sub_nodes = []

    def __repr__(self):
        return f'[{self.name}, {self.description}; {self.parameters}; {self.sub_nodes}]'


class AlconnaNodeVisitor:
    """
    命令节点访问器

    该访问器会读取Alconna内的命令节点, 并转为节点树
    """
    name_list: List[str]
    node_map: Dict[int, _BaseNode]

    def __init__(self, alconna: "Alconna") -> None:
        self.name_list = [alconna.name]
        self.node_map = {0: _BaseNode(0, alconna, 'command')}
        self.node_map[0].additional_info['command'] = alconna.command
        self.node_map[0].additional_info['headers'] = alconna.headers
        self.node_map[0].additional_info['namespace'] = alconna.namespace

        for node in alconna.options:
            real_name = node.name.lstrip('-')
            if isinstance(node, Option):
                if f"option:{real_name}" in self.name_list:
                    raise DuplicateCommand(lang_config.visitor_duplicate_option.format(target=real_name))
                self.name_list.append(f"option:{real_name}")
            elif isinstance(node, Subcommand):
                if f"subcommand:{real_name}" in self.name_list:
                    raise DuplicateCommand(lang_config.visitor_duplicate_subcommand.format(target=real_name))
                self.name_list.append(f"subcommand:{real_name}")
            new_id = max(self.node_map) + 1
            if isinstance(node, Subcommand):
                self.node_map[new_id] = _BaseNode(new_id, node, 'subcommand')
                for sub_node in node.options:
                    real_sub_name = sub_node.name.lstrip('-')
                    if f"subcommand:{real_name}:{real_sub_name}" in self.name_list:
                        raise DuplicateCommand(lang_config.visitor_duplicate_suboption.format(target=real_sub_name))
                    self.name_list.append(f"subcommand:{real_name}:{real_sub_name}")
                    sub_new_id = max(self.node_map) + 1
                    self.node_map[sub_new_id] = _BaseNode(sub_new_id, sub_node, 'option')
                    self.node_map[sub_new_id].additional_info['aliases'] = sub_node.aliases
                    self.node_map[new_id].sub_nodes.append(sub_new_id)
            else:
                self.node_map[new_id] = _BaseNode(new_id, node, 'option')
                self.node_map[new_id].additional_info['aliases'] = node.aliases
            self.node_map[0].sub_nodes.append(new_id)

    def require(self, path: Optional[Union[str, List[str]]] = None) -> _BaseNode:
        """
        依据指定路径获取节点
        """
        _cache_name = ""
        _cache_node = self.node_map[0]
        if path is None:
            return _cache_node
        if isinstance(path, str):
            path = path.split('.')
        for part in path:
            if part in ("option", "subcommand"):
                _cache_name = part
                continue
            if _cache_name:
                _cache_name = f'{_cache_name}:{part}'
                if _cache_name in self.name_list:
                    _cache_node = self.node_map[self.name_list.index(_cache_name)]
            else:
                if (
                    f'option:{part}' in self.name_list
                    and f'subcommand:{part}' in self.name_list
                ):
                    raise ValueError(lang_config.visitor_ambiguous_name.format(target=part))
                if f"subcommand:{part}" in self.name_list:
                    _cache_name = f"subcommand:{part}"
                    _cache_node = self.node_map[self.name_list.index(_cache_name)]
                elif f"option:{part}" in self.name_list:
                    _cache_name = f"option:{part}"
                    _cache_node = self.node_map[self.name_list.index(_cache_name)]
        return _cache_node

    def trace_nodes(self, root: _BaseNode):
        """
        跟踪所有的节点
        """
        return {
            "type": root.type, "name": root.name, "description": root.description, "parameters": root.parameters,
            "separators": root.separators, "param_separators": root.param_separators,
            "additional_info": root.additional_info,
            "sub_nodes": [self.trace_nodes(self.node_map[i]) for i in root.sub_nodes]
        }

    def format_node(self, formatter: AbstractTextFormatter, node: Optional[_BaseNode] = None) -> str:
        """
        通过格式化器格式化节点
        """
        if not node:
            node = self.node_map[0]
        return formatter.format(self.trace_nodes(node))