---
name: wsl-tesseract-ocr-pipeline
description: 在WSL无root环境下，通过dpkg-deb手动解压方式安装Tesseract OCR并处理中文PDF扫描件的完整流水线
tags: [ocr, tesseract, wsl, pdf, chinese]
---

# WSL无root环境下Tesseract OCR完整流水线

## Problem
WSL（Ubuntu）没有root权限，无法用apt-get安装tesseract-ocr。但需要OCR识别PDF扫描件（中文合同）。

## Solution：dpkg-deb手动解压安装

### 步骤

**1. 下载所有相关deb包**
```bash
cd /home/dministrator/tesseract_full
apt-get download tesseract-ocr tesseract-ocr-chi-sim liblept5 libtesseract4 libgif7 2>&1
```

**2. 创建提取目录并解压（维持deb内部路径结构）**
```bash
mkdir -p extracted
dpkg-deb -x tesseract-ocr_4.1.1-2.1build1_amd64.deb extracted/
dpkg-deb -x liblept5_1.82.0-3build1_amd64.deb extracted/
dpkg-deb -x libtesseract4_4.1.1-2.1build1_amd64.deb extracted/
dpkg-deb -x tesseract-ocr-chi-sim_1%3a4.00~git30-7274cfa-1.1_all.deb extracted/
dpkg-deb -x libgif7*.deb extracted/
```

**3. 下载中文语言包**（deb里的不是独立的，需从deb内提取）
```bash
# 方法A：从deb内提取（适用于4.00~git30版本）
dpkg-deb -x tesseract-ocr-chi-sim_1%3a4.00~git30-7274cfa-1.1_all.deb extracted/
# 语言包在: extracted/usr/share/tesseract-ocr/4.00/tessdata/chi_sim.traineddata

# 方法B：从Aliyun镜像下载（注意：curl可能返回0字节空文件，需验证大小）
curl -L -o /tmp/chi_sim.traineddata "https://mirrors.aliyun.com/tesseract/4.00/chi_sim.traineddata"
ls -la /tmp/chi_sim.traineddata  # 验证文件大小>0才能用
```

**4. 配置LD_LIBRARY_PATH并验证**
```bash
export LD_LIBRARY_PATH=/home/dministrator/tesseract_full/extracted/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
TESS=/home/dministrator/tesseract_full/extracted/usr/bin/tesseract
$TESS --version
$TESS --list-langs  # 应包含 chi_sim
```

**5. 用ldd检查缺失库，循环下载**
```bash
ldd $TESS | grep "not found"
# 对于每个缺失库：apt-get download <lib> && dpkg-deb -x <lib>.deb extracted/
```

### Python OCR使用示例

```python
import subprocess, os, fitz  # PyMuPDF

TESS_BIN = "/home/dministrator/tesseract_full/extracted/usr/bin/tesseract"
TESSDATA = "/home/dministrator/tesseract_full/extracted/usr/share/tesseract-ocr/4.00/"
LIB_DIR  = "/home/dministrator/tesseract_full/extracted/usr/lib/x86_64-linux-gnu"

def render_pdf_page(pdf_path, page_num=0, dpi=200):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_path = f"/tmp/page_{os.getpid()}_{page_num}.png"
    pix.save(img_path)
    return img_path

def ocr_image(img_path):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = LIB_DIR
    subprocess.run(
        [TESS_BIN, img_path, "/tmp/ocr_out",
         "--tessdata-dir", TESSDATA, "-l", "chi_sim", "--psm", "6", "quiet"],
        capture_output=True, timeout=60, env=env
    )
    with open("/tmp/ocr_out.txt", "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
```

## Pitfalls

1. **中文路径空格**：WSL处理含空格的中文Windows路径时子进程调用容易失败，输出文件优先写到 `/tmp/`
2. **语言包位置**：tesseract-ocr-chi-sim deb里的traineddata路径非标准位置，需手动复制到 `$TESSDATA_PREFIX/tessdata/`
3. **libarchive依赖**：新版tesseract依赖libarchive，需额外下载解压
4. **LD_LIBRARY_PATH必须设置**：每次调用tesseract前都要export
5. **`--quiet` flag**：部分版本不支持，去掉该参数保险
6. **DPI分辨率**：PDF渲染时建议 DPI>=144（使用 `fitz.Matrix(2.0, 2.0)` 即144dpi），低于此值中文OCR识别率显著下降
7. **chi_sim.traineddata下载**：Aliyun镜像可能返回0字节空文件，下载后必须 `ls -la` 验证文件大小
8. **先验证JSON结构再写脚本**：读取源JSON文件后，务必先用 `python -c "import json; print(list(json.load(open(...))[0].keys()))"` 确认字段名，再写处理脚本。避免字段名假设错误（如`file_path` vs `path`、`file_name` vs `filename`）导致批量Worker全部失败

## 批量并行Worker最佳实践

**第一步（必须）：先读源文件结构**
```python
# 先确认数据结构，再写处理脚本
with open("源文件清单.json") as f:
    data = json.load(f)
print(f"总条数: {len(data)}, 第一条keys: {list(data[0].keys())}")
print(f"示例: {data[0]}")
```

**第二步：写脚本时用实际key名**
```python
fp = item["path"]        # 不是 item["file_path"]
fname = item["filename"] # 不是 item["file_name"]
```

**第三步：先小规模测试（0-5条），确认OK后再全量**
```bash
python3 worker.py 0 5 inputs.json /tmp/test_output.json && echo "OK"
```

**第四步：输出写到 /tmp/**：避免含空格中文路径导致的写入失败

**JSON字段名经验值**：
- 自己生成的清单 → 通常用 `path`、`filename`
- 外部导入的 → 可能是 `file_path`、`file_name`，必须先验证

## Verification
```bash
$TESS --version        # 应输出版本
$TESS --list-langs    # 应包含 chi_sim
```
