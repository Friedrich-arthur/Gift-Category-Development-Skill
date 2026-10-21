# 维护者检查

用户安装的目录只有 `gift-development-service/`，不需要 Python、开发依赖或本目录。

```text
python -m pip install -r requirements-dev.txt
python -B -X utf8 -m unittest discover -s tests -v
python -B -X utf8 tools/check_skill.py --build
python -B -X utf8 tools/check_skill.py --verify dist/gift-development-service.zip --manifest dist/gift-development-service.manifest.json
```

`--skill <目录>` 可检查隔离副本；`--output <目录>` 可指定包外输出位置。默认产物位于忽略提交的 `dist/`。CI 只检查并上传运行产物，不发布市场。

一个不可变 `SkillPackage` 保存校验过的目录名与 LF 文件字节；源码检查和 ZIP 回读共用这一份合同。相比在源码、ZIP 和清单之间传递松散字典，此结构把路径、引用和字节规则集中在一个维护模块。包只接受 UTF-8 文本资源；YAML 需要 `name`、`description` 和字符串 `metadata.version`。

使用固定版本的 `markdown-it-py` 按 CommonMark 语法提取 Markdown 链接、图片与引用式定义，另核显式未定义标签。实际 HTML token 由标准库 `HTMLParser` 提取 `href`/`src`，包括无引号属性、大小写属性名和 HTML 字符实体。HTML 注释、代码块和行内代码里的示意链接不作为资料引用。解析器只提取目标，外部 HTTP、HTTPS、邮件链接由工具自己的规则分类，不联网验证；其他方案或包外目标仍拒绝。凭据检查拒绝已知密钥格式、私钥头和敏感赋值；它不是任意秘密的完备识别器。目录和祖先路径拒绝符号链接、Windows junction 和其他重解析点；源文件不能执行，也不接受脚本后缀。本工具用于静止的维护者工作区，不处理被其他进程同时替换的源目录。

ZIP 使用排序文件名、1980-01-01 时间、固定 0644 权限、LF 和无压缩存储，避免压缩库版本影响字节。包外 JSON 清单记录 ZIP 与逐文件 SHA-256；这是完整性校验，不是签名。回读先拒绝绝对或越界路径、重复条目、链接和过大内容，再限量读取成员，在内存中核对清单与正文，全程不解压。限制为 128 个文件、单文件 1 MiB、合计 8 MiB、ZIP 16 MiB。

源码与ZIP共用不区分大小写的文件路径检查。一个文件不能同时成为另一文件的父目录，例如 `a.md` 与 `a.md/child.md`；`a.md` 与 `a.md2/child.md` 则可以共存。ZIP在读取成员内容前拒绝这类冲突，避免把不能落盘的文件树报告为有效。

本地验证不覆盖 WorkBuddy 识别、自然调用、模型输出质量或真人采用。Windows 无符号链接权限时相关测试明确跳过；junction 和普通路径越界另测。
