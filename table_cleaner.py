import pandas as pd
import numpy as np
import re
from typing import Optional, Union, List, Dict, Tuple


class TableCleaner:
    """表格清洗核心类 - 强制规则 + 可配置选项"""

    DEFAULT_CONFIG = {
        "remove_duplicates": True,
        "duplicate_subset": None,
        "missing_strategy": {"numeric": "mean", "text": "mode"},
        "outlier_method": "iqr",
        "outlier_threshold": 1.5,
        "range_rules": {
            "age": (0, 150),
            "salary": (0, None),
            "score": (0, 100),
            "performance_score": (0, 100),
        },
        "date_format": "%Y-%m-%d",
        "auto_detect_dates": True,
        "category_mapping": {},
        "remove_city_suffix": True,
        "validate_email": True,
        "email_columns": ["email"],
    }

    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        self.df = df.copy()
        self.cleaning_log = []
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

    def _log(self, action: str, details: str):
        self.cleaning_log.append({"action": action, "details": details})

    def config(self, **kwargs):
        """自定义配置"""
        self.config.update(kwargs)
        return self

    # ============================================================
    # 强制规则（不可跳过）
    # ============================================================

    def _remove_empty_rows_cols(self) -> pd.DataFrame:
        """清理全空行和全空列"""
        before_rows, before_cols = len(self.df), len(self.df.columns)
        self.df = self.df.dropna(how="all")
        self.df = self.df.dropna(axis=1, how="all")
        after_rows, after_cols = len(self.df), len(self.df.columns)
        self._log("remove_empty", f"删除 {before_rows - after_rows} 空行, {before_cols - after_cols} 空列")
        return self.df

    def _empty_strings_to_nan(self) -> pd.DataFrame:
        """空字符串/纯空格转为 NaN"""
        before = self.df.isnull().sum().sum()
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                self.df[col] = self.df[col].replace(r"^\s*$", np.nan, regex=True)
        after = self.df.isnull().sum().sum()
        self._log("empty_to_nan", f"转换 {after - before} 个空字符串为 NaN")
        return self.df

    def _clean_column_names(self) -> pd.DataFrame:
        """列名规范化"""
        new_columns = []
        for col in self.df.columns:
            col = str(col)
            col = col.lower()
            col = col.replace(" ", "_").replace("\t", "_")
            col = "".join(c for c in col if c.isalnum() or c == "_")
            col = re.sub(r"_+", "_", col).strip("_")
            new_columns.append(col)
        self.df.columns = new_columns
        self._log("clean_column_names", f"规范化 {len(new_columns)} 个列名")
        return self.df

    def _remove_invisible_chars(self) -> pd.DataFrame:
        """去除不可见字符"""
        count = 0
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                before = self.df[col].copy()
                self.df[col] = self.df[col].str.replace(r"[\t\n\r\x00-\x1f\u200b-\u200d\ufeff]", "", regex=True)
                count += (before != self.df[col]).sum()
        self._log("remove_invisible_chars", f"清理 {count} 个含不可见字符的单元格")
        return self.df

    def _strip_text_columns(self) -> pd.DataFrame:
        """文本列去首尾空格"""
        count = 0
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                before = self.df[col].copy()
                self.df[col] = self.df[col].str.strip()
                count += (before != self.df[col]).sum()
        self._log("strip_text", f"去除 {count} 个单元格首尾空格")
        return self.df

    def _fullwidth_to_halfwidth(self) -> pd.DataFrame:
        """全角转半角"""
        count = 0
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                before = self.df[col].copy()

                def convert(s):
                    if not isinstance(s, str):
                        return s
                    result = []
                    for char in s:
                        code = ord(char)
                        if code == 0x3000:
                            result.append(" ")
                        elif 0xFF01 <= code <= 0xFF5E:
                            result.append(chr(code - 0xFEE0))
                        else:
                            result.append(char)
                    return "".join(result)

                self.df[col] = self.df[col].apply(convert)
                count += (before != self.df[col]).sum()
        self._log("fullwidth_to_halfwidth", f"转换 {count} 个全角字符为半角")
        return self.df

    def _collapse_spaces(self) -> pd.DataFrame:
        """合并连续空格为一个"""
        count = 0
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                before = self.df[col].copy()
                self.df[col] = self.df[col].str.replace(r"\s+", " ", regex=True)
                count += (before != self.df[col]).sum()
        self._log("collapse_spaces", f"合并 {count} 个单元格的连续空格")
        return self.df

    def apply_basic_rules(self) -> pd.DataFrame:
        """执行所有强制规则"""
        self._remove_empty_rows_cols()
        self._empty_strings_to_nan()
        self._clean_column_names()
        self._remove_invisible_chars()
        self._strip_text_columns()
        self._fullwidth_to_halfwidth()
        self._collapse_spaces()
        return self.df

    # ============================================================
    # 可选规则（可配置）
    # ============================================================

    def remove_duplicates(self) -> pd.DataFrame:
        """去除重复行"""
        if not self.config.get("remove_duplicates", True):
            return self.df
        subset = self.config.get("duplicate_subset")
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep="first")
        after = len(self.df)
        self._log("remove_duplicates", f"删除 {before - after} 行重复数据")
        return self.df

    def handle_missing_values(self) -> pd.DataFrame:
        """智能填充缺失值"""
        strategy = self.config.get("missing_strategy", {"numeric": "mean", "text": "mode"})
        before = self.df.isnull().sum().sum()

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        text_cols = self.df.select_dtypes(include=["object", "string"]).columns

        numeric_strategy = strategy.get("numeric", "mean")
        text_strategy = strategy.get("text", "mode")

        if numeric_cols.any():
            if numeric_strategy == "mean":
                self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].mean())
            elif numeric_strategy == "median":
                self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].median())
            elif numeric_strategy == "ffill":
                self.df[numeric_cols] = self.df[numeric_cols].ffill()
            elif numeric_strategy == "bfill":
                self.df[numeric_cols] = self.df[numeric_cols].bfill()
            elif numeric_strategy == "drop":
                self.df = self.df.dropna(subset=numeric_cols)

        if len(text_cols) > 0:
            if text_strategy == "mode":
                for col in text_cols:
                    mode_val = self.df[col].mode()
                    if len(mode_val) > 0:
                        self.df[col] = self.df[col].fillna(mode_val[0])
            elif text_strategy == "ffill":
                self.df[text_cols] = self.df[text_cols].ffill()
            elif text_strategy == "bfill":
                self.df[text_cols] = self.df[text_cols].bfill()
            elif text_strategy == "drop":
                self.df = self.df.dropna(subset=text_cols)

        after = self.df.isnull().sum().sum()
        self._log("handle_missing_values", f"处理 {before - after} 个缺失值 (数值={numeric_strategy}, 文本={text_strategy})")
        return self.df

    def detect_outliers(self) -> Dict[str, List[int]]:
        """异常值检测"""
        method = self.config.get("outlier_method", "iqr")
        threshold = self.config.get("outlier_threshold", 1.5)
        target_cols = self.df.select_dtypes(include=[np.number]).columns
        outliers = {}

        for col in target_cols:
            if col not in self.df.columns:
                continue
            if method == "iqr":
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                mask = (self.df[col] < (Q1 - threshold * IQR)) | (self.df[col] > (Q3 + threshold * IQR))
            elif method == "zscore":
                z = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                mask = z > threshold
            else:
                continue
            indices = self.df[mask].index.tolist()
            if indices:
                outliers[col] = indices

        self._log("detect_outliers", f"检测到 {sum(len(v) for v in outliers.values())} 个异常值 ({method})")
        return outliers

    def remove_outliers(self) -> pd.DataFrame:
        """移除异常值"""
        before = len(self.df)
        outliers = self.detect_outliers()
        if outliers:
            all_idx = set()
            for indices in outliers.values():
                all_idx.update(indices)
            self.df = self.df.drop(list(all_idx))
        after = len(self.df)
        self._log("remove_outliers", f"删除 {before - after} 行异常数据")
        return self.df

    def validate_ranges(self) -> pd.DataFrame:
        """范围校验"""
        range_rules = self.config.get("range_rules", {})
        removed = 0

        for col_name, (min_val, max_val) in range_rules.items():
            matching_cols = [c for c in self.df.columns if col_name in c.lower()]
            for col in matching_cols:
                if col not in self.df.select_dtypes(include=[np.number]).columns:
                    continue
                mask = pd.Series(True, index=self.df.index)
                if min_val is not None:
                    mask &= self.df[col] >= min_val
                if max_val is not None:
                    mask &= self.df[col] <= max_val
                invalid = (~mask).sum()
                if invalid > 0:
                    self.df = self.df[mask]
                    removed += invalid
                    self._log("validate_range", f"列 {col}: 删除 {invalid} 行超出范围 [{min_val}, {max_val}]")

        if removed == 0:
            self._log("validate_range", "无超出范围的数据")
        return self.df

    def standardize_dates(self) -> pd.DataFrame:
        """日期标准化"""
        date_format = self.config.get("date_format", "%Y-%m-%d")
        auto_detect = self.config.get("auto_detect_dates", True)

        date_cols = []
        if auto_detect:
            for col in self.df.columns:
                if any(kw in col.lower() for kw in ["date", "time", "日期", "时间"]):
                    date_cols.append(col)

        if not date_cols:
            self._log("standardize_dates", "未检测到日期列")
            return self.df

        for col in date_cols:
            try:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce").dt.strftime(date_format)
            except Exception:
                pass

        self._log("standardize_dates", f"标准化 {len(date_cols)} 个日期列为 {date_format}")
        return self.df

    def unify_categories(self) -> pd.DataFrame:
        """分类值统一"""
        custom_mapping = self.config.get("category_mapping", {})
        remove_suffix = self.config.get("remove_city_suffix", True)
        total_changes = 0

        for col in self.df.columns:
            if self.df[col].dtype != "object":
                continue

            if col in custom_mapping:
                mapping = custom_mapping[col]
                before = self.df[col].copy()
                self.df[col] = self.df[col].replace(mapping)
                total_changes += (before != self.df[col]).sum()

            if remove_suffix and any(kw in col.lower() for kw in ["city", "city_name", "城市"]):
                before = self.df[col].copy()
                self.df[col] = self.df[col].str.replace(r"(市|省|自治区|特别行政区|省辖市)$", "", regex=True)
                total_changes += (before != self.df[col]).sum()

        self._log("unify_categories", f"统一 {total_changes} 个分类值")
        return self.df

    def validate_emails(self) -> pd.DataFrame:
        """邮箱格式校验"""
        if not self.config.get("validate_email", True):
            return self.df

        email_cols = self.config.get("email_columns", ["email"])
        matching_cols = []
        for pattern in email_cols:
            matching_cols.extend([c for c in self.df.columns if pattern in c.lower()])

        if not matching_cols:
            self._log("validate_email", "未检测到邮箱列")
            return self.df

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        invalid_count = 0

        for col in matching_cols:
            mask = self.df[col].str.match(email_pattern, na=True)
            invalid = (~mask).sum()
            invalid_count += invalid
            if invalid > 0:
                self.df = self.df[mask]
                self._log("validate_email", f"列 {col}: 删除 {invalid} 行无效邮箱")

        if invalid_count == 0:
            self._log("validate_email", "无无效邮箱格式")
        return self.df

    # ============================================================
    # 一键清洗
    # ============================================================

    def auto_clean(self) -> pd.DataFrame:
        """一键完整清洗：强制规则 + 所有可选规则"""
        self.apply_basic_rules()
        self.remove_duplicates()
        self.validate_ranges()
        self.remove_outliers()
        self.handle_missing_values()
        self.standardize_dates()
        self.unify_categories()
        self.validate_emails()
        return self.df

    def run(self) -> pd.DataFrame:
        """执行清洗（同 auto_clean）"""
        return self.auto_clean()

    def get_df(self) -> pd.DataFrame:
        return self.df

    def get_cleaning_report(self) -> Dict:
        return {
            "current_shape": self.df.shape,
            "missing_values": self.df.isnull().sum().to_dict(),
            "duplicates": self.df.duplicated().sum(),
            "dtypes": self.df.dtypes.to_dict(),
            "cleaning_log": self.cleaning_log,
        }
