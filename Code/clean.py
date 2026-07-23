import pandas as pd
import numpy as np


def remove_missing_values(df: pd.DataFrame, column_index: int) -> pd.DataFrame:
    """Remove rows with missing values from a specific column."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    return df.dropna(subset=[df.columns[column_index]])

def fill_missing_values_mean(df: pd.DataFrame, column_index: int) -> pd.DataFrame:
    """Fill missing values in a specific column with the mean of that column."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    mean_value = df.iloc[:, column_index].mean()
    df.iloc[:, column_index] = df.iloc[:, column_index].fillna(mean_value)
    
    return df

def fill_missing_values_median(df: pd.DataFrame, column_index: int) -> pd.DataFrame:
    """Fill missing values in a specific column with the median of that column."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    median_value = df.iloc[:, column_index].median()
    df.iloc[:, column_index] = df.iloc[:, column_index].fillna(median_value)
    
    return df

def fill_missing_values_mode(df: pd.DataFrame, column_index: int) -> pd.DataFrame:
    """Fill missing values in a specific column with the mode of that column."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    mode_value = df.iloc[:, column_index].mode()[0]
    df.iloc[:, column_index] = df.iloc[:, column_index].fillna(mode_value)
    
    return df

def fill_missing_values_interpolation(df: pd.DataFrame, column_index: int) -> pd.DataFrame:
    """Fill missing values in a specific column using linear interpolation."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    df.iloc[:, column_index] = df.iloc[:, column_index].interpolate(method='linear')
    
    return df

def fill_missing_values_specific_value(df: pd.DataFrame, column_index: int, value) -> pd.DataFrame:
    """Fill missing values in a specific column with a specific value."""
    
    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError("column_index is out of range")
    
    df.iloc[:, column_index] = df.iloc[:, column_index].fillna(value)
    
    return df