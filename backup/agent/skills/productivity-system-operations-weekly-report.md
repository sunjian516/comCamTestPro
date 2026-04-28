---
name: system-operations-weekly-report
description: 分析系统运行部周报，生成工作量排行、亮点工作、风险提示，供科室绩效考核参考
---

# System Operations Department Weekly Report Analysis

Analyze weekly work summary Word documents (系统运行部一周工作总结) sent by the department head, generating structured workload/performance insights.

## Trigger
User sends a Word document via WeChat: `系统运行部一周工作总结（YYMMDD-YYMMDD）.docx`

## Input Files
Location: `/home/dministrator/.hermes/cache/documents/`
File naming: `系统运行部一周工作总结（0330-0405）.docx`

## Analysis Dimensions

### 1. Workload Ranking
Count task entries per person (extract via regex pattern `（姓名）` per paragraph)

### 2. Category Classification
- **安全类**: 安全隐患、安全事件、安全督查、信息安全、病毒、木马、漏洞扫描、防病毒、等保
- **跨部门协作**: 配合、协调、沟通、对接、共同、踏勘
- **项目推进**: 项目、招标、委外、合同、验收、流转、推进

### 3. Highlights
Identify tasks with high complexity: cross-dept + project, or security + project

### 4. Risk Alerts
Flag: 故障上升趋势、磁盘空间不足、安全事件、仓库管理问题

## Output Format
```
## 系统运行部周报分析（0420-0426）

### 一、工作量排行
| 人员 | 本周任务数 | vs上周 |

### 二、亮点工作
- (列出3-5项最突出工作，附执行人)

### 三、⚠️ 风险提示
- (列出需关注的风险事项)
```

## Known Personnel
张勇、戴天宇、杨烨、严冬、周烨琳、韩暑、王躬亲、冯晋卿、陈裔、钟朝晖、张志豪、滕志伟

## Key Files
- Weekly reports: `/home/dministrator/.hermes/cache/documents/系统运行部一周工作总结*.docx`
- Device inventory: `/mnt/e/her/workspace/02 知识库/设备台账.xls`
- T2泊位系统手册: `/mnt/e/her/workspace/02 知识库/03 T2泊位系统运维手册/`
