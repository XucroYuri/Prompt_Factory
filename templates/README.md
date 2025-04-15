# 模板目录

## 模板结构

每个模板必须包含两个部分：

1. `## System Message` - 系统消息，定义AI角色和处理逻辑
2. `## User Message` - 用户消息，必须包含`{PROMPT}`占位符

## 可用模板

- `standard.txt`: 标准提示词优化模板（INTJ架构师性格特点）
- `concise.txt`: 简洁版提示词优化模板，专注于效率

## 自定义模板

在此目录添加新的.txt文件，遵循上述结构，确保System Message明确指定角色和处理逻辑，User Message包含{PROMPT}占位符。