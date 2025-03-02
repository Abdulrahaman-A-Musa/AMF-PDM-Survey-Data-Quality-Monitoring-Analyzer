from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np


def my_css():
    return ui.tags.style("""
        /* Overall app background and text styling */
        body {
            background-color: white;
            color: #333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Header styling */
        .app-header {
            background-color: #2ec6f8;
            color: white;
            padding: 5px;
            margin-bottom: 5px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Card styling */
        .card {
            background-color: white;
            border: none;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        .card-header {
            background-color: #2ec6f8;
            color: white;
            border-radius: 8px 8px 0 0 !important;
            padding: 15px 20px;
        }

        /* Sidebar styling */
        .sidebar {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            padding: 20px;
        }

        /* Tab styling */
        .nav-tabs .nav-link {
            color: #2c3e50;
        }

        .nav-tabs .nav-link.active {
            color: #2ec6f8;
            border-bottom: 2px solid #2980b9;
        }

        /* Accordion styling */
        .accordion-button {
            background-color: #2ec6f8;
            color: white;
        }

        .accordion-button:not(.collapsed) {
            background-color: #2ec6f8;
            color: white;
        }

        /* Table styling */
        .dataTable {
            background-color: white;
            border-radius: 8px;
        }

        /* Button styling */
        .btn-primary {
            background-color: #2980b9;
            border-color: #2980b9;
        }

        .btn-primary:hover {
            background-color: #2c3e50;
            border-color: #2c3e50;
        }
    """)


def optimize_df(df):
    """Optimize dataframe memory usage"""
    for col in df.columns:
        # Optimize integers
        if df[col].dtype == 'int64':
            if df[col].min() > np.iinfo(np.int32).min and df[col].max() < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        # Optimize floats
        elif df[col].dtype == 'float64':
            df[col] = df[col].astype(np.float32)
        # Optimize strings
        elif df[col].dtype == 'object':
            if df[col].nunique() / len(df[col]) < 0.5:  # If less than 50% unique values
                df[col] = df[col].astype('category')
    
    return df

