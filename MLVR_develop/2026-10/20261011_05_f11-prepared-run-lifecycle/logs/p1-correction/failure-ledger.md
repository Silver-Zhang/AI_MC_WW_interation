# P1修复过程记录

- 开工快照脚本首次把git submodule目录当普通文件读取，IsADirectoryError；尚未编辑生产文件。修正为独立记录submodule status，普通文件逐个SHA256并完整打包。

- 首次完整configure/build成功，两个target链接成功；既有源码编译warning原样保留在build-01/stderr.txt，未改清单外文件去消警。
- 新增51负例、原66负例、36配对run及普通123项、10CTest均首轮通过；没有失败数值用例被删除，也没有事后放宽容差。
- 私有脚本复制后、执行前检查发现硬编码路由尚指向旧Task日志/工具，已统一改为本轮P目录，并保持普通比较器与时间例外规则不变；旧证据全量SHA检查确认未被覆盖。旧WEIGHT=D1退出1按baseline预期记录，不记作输运通过。
- Step1核心比较包含签名共631行、花括号内body623行，均与HEAD逐字一致。

- 最后归档自检虽退出0，但正文报告Task05 README旧状态与INDEX不一致1项（旧状态字符串已由Task07更新，首次精确文本替换未命中）；已修正状态行并以新的workflow-archive-check-02重新检查。不把工具exit0误当作无问题。
