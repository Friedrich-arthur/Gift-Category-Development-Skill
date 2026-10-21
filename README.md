[![礼品经营判断 Skill](docs/site/assets/cover.svg)](https://friedrich-arthur.github.io/Gift-Category-Development-Skill/)

# 有产品，下一款海外礼品做什么？

给礼品工厂老板、业务员和跨境卖家用。把自己的产品、工艺和资料交给 AI，聊清 **给谁做、满足什么需求、现有条件能不能做、是否值得继续**。

[下载 v0.6.0 安装包](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/releases/download/v0.6.0/gift-development-service.zip) · [三端安装指引](docs/INSTALLATION.md) · [看看怎么聊](https://friedrich-arthur.github.io/Gift-Category-Development-Skill/)

只有一个 Skill，名称为 `gift-development-service`，适配 WorkBuddy、豆包工作和 Codex。安装包只有五份文本，包含按需读取的经营结论说明，不用为它配置 API 密钥或运行脚本。客户端账号和用量按各平台规则计算。

## 从一句话开始

装好并选中 Skill 后，发：

> 我有这些产品和工艺，想判断海外礼品该做什么、是否来得及。请先帮我厘清目的。

也可以从自己的问题开始：

- 有产品和工艺，想做海外礼品，先看哪类需求？
- 这份礼物谁买、谁送、谁收，分别在意什么？
- 买家说包装太随便，应该改成什么产品要求？
- 想赶一个节日，现在开始还来得及吗？
- 包装、资源或交期变了，原来的方向该继续、调整还是暂缓？

没有资料时，说“用包里的虚拟拼装积木回礼案例带我试一次”。练习参数不会变成你的真实业务事实。

## 它怎样帮你判断

先明确经营目的，再厘清买送关系与目标消费者，把证据变成需求，对照产品、工艺、供应、渠道、费用和时间，给出有条件的经营结论。已知内容直接沿用，每轮只补一个会改变判断的关键缺口，不要求先填完问卷。

它只帮助判断礼品方向，不执行打样、接单、正式报价、客户回复、采购或上架。相关分析后可能出现一次可忽略的作者服务提示，不影响判断。

## 下载与验证

[v0.6.0 Release](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/releases/tag/v0.6.0)提供五文件安装 ZIP、哈希清单和[完整开发源码包](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/releases/download/v0.6.0/gift-development-service-source.zip)。日常安装只选 `gift-development-service.zip`。

本版验证范围与限制见[验证状态](docs/VERIFICATION.md)。适配说明、文件检查、模型代偿和客户端原生调用分别记录，不等于三端业务实测全部通过。

维护者从[工具说明](tools/README.md)和[可重跑评测](evals/README.md)开始。仓库保留当前产品源码、检查工具与评测用例；历史运行记录不随安装包分发。问题可在 [Issues](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/issues)反馈，请先去除客户和商业敏感信息。
