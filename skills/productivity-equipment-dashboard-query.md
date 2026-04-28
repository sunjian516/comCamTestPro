---
name: equipment-dashboard-query
description: 从设备台账Excel（约28000行）查询设备数量、分布的技能——用于航显系统、配电设备、门禁等资产统计
---

# 设备台账查询技能

从 `设备台账.xls`（约28,000行）中查询设备数量、分布等信息。

## 文件路径
`/mnt/e/her/workspace/02 知识库/设备台账.xls`
sheet名：`设备台账`，表头在第3行（header=2）

## 常用查询

### 航显系统显示屏数量（T1+T2）
```python
import pandas as pd
df = pd.read_excel('/mnt/e/her/workspace/02 知识库/设备台账.xls', sheet_name='设备台账', header=2)

# 筛选纯显示屏（排除工控机/OPS/工作站/服务器）
mask = df['设备名称'].str.contains('TFT.*显示屏|LCD.*显示屏|LED.*显示屏|显示屏', na=False, regex=True)
mask2 = ~df['设备名称'].str.contains('工控机|OPS|工作站|服务器', na=False)
screens = df[mask & mask2]

# 分T1/T2统计
for sys in ['T1航显系统', 'T2航显系统']:
    s = screens[screens['设备系统'] == sys]
    print(f'{sys}: {len(s)} 块')
    print(s['设备名称'].value_counts())
```

### 按设备系统统计设备数量
```python
df['设备系统'].value_counts()
```

### 按设备名称分类统计
```python
df['设备名称'].value_counts()
```

### 搜索含关键词的设备
```python
mask = df['设备名称'].str.contains('关键词', na=False)
result = df[mask]
```

### 按位置统计
```python
df['位置'].value_counts()
```

## 注意事项
- 设备台账约28,000行，搜索"航显"会包含工控机/OPS等后台设备
- 纯屏幕统计需排除：工控机、OPS工控机、工作站、服务器
- 设备系统列值如 'T1航显系统'、'T2航显系统'、'中航信离港系统(T1)' 等
- 使用 `mask & mask2` 组合筛选比单独筛选更准确
