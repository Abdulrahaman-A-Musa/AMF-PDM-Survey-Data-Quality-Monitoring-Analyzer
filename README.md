# AMF-PDM-Survey-Data-Quality-Monitoring-Analyzer
The EHA-(AMF-PDM) Survey Data Quality Monitoring Analyzer is a Shiny web application an automated tool for performing similarity checks on AMF project data, thereby ensuring a data quality threshold of no less than 96% is achieved. This tool offers a comprehensive set of features for managing survey team deployment, comparing datasets, cleaning and analyzing data, and generating pivot tables and frequency analyses. It's particularly tailored for applications. 
## Features
This application is divided into four main modules, each accessible through a tabbed interface:
1. **Team Deployment**: 
    *   **File Upload:** Upload Excel files containing survey area details (LGA, Ward, Village, etc.).
    *   **Configuration:** Define parameters for team deployment, including:
        *   Supervisors per LGA
        *   Enumerators per Supervisor
        *   Villages to be covered per Day
        *   Survey duration
        *   Households per Village
    *   **Summary Statistics:** View overall metrics such as total villages, days needed for coverage, and total households.
    *   **Daily Schedule:** Generate a detailed daily schedule assigning supervisors and enumerators to villages and wards. It also factors in revisits.
    *   **Map Visualization:** Display survey locations on an interactive map with various layers (satellite imagery, roads, place labels) and features (location finder, measure tool).
    * **Raw Data**: view the uploaded raw data.
      ![image](https://github.com/user-attachments/assets/2231e198-225d-4d52-bd64-97e4e6dee46d)


2. **Data Comparison:**
    *   **File Upload:** Upload two Excel files for comparison: the main data and the revisit data.
    *   **LGA Filter:** Filter data by specific Local Government Areas (LGAs).
    *   **Similarity Score:** Calculate and display overall and variable-specific similarity scores between the two datasets for a selected set of columns, showing perfect matches and percentages.
    *   **Detailed Comparison:** Generate a table for detailed comparisons between the two datasets.
      ![image](https://github.com/user-attachments/assets/d800564e-d8e8-4559-8df3-d84ac6f96c5a)


3. **Data Cleaning and Coverage Analysis:**
    *   **File Upload:** Upload an Excel file for data cleaning.
    *   **LGA Filter:** Filter data by specific Local Government Areas (LGAs).
    *   **Duplicate Detection:** Identify and highlight duplicate entries based on unique household IDs.
    *   **Coverage Analysis:** Display statistics such as total submissions, valid submissions, and duplicate counts.
    *   **Cleaned Data Table:** View the data, with options to show all or only duplicate records.
    * **Show all**: option to show all data or just filter data.

4. **Pivot Table Analysis:**
    *   **Pivot Table Generator:** Create pivot tables with customizable rows, columns, values, and aggregation functions.
    *   **Frequency Analysis:** Conduct frequency analyses on selected categorical variables.
        *   **Frequency Table:** Generate a table showing frequencies and percentages.
        *   **Visualizations:** Create bar charts and pie charts to visualize the frequency data.
          ![image](https://github.com/user-attachments/assets/ddac1b0b-52ac-47cb-a913-acd72c53ad60)


## Setup and Installation
### Prerequisites
*   **Python 3.8+**
*   **pip** (Python package installer)
the project.
6. **Run the Application:**
    shiny run app.py
## Usage
1. **Navigation:** Use the tabs at the top to switch between different modules of the application.
2. **File Upload:**
    *   Click on the "Browse" button or drag and drop the Excel file.
    *   The application will validate the required columns.
3. **Configuration:**
    *   Adjust parameters (supervisors, enumerators, villages, etc.) using the input fields.
4. **Filtering:**
    *   Select LGAs or other available filters to narrow down the data.
5. **Data Views:**
    *   Switch between different views using the sub-tabs (e.g., "Team Assignments," "Map," "Raw Data").
    *   Interact with the data tables and maps as needed.
6. **Generating Reports:**
    *   Use the "copy", "csv", "excel" and "print" buttons in the tables to export the data or tables.
7. **Data comparison:**
    * Upload your main data and revisit data.
    * Select LGA filter
    *Observe the result in the table and summary statistics

8. **Data Cleaning**:
    * Upload your data
    * Select all the check boxes and LGA filter to view data
    * You can filter for duplicate by using show duplicate check box.
9. **Pivot table and Frequency**:
    * Navigate to the tab
    * Select the desired parameters and generate your desired table.
    * Select the variable and chart type you want and generate the table and chart

App-Link(https://eha-full-stack-data-analytics.shinyapps.io/amf_pdm/)


