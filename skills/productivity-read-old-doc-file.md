---
name: read-old-doc-file
description: 在WSL无root环境下读取旧版.doc文件（Binary Word格式）——通过olefile解析OLE2结构，直接扫描WordDocument流的UTF-16 LE中文文本
triggers:
  - ".doc文件无法读取"
  - "Composite Document File V2"
  - "antiword not found"
---

# 读取旧版 .doc 文件（无 antiword/libreoffice）

## 触发条件
需要读取 `.doc` 文件（非 `.docx`）但系统中没有 `antiword`、`catdoc` 或 `libreoffice`。

## 问题背景
WSL 环境（无 root）无法 apt-get 安装工具，旧版 `.doc`（Binary Word / Office 2003 格式）是 OLE2 Compound Document，`python-docx` 只支持新版 `.docx`。

## 解决方案

### 依赖
```bash
pip install --user olefile
# 或 pip install --user oletools  (包含 olefile)
```

### 核心方法：UTF-16 LE 扫描

```python
import olefile, struct

path = '/path/to/file.doc'
ole = olefile.OleFileIO(path)
doc_stream = ole.openstream('WordDocument').read()

result = []
i = 0
current = b''
while i < len(doc_stream) - 1:
    w = struct.unpack('<H', doc_stream[i:i+2])[0]
    # 保留中文字符 + 常用ASCII（空格、换行、字母、数字）
    if (0x4e00 <= w <= 0x9fff or  # 中文
        w == 0x0020 or w == 0x000a or w == 0x000d or  # 空格/换行
        (0x0030 <= w <= 0x0039) or  # 数字
        (0x0041 <= w <= 0x005a) or  # 大写字母
        (0x0061 <= w <= 0x007a)):   # 小写字母
        current += struct.pack('<H', w)
    else:
        if len(current) >= 2:
            try:
                decoded = current.decode('utf-16-le').strip()
                if decoded and any('\u4e00' <= c <= '\u9fff' for c in decoded):
                    result.append(decoded)
            except:
                pass
        current = b''
    i += 2

full_text = '\n'.join(result)
print(full_text)
```

### 验证文件类型
```bash
file /path/to/file.doc
# 输出包含 "Composite Document File V2 Document" 即为旧版 .doc
```

## 已知局限
- 本方法直接从二进制流提取 UTF-16 LE 文本，可能包含少量乱码字符（非中文片段）
- 复杂的 Word 格式特性（表格、图像、特殊格式）无法保留
- 适用于纯文本为主的法律合同、文档

## 实践补充（2026-04-30）

**olefile 导入注意**：WSL 中 `python3`（hermes-agent venv）无法导入 olefile，但 `python3.10`（系统 Python）可以：
```bash
python3.10 -c "import olefile; print('ok')"  # 成功
python3 -c "import olefile; print('ok')"     # 失败（ModuleNotFoundError）
```
**解决方案**：使用 `python3.10` 运行脚本，或 `pip install --user oletools` 安装到用户目录后用 `python3.10`。

**输出文件写到 /tmp/**：避免含空格中文路径导致的写入失败。

### 调试技巧
```bash
# 1. 先用 file 命令确认文件类型
file /path/to/file.doc
# 输出: Composite Document File V2 Document → 旧版 .doc，可用本方法
# 输出: ZIP archive → 新版 .docx，用 python-docx

# 2. 查看可用流（调试用）
python3.10 -c "
import olefile
ole = olefile.OleFileIO('/path/to/file.doc')
for s in ole.listdir():
    print('/'.join(s))
"

# 3. 快速验证中文内容存在
python3.10 -c "
import olefile, struct
ole = olefile.OleFileIO('/path/to/file.doc')
data = ole.openstream('WordDocument').read()
# 找 UTF-16 LE 中文序列
has_cn = any(0x4e00 <= struct.unpack('<H', data[i:i+2])[0] <= 0x9fff
             for i in range(0, len(data)-1, 2))
print('Has Chinese:', has_cn)
"
```

### 完整读取流程（可直接复制使用）
```python
import olefile, struct, sys

def read_old_doc(path: str) -> str:
    ole = olefile.OleFileIO(path)
    doc_stream = ole.openstream('WordDocument').read()
    result, current = [], b''
    i = 0
    while i < len(doc_stream) - 1:
        w = struct.unpack('<H', doc_stream[i:i+2])[0]
        if (0x4e00 <= w <= 0x9fff or w in (0x0020, 0x000a, 0x000d) or
            0x0030 <= w <= 0x0039 or 0x0041 <= w <= 0x005a or 0x0061 <= w <= 0x007a):
            current += struct.pack('<H', w)
        else:
            if len(current) >= 2:
                try:
                    dec = current.decode('utf-16-le').strip()
                    if dec and any('\u4e00' <= c <= '\u9fff' for c in dec):
                        result.append(dec)
                except: pass
            current = b''
        i += 2
    return '\n'.join(result)

if __name__ == '__main__':
    text = read_old_doc(sys.argv[1])
    with open('/tmp/doc_output.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Extracted {len(text)} chars → /tmp/doc_output.txt")
```

## 备选方案（按优先级）
1. `pip install --user textract` + 安装 `antiword` 二进制
2. Windows 上用 `winword.exe` 转换（如果有 PATH）
3. 手动复制粘贴（最简单的用户方案）
