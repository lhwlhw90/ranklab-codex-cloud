# RankLab · 用 Codex Cloud 完成第一个 PR

RankLab 读取检索结果，计算各查询的 Precision@K，再取平均值。这次练习由你给 Codex 派任务，让它新增 Recall@K，最后审查它提交的改动。项目使用 Python 3.10+ 标准库，运行示例和测试无需安装第三方包或配置 API Key。

## 1. 把起始项目放进 GitHub

解压后，在自己的 GitHub 账号下创建一个空仓库，例如 `ranklab`。用 GitHub 网页的 **Upload files** 上传解压目录**里面的文件和子目录**，保留目录结构，提交到默认分支。提交后，仓库首页应能直接看到 `README.md`、`AGENTS.md` 和 `ranklab.py`。

| 文件 | 练习中怎么用 |
| --- | --- |
| `ranklab.py` | 运行 CLI，也是在本次练习中添加指标的入口 |
| `examples/queries.json` | 两条查询，可手算每个指标 |
| `tests/test_ranklab.py` | 检查起始版本的行为 |
| `practice/check_recall.py` | 从命令行验收新功能，随项目提供 |
| `AGENTS.md` | 给 Codex 的仓库约定和测试命令 |

## 2. 在 Cloud 打开仓库，跑通起点

登录 ChatGPT，在新对话选择 **Work in → Cloud**。连接能访问练习仓库的 GitHub 账号。若有默认云环境，可直接让 Codex 检出仓库；若工作区使用已发布的环境，选择能访问该仓库的环境。环境只需提供 Python 3.10+。[OpenAI 官方 Codex Cloud 指南](https://learn.chatgpt.com/docs/cloud)

把下面的“我的账号/ranklab”替换成自己的仓库名，发送第一条消息。

> 请打开 GitHub 仓库“我的账号/ranklab”的默认分支，阅读根目录的 AGENTS.md。在仓库根目录运行下面两条命令，贴出样例输出和测试数量，指出计算单条查询得分的位置。这一步只读。
>
> `python3 ranklab.py examples/queries.json --k 2`
>
> `python3 -m unittest discover -s tests -v`

第一条命令应该只打印 `precision@2 = 0.5000`。第二条应发现 8 个测试并以 `OK` 结束。若找不到 `ranklab.py`，先对照 GitHub 首页检查分支和上传时的目录层级。

## 3. 在同一对话派发开发任务

> 请给 RankLab CLI 增加 `--metric precision|recall`，默认使用 precision，兼容现有命令和输出格式。每条查询的 Recall@K 等于前 K 个结果中命中的文档数除以该查询全部相关文档数。相关集合为空时记 0，也计入平均值。最终对各查询等权平均，显示四位小数。
>
> 先运行 `python3 practice/check_recall.py`，确认起始版本缺少哪项行为。再实现功能，补充单元测试，保持验收脚本和样例数据原样。完成后运行基线测试、验收脚本和两条样例命令（默认指标与 `--metric recall`）。请列出改了哪些文件以及实际的命令输出。

这条任务给出了 CLI 接口、兼容要求、边界情况和验收方式。开发前，6 项验收中只有默认 Precision 通过，其余 5 项会报告起始 CLI 无法识别 `--metric`。开发后，6 项均应通过，基线测试和你让 Codex 补充的单元测试也应以 `OK` 结束。

## 4. 手算一次，再审查 PR

打开 `examples/queries.json`。当 K = 2 时，两条查询各命中一个文档，但相关文档的总数不同。

| 查询 | 前两个结果 | 全部相关文档 | Precision@2 | Recall@2 |
| --- | --- | --- | ---: | ---: |
| 第一条 | A、B | A、C、D | 1/2 | 1/3 |
| 第二条 | X、Y | X | 1/2 | 1 |
| 按查询平均 | | | 0.5000 | 0.6667 |

在任务结果中打开代码差异，找到 Recall 的分母和平均值的计算位置。如果看到把所有查询的命中数和相关文档数分别相加再相除，样例会得到 `2/4 = 0.5000`。这时可以在原对话追问：“请列出两个查询各自的 Recall@2，按查询等权平均，修正实现后重跑验收。”

对照执行记录，核对以下两条命令的输出，并确认新增测试覆盖空相关集合。检查通过后，请 Codex 为本次改动创建以默认分支为目标的 Pull Request（PR）。在 GitHub 的 **Files changed** 查看最终差异，再决定是否合并。

```sh
python3 ranklab.py examples/queries.json --k 2
# precision@2 = 0.5000

python3 ranklab.py examples/queries.json --k 2 --metric recall
# recall@2 = 0.6667
```
