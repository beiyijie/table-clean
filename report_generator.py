import pandas as pd
import os
from datetime import datetime
from typing import Dict, Optional


class ReportGenerator:
    """清洗报告生成器"""

    @staticmethod
    def generate_report(
        original_df: pd.DataFrame,
        cleaned_df: pd.DataFrame,
        cleaning_log: list,
        output_path: Optional[str] = None
    ) -> str:
        """生成清洗报告"""
        report = []
        report.append("=" * 60)
        report.append("表格清洗报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")

        report.append("【数据概览】")
        report.append(f"原始数据: {original_df.shape[0]} 行 × {original_df.shape[1]} 列")
        report.append(f"清洗后数据: {cleaned_df.shape[0]} 行 × {cleaned_df.shape[1]} 列")
        report.append(f"删除行数: {original_df.shape[0] - cleaned_df.shape[0]}")
        report.append(f"删除列数: {original_df.shape[1] - cleaned_df.shape[1]}")
        report.append("")

        report.append("【缺失值统计】")
        report.append(f"原始缺失值总数: {original_df.isnull().sum().sum()}")
        report.append(f"清洗后缺失值总数: {cleaned_df.isnull().sum().sum()}")
        report.append("")

        report.append("【重复值统计】")
        report.append(f"原始重复行数: {original_df.duplicated().sum()}")
        report.append(f"清洗后重复行数: {cleaned_df.duplicated().sum()}")
        report.append("")

        report.append("【数据类型分布】")
        report.append("原始数据:")
        report.append(original_df.dtypes.value_counts().to_string())
        report.append("\n清洗后数据:")
        report.append(cleaned_df.dtypes.value_counts().to_string())
        report.append("")

        report.append("【清洗操作记录】")
        for i, log in enumerate(cleaning_log, 1):
            report.append(f"{i}. [{log['action']}] {log['details']}")
        report.append("")

        report.append("【列信息对比】")
        report.append(f"{'列名':<30} {'原始类型':<15} {'清洗后类型':<15}")
        report.append("-" * 60)
        all_columns = set(original_df.columns) | set(cleaned_df.columns)
        for col in sorted(all_columns):
            orig_type = str(original_df[col].dtype) if col in original_df.columns else "已删除"
            clean_type = str(cleaned_df[col].dtype) if col in cleaned_df.columns else "新增"
            report.append(f"{col:<30} {orig_type:<15} {clean_type:<15}")
        report.append("")

        report.append("=" * 60)
        report.append("报告结束")
        report.append("=" * 60)

        report_text = "\n".join(report)

        if output_path:
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"报告已保存至: {output_path}")

        return report_text

    @staticmethod
    def generate_csv_report(
        original_df: pd.DataFrame,
        cleaned_df: pd.DataFrame,
        output_path: str
    ):
        """生成CSV格式的统计报告"""
        stats = {
            "指标": [
                "原始行数",
                "清洗后行数",
                "删除行数",
                "原始列数",
                "清洗后列数",
                "原始缺失值",
                "清洗后缺失值",
                "原始重复行",
                "清洗后重复行"
            ],
            "值": [
                original_df.shape[0],
                cleaned_df.shape[0],
                original_df.shape[0] - cleaned_df.shape[0],
                original_df.shape[1],
                cleaned_df.shape[1],
                original_df.isnull().sum().sum(),
                cleaned_df.isnull().sum().sum(),
                original_df.duplicated().sum(),
                cleaned_df.duplicated().sum()
            ]
        }
        pd.DataFrame(stats).to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"CSV报告已保存至: {output_path}")
