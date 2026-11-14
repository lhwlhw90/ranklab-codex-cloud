# RankLab 开发约定

项目使用 Python 3.10+ 和标准库。从仓库根目录运行命令。

- CLI 入口是 `ranklab.py`。输入样例在 `examples/queries.json`。每一行输出的指标值保留四位小数。
- 更改指标时，在 `tests/` 补充相应的单元测试，并运行 `python3 -m unittest discover -s tests -v`。
- 用 `python3 ranklab.py examples/queries.json --k 2` 检查默认 CLI 行为。
- `practice/check_recall.py` 是本次 Recall 练习提供的验收脚本。实现该功能后，另行运行 `python3 practice/check_recall.py`。
