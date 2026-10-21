# 装好后，拿一款产品试试

三端安装同一个 `gift-development-service`。选自己正在用的工具，装好后聊自己的经营问题。

[WorkBuddy](#workbuddy) · [豆包工作](#doubao) · [Codex](#codex) · [开始使用](#start) · [升级与卸载](#update) · [装不上怎么办](#help)

<a id="download"></a>
## 先下对这个包

[下载 v0.6.0 安装 ZIP](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/releases/download/v0.6.0/gift-development-service.zip) · [版本与附件页面](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/releases/tag/v0.6.0)

日常安装选 `gift-development-service.zip`。Release 里的完整源码包供开发者维护，不要把整个仓库上传成 Skill。若目标版本尚未发布，先等待对应附件，不要把网页另存为 ZIP，也不要换成别的版本后当作本版。

WorkBuddy 和豆包工作先上传 ZIP。只有界面要求文件夹时，才解压并选中里面直接包含 `SKILL.md` 的 `gift-development-service` 文件夹。

```text
gift-development-service/
├── SKILL.md
├── README.md
├── INSTALL.agent.md
├── examples/
│   └── demo-source.md
└── references/
    └── decision.md
```

五份文件都要保留，包括按需读取的 `references/decision.md`。不要只上传 `SKILL.md`，也不要把 `.md` 改为 `.txt`。本包没有执行脚本、hooks 或密钥，不要求改模型、权限或其他技能。AI 工具本身的账号、订阅和用量按各平台规则计算。

<a id="workbuddy"></a>
## WorkBuddy

1. 打开并登录 [WorkBuddy](https://www.workbuddy.cn/)。
2. 在左侧进入**专家·技能·连接器 → 技能**。
3. 点**添加技能 → 上传技能**，选择 `gift-development-service.zip`。界面只接受文件夹时，选择解压后的完整文件夹。
4. 在**已安装**里搜索 `gift-development-service` 或 `Gift Development Service`，确认用途是海外礼品经营判断。
5. 准备使用时开启这项技能，新建对话并优先从技能选择入口选中它；没有选择入口时，明确说“请使用 gift-development-service”，再发[开始语](#start)。

官方市场中的技能支持一键安装。本包使用**本地上传**，尚无已核验的官方市场一键入口，不能用“市场支持”替代“本包已上架”。菜单和上传方式依据 [WorkBuddy 官方技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

看到已安装列表中的名称，只说明客户端识别了它；还要新开对话选中并试一次。本版原生验证状态见[验证摘要](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/blob/main/docs/VERIFICATION.md)。

<a id="doubao"></a>
## 豆包工作

1. 打开并登录[豆包工作](https://www.doubao.com/work)，进入工作任务。
2. 找到**插件·技能·伙伴 → 技能 → 管理**。
3. 点**添加 → 上传技能**，上传 `gift-development-service.zip`。要求文件夹时，选解压后的完整文件夹。
4. 搜索 `Gift Development Service` 并打开详情，确认是海外礼品经营判断。同名已安装时按[升级方法](#update)替换，不新增一份。
5. 新建任务，在输入框附近的**更多技能**中选中它。窄窗口先看输入框旁的 **…**；详情页有**在对话中试用**时，也可从那里开始。
6. 发[开始语](#start)，接着给自己的资料。

这条路线依据此前网页版的实际导入、替换和选中观察，客户端或账号不同可能有差异。本版业务答复另做验证，不沿用历史通过结论。找不到入口时查当前页面或[官方技能说明](https://www.doubao.com/work/docs/zh-cn/articles/081010973544-skills)，不要猜本地目录，也不要把 ZIP 发到普通聊天后当作安装完成。

<a id="codex"></a>
## Codex

### 推荐：把这段发给 Codex

在准备使用它的本机 Codex 桌面版或 CLI 中发：

```text
请使用 skill-installer，安装这个固定版本的礼品经营判断 Skill：
https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/tree/v0.6.0/gift-development-service

只安装 gift-development-service 这一项。已安装时先检查现有内容并完整备份，再按包内 INSTALL.agent.md 升级；有我的自改内容或未知文件时先说明差异，不直接覆盖。使用当前客户端实际扫描的技能目录，不改模型、权限或其他技能。分别报告文件安装、客户端识别和实际调用结果。
```

装好后，在新对话输入 `$gift-development-service` 并从列表选中，再发[开始语](#start)。没有名称选择入口时，明确要求“先完整读取已安装的 gift-development-service，再回答”。未出现时重启 Codex 后另开对话。提示“目录已存在”要走升级，不换名字重复安装。

### 没有 skill-installer 时

把下载包交给能读取本机文件的 Codex，再使用下面的[代安装说明](#agent)。远端任务无法访问桌面文件时，不能视为已为本机安装。

熟悉目录的人可把完整文件夹放到当前客户端扫描的位置。当前[官方技能说明](https://learn.chatgpt.com/docs/build-skills)列出用户目录 `~/.agents/skills/`，Windows 对应 `%USERPROFILE%\.agents\skills\`。一些旧安装器使用 `CODEX_HOME/skills`，默认 `~/.codex/skills`。以实际客户端为准，只保留一个有效安装，不在两个位置各放一份。

<a id="start"></a>
## 装好后，发这句话

```text
我有这些产品和工艺，想判断海外礼品该做什么、是否来得及。请先帮我厘清目的。
```

接着给产品图片、工艺、市场或手头资料，不用先填完整问卷。已有目的直接说，已确认内容不必重复回答。还没准备资料可以说：

```text
请使用 gift-development-service，用包里的虚拟拼装积木回礼案例带我试一次。每轮只补一个关键问题，练习数字不要当成我的真实资料。
```

想从具体问题开始，也可以问“谁买、谁送、谁收？”“评论嫌包装廉价，应该改成什么需求？”或“换包装后还来得及吗？”。它会沿着目的、买送关系、消费者、需求和资源，形成继续、调整或暂缓的条件判断。

它不执行打样、接单、正式报价、客户回复、采购或上架。需要保存讨论时，可以说“保存这次判断”；工具有文件能力时核对保存位置，没有时复制输出自行保存。

<a id="update"></a>
## 已装旧版，怎么升级或卸载

先保存自己的资料和判断。同一工具只保留一份 `gift-development-service`。

- **豆包工作：** 在现有技能详情使用**替换**，上传目标 ZIP。关闭旧详情、刷新后重新打开核对，新建任务重新选中。入口与名称以当前界面为准。
- **WorkBuddy：** 有同名更新或替换入口时优先使用。没有时，先备份，再由能操作本机文件的代理按包内说明升级；位置不明时保留旧版并报告，别反复导入制造副本。
- **Codex：** 目录已存在时由代理先比较、备份，再升级同一位置，不另装一个名字。

<a id="agent"></a>
### 让能操作文件的代理代装或升级

把下载包交给代理，再复制：

```text
请按包内 INSTALL.agent.md，在我当前使用的工具中安装或升级 gift-development-service。先检查实际位置和现有版本，备份旧版，保护我的资料和客户端元数据；同一工具只保留一个有效安装。不改其他技能、模型、设置、权限或开关。有未知文件或自改内容先说明差异，不直接覆盖。完成后核对五份源文件，分别报告文件更新、客户端可见和实际调用结果。
```

完整安全约束见[包内 INSTALL.agent.md](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/blob/v0.6.0/gift-development-service/INSTALL.agent.md)。代理无法访问客户端或本机文件时，仍需使用对应工具的上传入口。

### 暂停或卸载

WorkBuddy 可关闭该技能，另开新对话后生效；要卸载，在已安装列表这项技能的 **… → 卸载** 操作。豆包使用当前个人技能管理中的停用或删除入口，共享技能交管理员处理，不猜目录删除。Codex 可让代理先保留用户资料与备份，只移除已核位置的这一项。不要删除整个 `skills` 目录。

<a id="help"></a>
## 装不上，先看这里

| 情况 | 处理 |
| --- | --- |
| 下载失败、得到网页或解压失败 | 从 v0.6.0 Release 找同名附件；未发布就等待本版，不把网页改名为 ZIP。 |
| 缺少 SKILL.md | 选中直接含 `SKILL.md` 的 `gift-development-service` 文件夹，其他四份文件及其子目录也要在。 |
| 列表找不到 | 核对账号和工作环境，刷新后搜英文名称；Codex 必要时重启。不要连续重复导入。 |
| 已存在或有两个同名技能 | 按升级步骤检查，只留一个有效安装；自改资料先备份。 |
| 能看到，回答却像没使用 | 新开对话并明确选中或要求读取。模型说“我用了”不等于核到了读取过程。 |
| WorkBuddy 报 1001 | 同模型新开普通对话，只要求回复 OK。对照也失败时先处理客户端或账号，不反复重装。 |
| 豆包提示额度不足或连接失败 | 保留当前进度，按平台规则等待或处理连接；别把未得到的业务答复记为通过。 |
| 回答直接建议打样、报价或备货 | 暂停采用，要求回到需求与资源匹配判断；这是回答质量问题，不一定是安装失败。 |
| 把未知交期写死或结论没条件 | 要求保留未知项，重算依赖，并说清什么条件改变继续、调整或暂缓。 |

仍有问题，在 [Issues](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/issues)写清工具版本、系统、包版本、停留步骤与报错。截图先去除账号和客户资料，不公开凭据或私人聊天。

<a id="sources"></a>
## 指引依据与验证边界

WorkBuddy 上传与管理方式、Codex 用户技能目录依据上述官方说明，2026-10-21核读。豆包菜单依据此前实机观察；本次读取官方页面未成功，保留该链接供用户核对当前入口。菜单或账号能力变化时以当前客户端为准。

本版维护检查、模型代偿与三端原生业务验证分别记录在[验证摘要](https://github.com/Friedrich-arthur/Gift-Category-Development-Skill/blob/main/docs/VERIFICATION.md)。安装成功、客户端可见和完整咨询通过是三件事，不能互相替代。
