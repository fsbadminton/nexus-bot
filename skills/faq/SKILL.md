---
name: faq
description: 查询 FAQ 知识库，回答用户常见问题
metadata:
  nanobot:
    always: true
---

# FAQ 知识库查询

当用户提出产品相关问题时，优先从知识库中查找答案。

## 使用方式

1. 使用 `read_file` 或 `grep` 工具搜索 `knowledge/faq/` 目录下的 Markdown 文件
2. 根据匹配到的 FAQ 内容回答用户
3. 如果知识库中没有找到相关信息，告知用户并建议创建工单

## 知识库结构

```
knowledge/faq/
├── general.md      # 通用问题
├── account.md      # 账户相关
├── billing.md      # 计费相关
├── technical.md    # 技术问题
└── ...
```

## 搜索策略

- 先用 `grep` 按关键词搜索所有 FAQ 文件
- 如果有多个匹配，选择最相关的条目回答
- 引用来源文件名，方便后续更新

## 注意事项

- 只回答知识库中明确记录的内容
- 不要编造或推测答案
- 如果 FAQ 内容过时，提醒用户以官方最新信息为准
