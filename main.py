import argparse
import pandas as pd
import os
import sys
from table_cleaner import TableCleaner
from table_merger_splitter import TableMergerSplitter
from report_generator import ReportGenerator


def load_file(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    else:
        print(f"错误: 不支持的文件格式 - {file_path}")
        sys.exit(1)


def save_file(df: pd.DataFrame, output_path: str):
    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    elif output_path.endswith((".xlsx", ".xls")):
        df.to_excel(output_path, index=False)
    else:
        print(f"错误: 不支持的输出格式 - {output_path}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="表格清洗机 - 自动化数据清洗工具")
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--auto-clean", action="store_true", help="一键完整清洗 (默认)")

    # 可选规则开关
    parser.add_argument("--no-duplicates", action="store_true", help="关闭去重")
    parser.add_argument("--missing-numeric", choices=["mean", "median", "ffill", "bfill", "drop"], default="mean", help="数值列缺失值策略")
    parser.add_argument("--missing-text", choices=["mode", "ffill", "bfill", "drop"], default="mode", help="文本列缺失值策略")
    parser.add_argument("--no-outliers", action="store_true", help="关闭异常值检测")
    parser.add_argument("--outlier-method", choices=["iqr", "zscore"], default="iqr", help="异常值检测方法")
    parser.add_argument("--outlier-threshold", type=float, default=1.5, help="异常值阈值")
    parser.add_argument("--no-range-check", action="store_true", help="关闭范围校验")
    parser.add_argument("--no-email-check", action="store_true", help="关闭邮箱校验")
    parser.add_argument("--no-category-unify", action="store_true", help="关闭分类值统一")
    parser.add_argument("--date-format", default="%Y-%m-%d", help="日期输出格式")

    # 合并/拆分
    parser.add_argument("--merge", nargs="+", help="合并多个文件")
    parser.add_argument("--split-by", help="按列拆分表格")
    parser.add_argument("--split-chunks", type=int, help="按行数拆分表格")

    # 报告
    parser.add_argument("--report", help="生成清洗报告到指定路径")

    args = parser.parse_args()

    if args.merge:
        print("正在合并表格...")
        merged = TableMergerSplitter.merge_from_files([args.input] + args.merge)
        output = args.output or "merged_output.csv"
        save_file(merged, output)
        print(f"合并完成，已保存至: {output}")
        return

    df = load_file(args.input)
    original_df = df.copy()

    config = {
        "remove_duplicates": not args.no_duplicates,
        "missing_strategy": {"numeric": args.missing_numeric, "text": args.missing_text},
        "outlier_method": args.outlier_method,
        "outlier_threshold": args.outlier_threshold,
        "date_format": args.date_format,
        "validate_email": not args.no_email_check,
        "remove_city_suffix": not args.no_category_unify,
    }

    if args.no_range_check:
        config["range_rules"] = {}

    cleaner = TableCleaner(df, config=config)

    print(f"加载文件: {args.input}")
    print(f"原始数据: {df.shape[0]} 行 x {df.shape[1]} 列")
    print(f"缺失值: {df.isnull().sum().sum()} | 重复行: {df.duplicated().sum()}")

    print("\n开始清洗...")
    cleaner.auto_clean()

    cleaned_df = cleaner.get_df()
    print(f"\n清洗完成: {cleaned_df.shape[0]} 行 x {cleaned_df.shape[1]} 列")

    if args.output:
        save_file(cleaned_df, args.output)
        print(f"已保存至: {args.output}")

    if args.report:
        print(f"\n生成报告: {args.report}")
        ReportGenerator.generate_report(original_df, cleaned_df, cleaner.cleaning_log, args.report)

    if args.split_by:
        print(f"\n按列 '{args.split_by}' 拆分...")
        tables = TableMergerSplitter.split_by_column(cleaned_df, args.split_by)
        output_dir = args.output.rsplit(".", 1)[0] if args.output else "split_output"
        TableMergerSplitter.export_tables(tables, output_dir)
        print(f"拆分为 {len(tables)} 个文件 -> {output_dir}/")

    if args.split_chunks:
        print(f"\n按 {args.split_chunks} 行拆分...")
        tables = TableMergerSplitter.split_by_rows(cleaned_df, args.split_chunks)
        output_dir = args.output.rsplit(".", 1)[0] if args.output else "chunk_output"
        TableMergerSplitter.export_tables({f"chunk_{i}": t for i, t in enumerate(tables)}, output_dir)
        print(f"拆分为 {len(tables)} 个文件 -> {output_dir}/")


if __name__ == "__main__":
    main()
