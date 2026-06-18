# 首次环境配置（setup）

agent 第一次在某台机器上用 lawiki、或检测到环境缺失时，照此走一遍。**每一步都让用户看到你在做什么**——尤其安装时明确说「正在安装环境……」。

lawiki 需要三样：① Python 3.11+（跑本 skill 自带的校验，零第三方依赖）② makeitdown（上游转换器，把各式文件转成 md）③ Obsidian（人看 wiki 用，可选、不自动装 GUI）。

## 第 1 步 · 检测（并把结果告诉用户）

依次在 shell 跑，报告每项有无：
- `python --version` —— 需 3.11+。
- `uv --version` —— 装 makeitdown 用（没有也可后面装）。
- `makeitdown --help` —— 上游转换器。

## 第 2 步 · 让用户选 OCR 方式（装 makeitdown 前必问）

扫描件 / 图片需要 OCR。两种模式，**把这张优缺点对比给用户，让他选**：

| | 本地 PaddleOCR | 云端 PaddleOCR（AI Studio） |
|---|---|---|
| 转换时联网 | **不需要** | 需要 |
| 账号 / token | **不需要**，装完即用 | 需去百度 AI Studio 申请 |
| 隐私 | 文件**不出本机** | 文件**上传到百度服务器** |
| 费用 | 免费 | 可能按量计费 |
| 体积 / 速度 | 大（几百 MB）、转换较慢 | 小、装得快、转换较快 |

- **选本地** → 适合涉密案件、能接受慢一点、磁盘够。
- **选云端** → 适合要轻快、案件不涉高度机密、愿意联网。

### 选云端：申请 token（大陆可直连）

请用户点开 **百度 AI Studio 申请 API：https://aistudio.baidu.com/** ，拿到 token 后设环境变量：
```
PADDLEOCR_AISTUDIO_TOKEN=<你的token>
```
（或转换时传 `--cloud-token <token>`。）token 绝不写进任何文件、不提交。

## 第 3 步 · 安装（明确告诉用户「正在安装环境……」）

按所选 OCR 模式装 makeitdown（**大陆走 gitee 镜像 + 清华 PyPI 源**，避开卡顿）：

- **本地版**：
  ```
  uv tool install --python 3.11 --index https://pypi.tuna.tsinghua.edu.cn/simple "makeitdown[local] @ git+https://gitee.com/code-lawyer/makeitdown.git"
  ```
- **云端版**：
  ```
  uv tool install --python 3.11 --index https://pypi.tuna.tsinghua.edu.cn/simple "makeitdown @ git+https://gitee.com/code-lawyer/makeitdown.git"
  ```
- **缺 Python / uv**：先装 uv（Windows：`winget install astral-sh.uv`；macOS/Linux：`curl -LsSf https://astral.sh/uv/install.sh | sh`），uv 能顺带备好 Python。装系统软件可能要权限——装不动就把命令交给用户自己跑，别硬来。
- **本 skill 的校验（lint）**：零依赖，只要有 Python 即可，**无需安装**。
- **海外用户**：去掉 `--index` 参数，把 `gitee.com` 换成 `github.com`。

装完用 `makeitdown --help` 验证；提示用户命令找不到时跑 `uv tool update-shell` 后开新终端。

## 第 4 步 · 优雅降级

makeitdown 实在装不上时**不阻塞核心**：若用户已有别处转好的 `_md/`，lawiki 仍能直接 ingest + 跑校验，只是不能在本机做转换。把这点告诉用户。

## 第 5 步 · 告诉用户怎么激活

环境就绪后，明确告诉用户**以后怎么启动**：

> 把法律文件放进案件目录的 `原始资料/`，然后对我说下面任一句即可启动：
> 「**整理案件资料**」「**把案件资料建成 wiki**」「**建案件库 / 建案件 wiki**」「**处理这个案子**」「**ingest case files**」「**build a case wiki**」。
