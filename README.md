# 表格清洗机 TableCleaner

> 自动化表格数据清洗工具 — 强制规则保障基础质量，可配置选项满足个性化需求。

---

## ✨ 特性概览

### 🔒 强制规则（自动执行，不可跳过）

| 规则 | 说明 |
|------|------|
| 清理全空行/列 | 删除完全为空的行和列 |
| 空字符串转 NaN | `""`、`"   "` 等假值统一转为缺失值 |
| 列名规范化 | 去空格、转小写、去除特殊字符 |
| 去除不可见字符 | `\t`、`\n`、`\r`、零宽字符等 |
| 文本去首尾空格 | 所有文本列统一 trim |
| 全角转半角 | 数字、字母统一为半角 |
| 连续空格合并 | 文本内部多个空格合并为一个 |

### ⚙️ 可选规则（默认开启，用户可自定义）

| 规则 | 默认配置 | 可调整项 |
|------|----------|----------|
| 去除重复行 | 全行匹配 | 可关闭 / 指定列 |
| 范围校验 | 年龄 0-150, 薪资>0 | 自定义每列范围 |
| 异常值检测 | IQR 法, 阈值 1.5 | 支持 Z-Score / 调阈值 |
| 缺失值填充 | 数值=均值, 文本=众数 | 5 种策略可选 |
| 日期标准化 | `%Y-%m-%d` | 自定义格式 |
| 分类值统一 | 去"市/省/自治区"后缀 | 自定义同义词映射 |
| 邮箱校验 | 基本格式检查 | 可关闭 |

### 📦 其他功能

- **表格合并** — 按行拼接 / 按列关联合并
- **表格拆分** — 按列值拆分 / 按行数拆分
- **清洗报告** — 生成 TXT / CSV 格式的详细报告

---

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 一键清洗（最简用法）

```bash
python main.py input.csv -o output.csv --auto-clean
```

### 一键清洗 + 生成报告

```bash
python main.py input.csv -o output.csv --auto-clean --report report.txt
```

---

## 📖 使用指南

### 命令行使用

#### 场景 1：默认清洗

```bash
python main.py data.csv -o cleaned.csv --auto-clean
```

#### 场景 2：自定义策略

```bash
# 关闭去重和异常值检测，缺失值用中位数填充
python main.py data.csv -o cleaned.csv \
  --auto-clean \
  --no-duplicates \
  --no-outliers \
  --missing-numeric median
```

#### 场景 3：调整异常值检测

```bash
# 使用 Z-Score 方法，阈值放宽到 3
python main.py data.csv -o cleaned.csv \
  --auto-clean \
  --outlier-method zscore \
  --outlier-threshold 3
```

#### 场景 4：关闭特定校验

```bash
# 关闭范围校验和邮箱校验
python main.py data.csv -o cleaned.csv \
  --auto-clean \
  --no-range-check \
  --no-email-check
```

#### 场景 5：合并多个文件

```bash
python main.py file1.csv --merge file2.csv file3.csv -o merged.csv
```

#### 场景 6：拆分表格

```bash
# 按列值拆分
python main.py data.csv --split-by category -o output/

# 按行数拆分（每 1000 行一个文件）
python main.py data.csv --split-chunks 1000 -o chunks/
```

---

### Python API 使用

#### 方式一：一键清洗

```python
from table_cleaner import TableCleaner

cleaner = TableCleaner(df)
cleaner.auto_clean()
cleaned_df = cleaner.get_df()
```

#### 方式二：自定义配置

```python
from table_cleaner import TableCleaner

cleaner = TableCleaner(df, config={
    "remove_duplicates": True,
    "missing_strategy": {"numeric": "median", "text": "mode"},
    "outlier_method": "zscore",
    "outlier_threshold": 3.0,
    "range_rules": {"age": (0, 150), "salary": (0, None)},
    "date_format": "%Y-%m-%d",
    "validate_email": True,
    "remove_city_suffix": True,
    "category_mapping": {
        "department": {"技术部": "研发部"},
        "city": {"北京市": "北京"}
    },
})
cleaner.auto_clean()
cleaned_df = cleaner.get_df()
```

#### 方式三：分步执行

```python
from table_cleaner import TableCleaner

cleaner = TableCleaner(df)

# 强制规则（自动执行）
cleaner.apply_basic_rules()

# 可选规则（按需调用）
cleaner.remove_duplicates()
cleaner.validate_ranges()
cleaner.remove_outliers()
cleaner.handle_missing_values()
cleaner.standardize_dates()
cleaner.unify_categories()

cleaned_df = cleaner.get_df()
```

#### 生成报告

```python
from report_generator import ReportGenerator

ReportGenerator.generate_report(
    original_df, cleaned_df,
    cleaner.cleaning_log,
    "report.txt"
)
```

---

## 📋 命令行参数

### 基础参数

| 参数 | 说明 |
|------|------|
| `input` | 输入文件路径（必填） |
| `-o, --output` | 输出文件路径 |
| `--auto-clean` | 一键完整清洗 |
| `--report` | 生成清洗报告路径 |

### 可选规则开关

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--no-duplicates` | 关闭去重 | 开启 |
| `--missing-numeric` | 数值列策略：`mean` / `median` / `ffill` / `bfill` / `drop` | `mean` |
| `--missing-text` | 文本列策略：`mode` / `ffill` / `bfill` / `drop` | `mode` |
| `--no-outliers` | 关闭异常值检测 | 开启 |
| `--outlier-method` | 检测方法：`iqr` / `zscore` | `iqr` |
| `--outlier-threshold` | 异常值阈值（越大越宽松） | `1.5` |
| `--no-range-check` | 关闭范围校验 | 开启 |
| `--no-email-check` | 关闭邮箱校验 | 开启 |
| `--no-category-unify` | 关闭分类值统一 | 开启 |
| `--date-format` | 日期输出格式 | `%Y-%m-%d` |

### 合并 / 拆分

| 参数 | 说明 |
|------|------|
| `--merge` | 合并多个文件 |
| `--split-by` | 按列值拆分表格 |
| `--split-chunks` | 按行数拆分表格 |

---

## 🔧 API 配置详解

### `config` 参数完整说明

```python
config = {
    # ── 去重 ──────────────────────────
    "remove_duplicates": True,           # 是否去重
    "duplicate_subset": None,            # 按哪些列去重，None = 全行匹配

    # ── 缺失值处理 ─────────────────────
    "missing_strategy": {
        "numeric": "mean",               # 数值列: mean / median / ffill / bfill / drop
        "text": "mode"                   # 文本列: mode / ffill / bfill / drop
    },

    # ── 异常值检测 ─────────────────────
    "outlier_method": "iqr",             # 检测方法: iqr / zscore
    "outlier_threshold": 1.5,            # 阈值，越大越宽松

    # ── 范围校验 ───────────────────────
    "range_rules": {
        "age": (0, 150),                 # 年龄范围
        "salary": (0, None),             # 薪资下限，None = 无上限
        "score": (0, 100),               # 分数范围
        "performance_score": (0, 100),   # 绩效分数范围
    },

    # ── 日期标准化 ─────────────────────
    "date_format": "%Y-%m-%d",           # 日期输出格式
    "auto_detect_dates": True,           # 自动检测日期列

    # ── 分类值统一 ─────────────────────
    "remove_city_suffix": True,          # 自动去除 "市/省/自治区" 后缀
    "category_mapping": {                # 自定义同义词映射
        "department": {"技术部": "研发部"},
        "city": {"北京市": "北京"}
    },

    # ── 邮箱校验 ───────────────────────
    "validate_email": True,              # 是否校验邮箱格式
    "email_columns": ["email"],          # 邮箱列名关键词
}
```

---

## 📁 项目结构

```
table-clean/
├── main.py                  # 命令行入口
├── table_cleaner.py         # 核心清洗模块（强制规则 + 可配置选项）
├── table_merger_splitter.py # 表格合并 / 拆分模块
├── report_generator.py      # 清洗报告生成模块
├── requirements.txt         # Python 依赖
├── .gitignore
└── README.md
```

---

## 📄 License

MIT
