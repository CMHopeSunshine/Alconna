# 更新日志

## 未发布:

**此版本为长期支持版本 (LTS), 也是 2.0 版本前的最后一个版本**

### 破坏性改动:

> 用户侧

- `ShortcutArgs` 不再需要 `options`, 其合并至 `args`
- `Alconna.parse` 移除参数 `interrupt`, 由 `CompSession` 替代

> 开发侧

- 使用 `NEPattern` 0.5 以上版本
- 使用 `tarina` 替代部分功能
- `DataCollectionContainer`, `Analyser`, `handle_xxx` 和 `analyser_xxx` 
等移动至 `arclet.alconna._internal`
- `DataCollectionContainer` 重命名为 `Argv`
- `Argv.config` 移出为独立函数 `argv_config`
- `Argv.text_sign` 现在是 `Argv.to_text`, 其返回值为 `str | None`

### 新增:

- `Option` 新增参数 `compact`, 允许选项名后的第一个参数紧随其头部
- `Option` 新增参数 `default`, 允许设置选项的默认值:
  - 传入的任意值会被包装为 `OptionResult`, 除非其为 `None`
  - 直接传入 `OptionResult` 会被直接使用
  - 若想设置 args 的默认值, 请传入 `OptionResult`
- `Subcommand` 新增参数 `default`, 允许设置子命令的默认值
  - 传入的任意值会被包装为 `SubcommandResult`, 除非其为 `None`
  - 直接传入 `SubcommandResult` 会被直接使用
  - 若想设置 args 的默认值, 请传入 `SubcommandResult`
- `CommandMeta` 与 `Namespace` 新增 `compact` 属性, 允许命令传入的第一个参数紧随其头部
- `Namespace` 新增 `to_text` 属性, 其与 `Argv.to_text` 一致
- 加入 `CompSession`, 用于交互式命令补全
  - `session.available`: 表示当前补全会话是否可用
  - `session.current()`: 当前选中的补全选项的文本
  - `session.tab([, offset])`: 切换补全选项
  - `session.enter([, content])`: 确认当前补全选项
- `Alconna` 的名字与前缀无传入时，取用 sys.argv[0] 作为其名字
- `Alconna` 现支持 `__call__`, 即直接调用实例; 当命令名与 sys.argv[0] 接近时, 传入命令不需要输入命令头
- `Action` 改动, 现在 `Action` 功能更接近于 `argparse`:
  - args 为空时:
    - `store`: 默认的 action, 存放 `...` 或 `default` 的值
    - `store_value`, `store_true`, `store_false`: 存放特殊值
    - `append`: 追加 `...` 或 `default` 的值
    - `append_value`: 追加特殊值
    - `count`: 计数
  - args 不为空时:
    - `store_xxx`, `count`: 最新的 args 结果会覆盖上一次
    - `append_xxx`: 此次的 args 结果会与之前的合并成列表
- 新增 `set_default_argv_type` 函数, 用于设置默认的 `Argv` 类型
- `CommandMeta.example` 现在会将 `$` 替换为可能的命令前缀
- `Completion` 选项增加别名 `'?'`

### 改进:

- 由 `name` 与 `requires` 合成的 `dest` 也会去掉 `name` 的前缀 
- `Argv` 不再是 `Analyser` 的属性, 而是其方法的传入参数
- `compile` 函数现在作为 `Alconna` 的方法
- shortcut 使用方法改变:
  - `ShortcutArgs` 增加 `fuzzy` 参数, 用于指定该快捷命令是否允许后随参数, 默认为 `True`
  - 可以通过 `{%X_n}` 来引用传入的快捷命令的第 n 个参数
  - 可以通过 `{*(SEP)}` 来引用传入的快捷命令的所有参数, 其中 SEP 为可选的分隔符
- bracket header 现在支持进行类型转换
- 性能优化, 提升25% ~ 30%
- `set_default` 的 `arg`, `option`, `subcommand` 合并为 `path`, 原参数仍可用

### 修复:

- 修复 `anti args` 的 bug
- 修复 `Formatter.remove` 的 bug


## Alconna 1.6.6:

### 修复

- 修复 `MultiVar` 工作异常的错误

## Alconna 1.6.5:

### 改进

- 调整 `Header Match` 的内部实现
- 格式化代码
- 更改测试文件

## Alconna 1.6.4:

### 修复

- 修复 shortcut 的功能错误

### 改进

- 字符串处理时不再对后跟引号外的 "\\" 处理

## Alconna 1.6.3:

### 修复

- 修复 `Stub.available` 初始值为 `True` 的错误
- 修复 `Duplication` 仅对解析存在的选项设置存根的错误

## Alconna 1.6.2

### 修复

- 修复 语言文件读取时未关闭的错误

## Alconna 1.6.1

###

- 修复 不同 Args 合并时丢失来自 from_callable 提供的参数

## Alconna 1.6.0

### 破坏性改动

> 用户侧

- 移除 `AlconnGroup` 类，但保留通过 `|` 组合命令的行为

> 开发侧

- 移动 `Args.from_string_list` 至 `arclet-alconna-tools`
- 移动 `Formatter` 至 `formatter.py`
- 移动 `ActionHandler` 至 `core.py`
- 移除 `analysis.base`
- 合并 `arparma` 与 `components.behavior`
- 合并 `parts` 与 `special`

### 新增

- 加入 `ShortcutArgs` 替代原 `shortcut` 中的 `command`, 其包括:
  - `command`: 快捷命令指向的命令
  - `args`: 快捷命令的参数
  - `options`: 快捷命令的选项
- `Subcommand` 增加 `add()` 方法，用于添加子命令与选项
- `Alconna` 增加 `option()` 方法，用于添加选项
- `Alconna` 增加 `subcommand()` 方法，用于添加快捷命令

### 改进

- `Alconna.add` 现在只传入 `Option` 或 `Subcommand` 的实例

### 修复
- 修复一系列 bugs

## Alconna 1.5.2:

### 改进

- 调整解析器的可拓展性
- 改进代码的类型提示

## Alconna 1.5.1:

### 修复

- 修复子解析器的 bug

## Alconna 1.5.0:

### 破坏性改动

> 开发侧

- `Arparma.update` 移动到 `ArparmaBehavior.update`
- 部分 api 改动: 
  - `Analyser.process` -> `Analyser.container.build`
  - `Analyser.analyser` -> `Analyser.process`
  - `analyse_subcommand` -> `analyse_param`

### 新增

- 加入 `SubAnalyser`, 负责部分原 `Analyser` 的部分功能
- 加入 `HeadResult`, 表示头部匹配的结果
- 新增 `DataCollectionContainer`, 负责原 `Analyser` 的数据操作
- 允许子命令嵌套
- 新增 `Analyser.config` 方法以配置如 `preprocessor`, `filter_out` 之类的参数
- 新增 `output_manager.set` 方法以新增输出行为
- 新增 `output_manager.capture` 上下文管理器以提供输出捕获功能

### 改进

- `Arparma.header_match` 现在返回 `HeadResult` 类型
- `output_manager.get` 方法从构建输出行为到只获取输出行为
- `set_default` 可以细化至更新 `subcmd.opt.args.arg` 的值

## Alconna 1.4.3:

### 改进
- `KeyWordVar` 现在可以指定 `sep`
- `MultiVar` 现在默认格式是 `+`

### 修复
- 修复 bugs

## Alconna 1.4.2:

### 修复

- 修复可变参数匹配的bug
- 修复 `Args.from_callable` 的bug
- 修复 `Arparma.__repr__` 的bug

## Alconna 1.4.1:

### 修复

- 修复 `help text` 的 bug
- 修复 `Arg` 提取 notice 的 bug

## Alconna 1.4.0:

### 破坏性改动

> 用户侧

- 'Arpamar' -> 'Arparma'
- `Alconna` 构建时不再允许废弃的 kwargs 参数传入
- `ArgFlag` 中关于可变参数与键值参数部分移除
- `behaviors` 与 `formatter` 的配置移至 `Namespace`, 原 `Alconna.config` 仅用于配置解析器类型

### 新增

- 加入 `ArparmaExecutor`, 以绑定一个响应函数
- 加入 `alconna.typing.MultiVar` 与 `alconna.typing.KeyWordVar` 显式声明可变参数与键值参数，
并提供 `alconna.typing.Kw` 来进行缩写 (如 `Kw @ int`)

### 改进

- 改进字符串分割过程，以运行更细粒度的分隔控制
- 改进 Args 构建， 加入 Arg 类 替代原先的 ArgUnit，并保留参数名后缀传入
- 原先的 ArgFlag `'H','O','A'` 变回 `'/','?','!'`
- Args.separators 移除，分割任务转移给 Arg.separators
- `set_default` 现在可以传入 factory 参数， 并且必须传入关键字参数

### 修复

- 修复可能存在的内存泄漏问题


## Alconna 1.3.3

### 修复

- 修复可能存在的内存泄漏问题

## Alconna 1.3.2 ~ 1.3.2.2

### 新增

- 通过 "+" 以组合字符串与选项或者子命令等隐式构建命令的方法
- 允许自定义内建选项的名称，比如改"--help"为"帮助"

### 改进

- `Arpamar.find` 现在可以用 query_path 了
- `Arpamar.query` 现在返回的是MappingProxyType, 若需要修改path的值请用`Arpamar.update`

### 修复

- 修复 bugs

## Alconna 1.3.1

### 改进

- 调整lang config
- 调整 completion 样式

### 修复
- 修改 help text 的 bug

## Alconna 1.3.0

### 破坏性改动

> 用户侧

- 取消 shortcut的expiration
- 调整 Alconna的构造样式, 将header、command、options等合并; 兼容旧版写法到1.4

> 开发侧

- 原先的builtins迁移至[`arclet-alconna-tools`](https://github.com/ArcletProject/Alconna-Tools), 只保留set_default、store_value与version

### 新增

- 新增命名空间配置，并将原先部分全局配置划为命名空间下的配置
- 允许.parse传入参数interrupt(bool)以在参数缺失的情况下可后续自行加参数

### 改进

- `set_default`可以附加一个 arg 名
- 调整repr样式

### 修复

- 修复 bugs

## Alconna 1.2.0:

### 破坏性改动

- 加入 `CommandMeta`, 并取代`help_text`、`is_raise_exception`等

### 新增

- 加入 `ArgField`, 可填入 `alias`, `default_factory`等
- 加入命令补全功能, 暂由`--comp|-cp`触发
- `CommandMeta` 新增 `hide`, 可以在命令管理器获取所有帮助时跳过该命令

### 改进

- 命令管理器可以获取原始的命令数据

### 修复

- 修复 bugs

## Alconna 1.1.2 - 1.1.2.3:

1. 修复 bugs
2. BasePattern 加入 `to` 方法

## Alconna 1.1.1:

1. `Arpamar` 泛型支持, 可通过`Arpamar[type]`指定原指令的类型
2. `Alconna` 可通过 `|` 进行组合, 返回命令组
    ```python
    alc = Alconna("{place1}在哪里") | Alconna("哪里有{place1}")
    alc.parse("食物在哪里")
    alc.parse("哪里有食物")
    ```

## Alconna 1.1.0:

1. `AlconnaDuplication` -> `Duplication`
2. `Duplication` 现在支持写入参数名或头部名称, 如

    ```python
    command = Alconna("test", Args["foo", int]) + Option("bar", Args["bar", str])
    
    class Demo(Duplication):
        foo: int
        bar: str
    ```

3. `Arpamar` 在执行行为器时可以通过抛出 `OutBoundsBehave` 使解析失败
4. 修复bugs
 
## Alconna 1.0.2 - 1.0.4:

1. 修复 BUG
2. 微调 Args

## Alconna 1.0.1:

1. `Args.from_callable` 允许 keyword 参数
2. 更改ArgAction参数
3. 修复bugs

## Alconna 1.0.0:

1. 将`lang`迁移到新增的`config`中，并为`config`加入了如全局分隔、开启缓存等选项
2. 压缩代码量并规范化
3. `--help` 选项允许在命令任何部位生效, 并且会根据当前命令选择是否展示选项的帮助信息
4. `Args` name 的flag附加现在不需要以`|`分隔
5. `Args` name 允许用`#...`为单个Arg提供注释, 其会展示在帮助信息内
6. `Args` 允许传入 `Callable[[A], B]` 作为表达, 会自动解析输入类型与输出类型
7. 完善了测试代码, 位于[测试文件夹](tests)内, 通过[入口文件](entry_test.py)可执行全部测试
8. 加入一个类似`beartype`的[`checker`](src/arclet/alconna/builtin/checker.py)
9. 命令头部允许使用非str类型, 即可以`Alconna(int)`
10. 解析器增加预处理器选项, 允许在分划数据单元前进行转化处理
11. 性能提升, 理想情况最快约为 20w msg/s
12. 删除`Alconna.set_action`
13. 重构 `ObjectPattern`
14. 增加 `datetime`的 BasePattern, 支持传入时间戳或日期文字
15. `Analyser` 的字段修改, `next_data` -> `popitem`, `reduce_data` -> `pushback`
16. `output_send` 合并到 `output_manager`
17. `Option` 添加参数`priority`, 仅在需要选项重载时安排优先级
18. 修复bugs

## Alconna 0.9.4:

1. 修改 `Args` 的构造方法, 取消使用 slice 传入参数. 请从 `Args[foo:int, bar:str:default]` 修改为 `Args[foo, int][bar, str, default]`.
2. Option 与 Subcommand 现支持 requires 参数, 该参数允许解析该节点时判断 require 的字段是否存在.
3. Option 与 Subcommand 的 requires 可以通过 name 传入, 用空格分隔. 该特性要求 Option 中传入别名时不能用空格.
4. 允许同名的 Option 与 Subcommand 在同一个命令中, 应保证能用 require 参数来区分.
5. 允许简单的选项重载, 如 `Option("foo", Args.bar[int])` 可以与 `Option("foo")` 一起使用.
6. BasePattern 增加 `validator` 属性, 负责对匹配结果进行验证.
7. Args 支持 Annotated 的传入, 如 `Args.bar[Annotated[int, lambda x: x > 0]]`, 或使用 `arclet.alconna.typing.Bind`
8. 加入 `AlconnaGroup` 类, 用于组合多个 `Alconna` 对象. 其解析行为与 `Alconna` 相同.
9. 取消不能构建多个重名的 `Alconna` 对象, 以 `AlconnaGroup` 代替. (暂定)
10. 删除 `arclet.alconna.components.visitor`, 修改 `Formatter` 的传入参数.
11. 增加 `Alconna.config` 类方法, 用于设置全局配置.
12. 移出 `arclet.alconna.builtin.commandline`, 独立为一个模块 `alconna-cli`.
13. `ObjectPattern` 移动到 `arclet.alconna.builtin.pattern` 模块.
14. 修复 bug.

## Alconna 0.9.3 - 0.9.3.3:

1. 合并 `ArgPattern` 与 `TypePattern` 为 `BasePattern`, 并将诸多分散特性(如 `anti`, `any`) 移动到 `BasePattern` 中.
2. 取消 `Analyser` 中有关 `arg_handler` 的部分
3. `AnyStr`、`AnyDigit`、`AnyFloat` 等现在不被公开.
4. `AnyParam` 重写为由 `BasePattern` 实现, 并改名为 `AnyOne`.
5. `alconna.types` 变为 `alconna.typing`.
6. 为 `all_command_help` 增加索引选项
7. 修复 bug.

## Alconna 0.9.2:

1. 增强 `Arpamar` 的功能, 使其更类似于一种接口. 其中的修改有:
   - 从 `get()` 变为 `query()`
   - 从 `has()` 变为 `find()`
   - 从 `set()` 变为 `update()`
   - 从 `update()` 变为 `execute()`
   - 增加 `get_duplication()`
   - 增加 `source`, `origin` 属性
2. 项目结构调整
3. ArgAction 的执行现在交给 `ActionHandler` 来处理.
4. `split` 以及 `separator` 现在需要传入 `Set[str]` 类型.
5. 修复 bug.

## Alconna 0.9.1:

1. 增添 `dest`, 其作为选项在 Arpamar 中的实际名称. 
2. 增加内建 `Argument` 方法, 类似于 `add_argument`, 以便捷创建 Option + Args 的组合. 
3. 修复 bug

## Alconna 0.9.0 - 0.9.0.3:

1. 将 HelpAction 与 HelpTextFormatter 作为 help 模块
2. 语言配置组件的增强. 现在以语言种类标识符作为父级, 以支持多语言.
3. 为 manager 新增一个记录命令输入的 LruCache. 解析器可以使用这个缓存来避免重复解析. 目前缓存上限为 100.
4. 新增 `--shortcut` 内置选项, 为命令提供临时快捷命令的创建与删除.
5. 修改 manager 中的 `shortcut`, 并支持持久化
6. 部分性能优化, 以大致抵消因缓存计算而带来的性能损耗.
7. 部分 api 名称变更:
   - `pattern` -> `pattern_gen`
   - `handle_message` -> `process_message`
8. Args 新增 `add_argument` 方法, 以添加参数.

## Alconna 0.8.3:

1. 命令头的正则支持格式修改, 由原来的`f"{表达式}"`改为`"{名称:类型或表达式}"`
2. 加入语言文件配置, 可以通过`Alconna.load_config_file`加载自定义的语言文件, 格式为`json`
3. 为选项与子命令的匹配也加入了模糊匹配
4. 选项与子命令的`separator`可以传入空字符串, `Alconna`会据此自动分割
5. 部分API修改, 暂时去除`from_dict`方法
6. 修复了一些bug

## Alconna 0.8.2:

1. 修改了一些docstring
2. 修改参数前缀, 现需要以后缀形式传入, 以`';'`为开头, 并用`'|'`分割。
3. 参数前缀现通过单个大写字母表示, 具体对应如下:
   * `'S'` <= `'*'`
   * `'W'` <= `'**'`
   * `'O'` <= `'?'`
   * `'K'` <= `'@'`
   * `'H'` <= `'_'`
   * `'F'` <= `'#'`
   * `'A'` <= `'!'`
4. 参数标识符现增加数字, 以表示指定长度的可变参数, 如`'foo;S'`表示能接收任意长度的可变参数, `'foo;3'`表示接收长度为3的可变参数。
5. `Args`现在允许传入分隔符, 通过`Args.separate(xx)`或`Args / xx`设置
6. 加入`pattern`装饰器函数, 用以便捷的创建`ArgPattern`对象
7. 加入`delegate`装饰器函数, 用以便捷的创建`Alconna`对象

## Alconna 0.8.1:

修复了一些严重的bug。

## Alconna 0.8.0:

1. `Option`的`alias`现在需要传入List[str]，而不是str。
2. `help_text`内置两个预选板块`Usage`和`Example`, 编写规则为`"xxx Usage:xxx; Example:xxx;"`。
3. 加入`TypePattern`, 作用为简单的类型转换器, 其可以设置前置转换器, 即可以`str -> Path -> bytes`。
4. 加入命令的模糊匹配, 在`Alconna`中传入`is_fuzzy_match`参数, 可以设置是否模糊匹配。
5. `AlconnaString`参数规则修改, 现在`<xx>`表示必选, `[xx]`表示可选, `&xx`表示action的值。
6. `ArgparseHelpTextFormatter`相关格式修改

## Alconna 0.7.7 - 0.7.7.4

1. 加入`Argparser`风格的HelpFormatter
2. 加入`AlconnaDuplication`, 旨在提供更好的解析结果使用
3. option的name与alias现在会根据长度自动倒换
4. 修复Bug

## Alconna 0.7.6 - 0.7.6.1

1. 增加对`Graia`系的原生支持, 位于`arclet.alconna.graia`
2. header现在可支持非文字类元素与文字混用的解析, 原来的方式请改用`元组(非文本元素, 文本)`
3. 增加`Alconna` 对 `/`与`@` 运算符的支持, 作用为重置命名空间
4. 增加`Alconna` 对 `+` 运算符的支持, 作用为增加选项
5. `Args` 可直接传入 `str`, 即`Args["foo":"foo"]` -> `Args["foo"]`
6. `Format`中的format slot可以直接写入类型, 如`"{name: str}"`
7. 修复Bug

## Alconna 0.7.5

1. 内部类型改进, `MessageChain` -> `DataCollection`
2. 加入`ArpamarBehavior`, 用以解析后的预处理, 并提供三个预制的`behavior`:
   - `set_default`: 当某个选项未被输入时, 使用该行为添加一个默认值
   - `exclusion`: 当指定的两个选项同时出现时报错
   - `cool_down`: 限制命令调用频率
3. 加入`NodeVisitor`与`HelpFormatter`, 并将原先给CommandNode的help生成转移给Formatter
4. 加入`AlconnaMessageProxy`, 用作对外适配接口

## Alconna 0.7.4 - 0.7.4.3:

1. 加入`Alconna.local_args`, 可用来注入额外参数
2. `actions`关键字改为`action`
3. 加入`_`前缀，用来隐藏该参数的类型注解
4. 修复bug

## Alconna 0.7.3:

1. 优化结构
2. 增加`AlconnaFire`的Config, 用来约束`AlconnaFire`的参数
3. `AlconnaFire`现在可以解析子命令, 通过Config传入`get_subcommand=True`来启用
4. 更好的parameter-helptext
5. 新增Args构造方法`a = Args.xxx[value, default]`
6. `util.chain_filter`重新归并到`Analyser.handle_message`里
7. 增加`Force`类, 用以标记arg类型不需要进行转换; 或者在key前面加上`"#"`
8. 支持传入键值对参数与可变键值对参数, 分别用`"@"`和`"**""`标记
9. 支持将参数设为可选(即未解析成功时不报错而是跳过), 用`"?"`标记
10. `Arpamar`可以通过`XXX.opt.arg1`、`XXX.sub.sub_opt.arg2`等方式获取参数值
11. 修复bug

## Alconna 0.7.2:

1. 改进`AlconnaFire`方法, 其可通过`AlconnaFire.instance`获取目标对象的可能实例
2. 加入`SequenceArg`与`MappingArg`, 其对应解析列表、元组、集合与字典
3. Subcommand在其Args未解析时抛出异常
4. Arpamar现在可以获取subcommands与error_info
5. 增强Format
6. 修改help—action相关

## Alconna 0.7.1:

1. 增加`alconna.builtin.construct.AlconnaFire`，为`Alconna`的`Fire-like`方法. 
其会尝试根据传入的对象生成`Alconna`
2. 增加 `UnionArg`, 其传入的列表中可以包含`ArgPattern`、`Type`与实际值. 为`choice`的改进
3. `Args`支持传入`Union[...]`格式的参数
4. 增加 `ObjectPattern`, 其会尝试从对象中生成`ArgPattern`, 并在解析成功后创建实例
5. `action`现支持传入异步函数
6. `AlconnaString`现在会读取`locals`的值

## Alconna 0.7.0:

1. 内部结构大更改, 将`Command`与`Analyser`进行了一个解耦
2. 多个api更改或去除, 请留意. 该特性为不兼容的特性.
   - `Alconna`:
      - `Alconna.analyse_message`: 变更为`Alconna.parse`; 其新增参数`static`, 可以指定是否动态创建`Analyser`
      - `Alconna.order_parse`: 移除, 以`Alconna.analyser_type`为准
      - `Alconna.from_string`、`Alconna.format`: 迁移至`alconna.builtin.construct`中
   - `TemplateCommand`:
     - 变更为`CommandNode`
     - `CommandNode.__init__`: 移除`kwargs`
     - `CommandNode.__init__`: 增加参数`help_text`, `separator`, 替代`CommandNode.help`与`CommandNode.separate`
     - `CommandNode.help`: 仍然保留, 但推荐从__init__中传入
     - `CommandNode.separate`: 移除
     - `CommandNode.action`: 增加对Iterable的判断
   - `Subcommand`:
     - `Option`的传入由`*option`改为`options`
   - `Arpamar`:
     - 新增`Arpamar.get_first_arg`, 用以获取第一个参数
   - `ArgAction`:
     - 从`alconna.actions`迁移至`alconna.base`, 剩余的`ArgAction`迁移至`alconna.builtin.actions`
   - `AlconnaDecorate`:
     - 迁移至`alconna.builtin.construct`
   - `alconna.analyser`:
     - 迁移至`alconna.analysis.analyser`
     - `analyse_args`、`analyse_option`、`analyse_subcommand`、`analyse_headers`: 迁移至`alconna.analysis.parts`
3. 增加`alconna.analysis`, 其中:
   - `analysis.compile`: 用以从`Alconna`中生成`Analyser`
   - `analysis.analyse`: 隐式调用`analyser.analyse`
   - `analysis.analyse_args`: 可直接传入`Args`以针对性解析
   - `analysis.analyse_option`: 可直接传入`Option`以针对性解析
   - `analysis.analyse_subcommand`: 可直接传入`Subcommand`以针对性解析
   - `analysis.analyse_headers`: 可直接传入`Headers`以针对性解析

## Alconna 0.6.5:

1. 可以自定义all_command_help
2. 加入anti-arg, 用以反向检查参数
3. 修复一些bug

## Alconna 0.6.4:

1. 加入快捷指令功能, 可以用一段特殊的字符串来表示命令
2. 加入arg-choice, 可以指定参数的可选值
3. 修改docstring, 使其变得更加可读
4. 加入commandManager.broadcast功能, 可以广播命令

## Alconna 0.6.3:

1. 修复命令行的Bug
2. 加入变长参数的支持, 可以在参数名前面添加一个`*`来表示变长参数

## Alconna 0.6.2:

1. 修复几个Bug
2. 加入from_dict与to_dict，暂时无法支持保存action
3. 命令行功能加入using

## Alconna 0.6.1:

1. 性能优化加强, 现在纯字符串匹配可以跑到60000msg/s (与之相对, 匹配其他消息元素可以跑到10w msg/s, re出来挨打)
2. commandline增加一个`analysis`功能，可以把命令转为命令格式
3. 修复Bug

## Alconna 0.6.0:

1. 加入click-like构造方法，具体内容在alconna/decorate里
2. 加入命令行功能，目前功能为便捷式编写Alconna与便捷查看docstring
3. 性能优化, 包含正则参数解析的速度提升大约10%
4. Option支持重复输入，此时多个解析结果会以列表形式存放

## Alconna 0.5.9: 

1. help选项可用传入一自定义函数已达到直接发送帮助说明的效果
2. 规范format方法；from_string现在可以用#加入帮助说明
3. 加入commandManager，帮助管理所有命令；支持解析原始消息链

## Alconna 0.5.8: 

加入有序匹配模式与命令缓存, 能使性能大大提升

## Alconna 0.5.7: 

修复非ArgPattern修饰的参数无法解析消息元素的Bug

## Alconna 0.5.6: 

1. 修复Bug
2. 增加了Email的参数匹配

## Alconna 0.5.5: 

1. from_sting可以传入option了
2. 修复bug

## Alconna 0.5.4: 

1. 优化结构
2. Arpamar 现可直接以XXX.name方式获取参数

## Alconna 0.5.3: 

1. 增加自定义消息元素过滤
2. headers支持传入消息元素

## Alconna 0.5.2: 

紧急修复Action无法返回值的bug

## Alconna 0.5.1: 

1. 优化整体结构
2. 完善了action相关
3. 修改参数默认值的bug

## Alconna 0.4.3：

1. 加入Action (暂时只针对Option)
2. Args解析出来的结果 (如bool值, int值) 会转为指定的类型

## Alconna 0.4.2：

1. 加入AnyFloat预制正则
2. Args构造支持传入元组;
3. 增加两种简易构造Alconna的形式
4. 修复Bug

## Alconna 0.4.1：

1. 加入 AnyParam类型 (单次泛匹配)与AllParam类型 (全部泛匹配)
2. 修改部分逻辑