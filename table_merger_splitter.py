import pandas as pd
import os
from typing import List, Optional, Dict, Union


class TableMergerSplitter:
    """表格合并与拆分类"""

    @staticmethod
    def merge_tables(
        tables: List[pd.DataFrame],
        how: str = "inner",
        on: Optional[Union[str, List[str]]] = None,
        axis: int = 0
    ) -> pd.DataFrame:
        """合并多个表格"""
        if axis == 0:
            result = pd.concat(tables, ignore_index=True)
        else:
            if on:
                result = tables[0]
                for table in tables[1:]:
                    result = pd.merge(result, table, on=on, how=how)
            else:
                result = pd.concat(tables, axis=1, ignore_index=True)
        return result

    @staticmethod
    def merge_from_files(
        file_paths: List[str],
        how: str = "inner",
        on: Optional[Union[str, List[str]]] = None,
        axis: int = 0
    ) -> pd.DataFrame:
        """从文件合并表格"""
        tables = []
        for path in file_paths:
            if path.endswith(".csv"):
                tables.append(pd.read_csv(path))
            elif path.endswith((".xlsx", ".xls")):
                tables.append(pd.read_excel(path))
            else:
                raise ValueError(f"不支持的文件格式: {path}")
        return TableMergerSplitter.merge_tables(tables, how, on, axis)

    @staticmethod
    def split_by_column(df: pd.DataFrame, column: str) -> Dict[str, pd.DataFrame]:
        """按列值拆分表格"""
        if column not in df.columns:
            raise ValueError(f"列 '{column}' 不存在")

        groups = df.groupby(column)
        return {str(name): group.reset_index(drop=True) for name, group in groups}

    @staticmethod
    def split_by_rows(df: pd.DataFrame, chunk_size: int) -> List[pd.DataFrame]:
        """按行数拆分表格"""
        return [df[i:i + chunk_size].reset_index(drop=True) for i in range(0, len(df), chunk_size)]

    @staticmethod
    def split_by_condition(df: pd.DataFrame, conditions: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """按条件拆分表格"""
        result = {}
        for name, condition in conditions.items():
            try:
                result[name] = df.query(condition).reset_index(drop=True)
            except Exception as e:
                print(f"条件 '{name}' 解析失败: {e}")
        return result

    @staticmethod
    def export_tables(
        tables: Dict[str, pd.DataFrame],
        output_dir: str,
        format: str = "csv"
    ):
        """导出多个表格到文件"""
        os.makedirs(output_dir, exist_ok=True)
        for name, df in tables.items():
            if format == "csv":
                df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False, encoding="utf-8-sig")
            elif format == "excel":
                df.to_excel(os.path.join(output_dir, f"{name}.xlsx"), index=False)
