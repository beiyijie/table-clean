# 表格清洗机 v2.0

自动化表格数据清洗工具，采用**"强制规则 + 可配置选项"**设计，确保基础数据质量的同时支持用户高度自定义。

## 功能特性

### 强制规则（自动执行，不可跳过）
- 清理全空行/列
- 空字符串/纯空格 → NaN
- 列名规范化（去空格、小写、去特殊字符）
- 去除不可见字符（`\t`、`\n`、`\r`、零宽字符等）
- 文本去首尾空格
- 全角转半角
- 连续空格合并为一个

### 可选规则（默认开启，用户可自定义）
- 去除重复行
- 范围校验（年龄 0-150、薪资>0、分数 0-100）
- 异常值检测与移除（IQR/Z-Score）
- 缺失值智能填充（数值=均值，文本=众数）
- 日期标准化
- 分类值统一（自动去除"市/省/自治区"后缀）
- 邮箱格式校验

### 其他功能
- 表格合并与拆分
- 清洗报告导出

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```bash
# 一键完整清洗（所有默认规则）
python main.py input.csv -o output.csv --auto-clean

# 一键清洗 + 生成报告
python main.py input.csv -o output.csv --auto-clean --report report.txt

# 自定义：关闭去重和异常值检测
python main.py input.csv -o output.csv --auto-clean --no-duplicates --no-outliers

# 自定义：修改缺失值策略
python main.py input.csv -o output.csv --auto-clean --missing-numeric median --missing-text ffill

# 自定义：调整异常值阈值
python main.py input.csv -o output.csv --auto-clean --outlier-method zscore --outlier-threshold 3

# 关闭范围校验
python main.py input.csv -o output.csv --auto-clean --no-range-check

# 合并多个表格
python main.py file1.csv --merge file2.csv file3.csv -o merged.csv

# 按列拆分表格
python main.py data.csv --split-by category -o output/

# 按行数拆分
python main.py data.csv --split-chunks 1000 -o chunks/
```

### Python API 使用

```python
import pandas as pd
from table_cleaner import TableCleaner
from report_generator import ReportGenerator

# 加载数据
df = pd.read_csv("data.csv")
original_df = df.copy()

# 方式一：一键清洗（所有默认规则）
cleaner = TableCleaner(df)
cleaner.auto_clean()
cleaned_df = cleaner.get_df()

# 方式二：自定义配置
cleaner = TableCleaner(df, config={
    "remove_duplicates": True,
    "missing_strategy": {"numeric": "median", "text": "mode"},
    "outlier_method": "zscore",
    "outlier_threshold": 3.0,
    "range_rules": {"age": (0, 150), "salary": (0, None)},
    "date_format": "%Y-%m-%d",
    "validate_email": True,
    "remove_city_suffix": True,
    "category_mapping": {"department": {"技术部": "研发部"}},
})
cleaner.auto_clean()
cleaned_df = cleaner.get_df()

# 方式三：分步执行
cleaner = TableCleaner(df)
cleaner.apply_basic_rules()  # 强制规则
cleaner.remove_duplicates()  # 可选规则按需调用
cleaner.handle_missing_values()
cleaned_df = cleaner.get_df()

# 生成报告
ReportGenerator.generate_report(original_df, cleaned_df, cleaner.cleaning_log, "report.txt")

# 保存结果
cleaned_df.to_csv("cleaned.csv", index=False)
```

## 命令行参数

### 基础参数
| 参数 | 说明 |
|------|------|
| `input` | 输入文件路径 (必填) |
| `-o, --output` | 输出文件路径 |
| `--auto-clean` | 一键完整清洗 |
| `--report` | 生成清洗报告路径 |

### 可选规则开关
| 参数 | 说明 | 默认 |
|------|------|------|
| `--no-duplicates` | 关闭去重 | 开启 |
| `--missing-numeric` | 数值列缺失值策略: mean/median/ffill/bfill/drop | mean |
| `--missing-text` | 文本列缺失值策略: mode/ffill/bfill/drop | mode |
| `--no-outliers` | 关闭异常值检测 | 开启 |
| `--outlier-method` | 异常值检测方法: iqr/zscore | iqr |
| `--outlier-threshold` | 异常值阈值 | 1.5 |
| `--no-range-check` | 关闭范围校验 | 开启 |
| `--no-email-check` | 关闭邮箱校验 | 开启 |
| `--no-category-unify` | 关闭分类值统一 | 开启 |
| `--date-format` | 日期输出格式 | %Y-%m-%d |

### 合并/拆分
| 参数 | 说明 |
|------|------|
| `--merge` | 合并多个文件 |
| `--split-by` | 按列拆分表格 |
| `--split-chunks` | 按行数拆分表格 |

## Python API 配置说明

### config 参数详解

```python
config = {
    # 去重
    "remove_duplicates": True,           # 是否去重
    "duplicate_subset": None,            # 按哪些列去重，None=全行匹配

    # 缺失值处理
    "missing_strategy": {
        "numeric": "mean",               # 数值列: mean/median/ffill/bfill/drop
        "text": "mode"                   # 文本列: mode/ffill/bfill/drop
    },

    # 异常值
    "outlier_method": "iqr",             # 检测方法: iqr/zscore
    "outlier_threshold": 1.5,            # 阈值，越大越宽松

    # 范围校验
    "range_rules": {
        "age": (0, 150),                 # 年龄范围
        "salary": (0, None),             # 薪资下限，None=无上限
        "score": (0, 100),               # 分数范围
        "performance_score": (0, 100),   # 绩效分数范围
    },

    # 日期
    "date_format": "%Y-%m-%d",           # 日期输出格式
    "auto_detect_dates": True,           # 自动检测日期列

    # 分类值统一
    "remove_city_suffix": True,          # 自动去除"市/省/自治区"后缀
    "category_mapping": {                # 自定义同义词映射
        "department": {"技术部": "研发部"},
        "city": {"北京市": "北京"}
    },

    # 邮箱校验
    "validate_email": True,              # 是否校验邮箱格式
    "email_columns": ["email"],          # 邮箱列名关键词
}
```

## 项目结构

```
表格清洗机/
├── main.py                  # 主程序入口
├── table_cleaner.py         # 核心清洗模块（强制规则 + 可配置选项）
├── table_merger_splitter.py # 表格合并拆分模块
├── report_generator.py      # 报告生成模块
├── requirements.txt         # 依赖文件
└── README.md               # 说明文档
```
