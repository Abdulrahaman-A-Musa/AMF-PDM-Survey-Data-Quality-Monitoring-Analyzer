from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np
from itables.shiny import DT
import matplotlib.pyplot as plt
import gc  # For garbage collection
import folium
from folium import plugins
import numpy as np
import base64
from shiny.types import NavSetArg
from io import BytesIO
from datetime import datetime, timedelta
import string
import math
from utility.helper import my_css, optimize_df



app_ui = ui.page_fluid(
    # Custom CSS for the app
    my_css(),
    # App Header
    ui.div(
        ui.h1("EHA-(AMF-PDM) Survey Data Quality Monitoring Analyser", class_="text-center"),
        ui.p(
            "Comprehensive tool for data quality assessment, monitoring, and analysis",
            class_="text-center text-muted"
        ),
        class_="app-header"
    ),

ui.navset_tab(
#===========================Deployement Tab=====================================
  ui.nav_panel("Team Deployment",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_file("file", "Upload Excel File", accept=[".xlsx", ".xls"]),
                ui.input_select(
                    "selected_lga",
                    "Select LGA",
                    choices=[]
                ),
                ui.input_numeric("sup_per_lga", "Supervisors per LGA", value=2, min=1),
                ui.input_numeric("enum_per_sup", "Enumerators per Supervisor", value=4, min=1),
                ui.input_numeric("villages_per_day", "Villages per Day", value=4, min=1),
                ui.input_numeric("survey_days", "Survey Duration (Days)", value=20, min=1),
                ui.input_numeric("households_per_village", "Households per Village", value=20, min=1),
                ui.hr(),
                width="300px"
            ),
            ui.navset_tab(
                ui.nav_panel("Team Assignments",
                    ui.card(
                        ui.card_header("Summary Statistics"),
                        ui.output_code("summary_stats")
                    ),
                    ui.card(
                        ui.card_header("Daily Team Deployment Schedule"),
                        ui.output_data_frame("daily_schedule")
                    )
                ),
                ui.nav_panel("Map",
                    ui.output_ui("map_output")
                ),
                ui.nav_panel("Raw Data",
                    ui.card(
                        ui.card_header("Uploaded Data"),
                        ui.output_data_frame("raw_data")
                    )
                )
            )
        )
    ),
      
        ui.nav_panel("Data Comparison",
            ui.page_sidebar(
                ui.sidebar(
                    ui.h4("File Upload"),
                    ui.input_file("file1", "Upload Main Data", accept=[".xlsx", ".xls"]),
                    ui.input_file("file2", "Upload Revisit", accept=[".xlsx", ".xls"]),
                    ui.div(
                        ui.input_select(
                            "column",
                            "Filter LGA",
                            choices=[" "],
                            selectize=True
                        ),
                        ui.div(
                            ui.output_text("variable_help"),
                            class_="text-muted small mt-2"
                        ),
                        style="margin-bottom: 1rem;"
                    ),
                ),

                ui.card(
                    ui.card_header(ui.h3("Summary Statistics")),
                    ui.output_code("similarity_score"),
                    ui.output_text("match_counts"),
                    class_="mb-4"
                ),
                ui.card(
                    ui.card_header(
                        ui.div(
                            ui.h3("Detailed Comparison"),
                            ui.div(ui.output_text("comparison_title"), class_="text-muted"),
                        )
                    ),
                    ui.output_ui("similarity_table"),
                ),
            )
        ),
        
           # Second tab - Data Cleaning and Coverage Analysis
        ui.nav_panel("Data Cleaning and Coverage Analysis",
            ui.page_sidebar(
                ui.sidebar(
                    ui.h4("File Upload"),
                    ui.input_file("cleaning_file", "Upload Excel File", accept=[".xlsx", ".xls"]),
                    ui.input_checkbox("show_all", "Show All Data", value=True),
                    ui.input_select(
                        "lga_filter",
                        "Select LGA",
                        choices=[],
                        selectize=True
                    ),
                ),
                ui.card(
                    ui.card_header(ui.h3("Coverage Analysis")),
                    ui.output_text("total_submissions"),
                    ui.output_text("valid_submissions"),
                    ui.output_text("duplicate_count"),
                    class_="mb-4"
                ),
                ui.card(
                    ui.card_header(ui.h3("Cleaned Data")),
                    ui.input_checkbox("show_duplicates", "Show only duplicates", False),
                    ui.output_ui("cleaned_data_table"),
                ),
            )
        ),
        
        # Third tab - Pivot Table Analysis
        ui.nav_panel("Pivot Table Analysis",
            ui.accordion(
                ui.accordion_panel("Pivot Table Generator",
                    ui.page_sidebar(
                        ui.sidebar(
                            ui.h4("Pivot Table Settings"),
                            ui.input_select(
                                "pivot_index",
                                "Select Row (Index)",
                                choices=[],
                                selectize=True
                            ),
                            ui.input_select(
                                "pivot_columns",
                                "Select Column",
                                choices=[],
                                selectize=True
                            ),
                            ui.input_select(
                                "pivot_values",
                                "Select Values",
                                choices=[],
                                selectize=True
                            ),
                            ui.input_select(
                                "pivot_aggfunc",
                                "Select Aggregation",
                                choices=["count", "sum", "mean", "min", "max"],
                                selected="count"
                            ),
                        ),
                        ui.card(
                            ui.card_header(ui.h3("Pivot Table Results")),
                            ui.output_ui("pivot_table"),
                        ),
                    )
                ),
                ui.accordion_panel("Frequency Analysis",
                    ui.layout_sidebar(
                        ui.sidebar(
                            ui.input_select(
                                "freq_variable",
                                "Select Variable for Analysis",
                                choices=[],
                                selectize=True
                            ),
                            ui.input_checkbox_group(
                                "chart_types",
                                "Select Chart Types",
                                choices=["Bar Chart", "Pie Chart"],
                                selected=["Bar Chart"]
                            ),
                        ),
                        ui.card(
                            ui.card_header("Frequency Table"),
                            ui.output_ui("freq_table")
                        ),
                        ui.card(
                            ui.card_header("Visualizations"),
                            ui.output_plot("freq_plot")
                        )
                    )
                ),
            )
        )
    ),
        title="PDM-Analyser", 
        fillable_mobile=False, 
)

def server(input, output, session):
#===========================Deployement Tab=====================================
    data = reactive.value(None)
    lga_supervisor_mapping = reactive.value({})
    
    @reactive.effect
    @reactive.event(input.file)
    def _():
        if input.file() is not None:
            file_path = input.file()[0]["datapath"]
            df = pd.read_excel(file_path)
            
            required_cols = ['LGA', 'Ward', 'Distribution point', 'Village', 'REVISIT STATUS']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                ui.notification_show(
                    f"Missing columns: {', '.join(missing_cols)}", 
                    type="error"
                )
            else:
                df['REVISIT STATUS'] = df['REVISIT STATUS'].fillna('NO').astype(str)
                data.set(df)
                
                ui.update_select(
                    "selected_lga",
                    choices=sorted(df['LGA'].unique()),
                    selected=None
                )
                
                update_supervisor_mapping()
                ui.notification_show("Data loaded successfully!", type="message")

    @reactive.effect
    @reactive.event(input.sup_per_lga)
    def _():
        if data() is not None:
            update_supervisor_mapping()

    def update_supervisor_mapping():
        df = data()
        if df is None:
            return
            
        letters = list(string.ascii_uppercase)
        lga_names = sorted(df['LGA'].unique())
        mapping = {}
        
        # Start index for continuous supervisor numbering across LGAs
        current_sup_num = 1
        
        for lga in lga_names:
            sup_ids = []
            n_sups = input.sup_per_lga()
            for i in range(n_sups):
                letter = letters[(current_sup_num - 1) % len(letters)]
                sup_ids.append(f"{letter}{current_sup_num}")
                current_sup_num += 1
            mapping[lga] = sup_ids
        
        lga_supervisor_mapping.set(mapping)

    @reactive.calc
    def filtered_data():
        if data() is None:
            return None
        
        df = data()
        selected_lga = input.selected_lga()
        
        if selected_lga:
            return df[df['LGA'] == selected_lga]
        return df

    @output
    @render.code
    def summary_stats():
        if data() is None:
            return "Please upload data first"
        
        df = filtered_data()
        if df is None:
            return "Please upload data first"
            
        total_villages = len(df['Village'].unique())
        villages_per_day = input.villages_per_day()
        total_days_needed = math.ceil(total_villages / villages_per_day)
        total_households = total_villages * input.households_per_village()
        
        stats = f"""
        Summary Statistics:
        • Total Villages: {total_villages}
        • Villages per Day: {villages_per_day}
        • Days Needed to Cover All Villages: {total_days_needed}
        • Total Households to be Covered: {total_households:,}
        • Number of Teams: {input.sup_per_lga()}
        • Enumerators per Team: {input.enum_per_sup()}
        • Households per Village: {input.households_per_village()}
        """
        return stats

    @output
    @render.data_frame
    def raw_data():
        df = filtered_data()
        if df is None:
            return pd.DataFrame()
        return render.DataGrid(df)

    @output
    @render.data_frame
    def daily_schedule():
        if data() is None:
            return pd.DataFrame()
        
        df = data()
        selected_lga = input.selected_lga()
        
        mapping = lga_supervisor_mapping()
        daily_assignments = {}
        n_enum_per_sup = input.enum_per_sup()
        households_per_village = input.households_per_village()
        total_days = input.survey_days()
        
        start_date = datetime.now()
        
        if selected_lga:
            lga_data = {selected_lga: df[df['LGA'] == selected_lga]}
        else:
            lga_data = {lga: group for lga, group in df.groupby('LGA')}
        
        for lga_name, lga_group in lga_data.items():
            supervisor_ids = mapping.get(lga_name, [])
            if not supervisor_ids:
                continue
            
            # Group by ward
            ward_groups = dict(tuple(lga_group.groupby('Ward')))
            
            # Reset index for all ward groups
            for ward in ward_groups:
                ward_groups[ward] = ward_groups[ward].reset_index(drop=True)
            
            day_num = 1
            while day_num <= total_days and any(len(group) > 0 for group in ward_groups.values()):
                survey_date = (start_date + timedelta(days=day_num-1)).strftime('%Y-%m-%d')
                
                # Get available wards
                available_wards = [ward for ward, group in ward_groups.items() if len(group) > 0]
                if not available_wards:
                    break
                
                # Assign wards and villages to supervisors
                for sup_id in supervisor_ids:
                    # Find a ward with at least 4 villages for this supervisor
                    assigned_ward = None
                    for ward in available_wards:
                        if len(ward_groups[ward]) >= 4:
                            assigned_ward = ward
                            break
                    
                    if assigned_ward is None:
                        continue
                    
                    key = (survey_date, lga_name, sup_id)
                    if key not in daily_assignments:
                        daily_assignments[key] = {
                            'enumerators': [f"{sup_id}_{j+1}" for j in range(n_enum_per_sup)],
                            'wards': set(),
                            'villages': [],  # Changed to list to maintain order
                            'enum_assignments': {},  # Track which enumerator gets which village
                            'revisits': set(),
                            'total_households': 0
                        }
                    
                    # Take exactly 4 villages from the ward
                    ward_data = ward_groups[assigned_ward]
                    sup_villages = ward_data.iloc[:4]
                    ward_groups[assigned_ward] = ward_data.iloc[4:]
                    
                    daily_assignments[key]['wards'].add(assigned_ward)
                    
                    # Assign each village to an enumerator
                    for enum_idx, (_, row) in enumerate(sup_villages.iterrows()):
                        enum_id = daily_assignments[key]['enumerators'][enum_idx]
                        village_name = row['Village']
                        daily_assignments[key]['villages'].append(village_name)
                        daily_assignments[key]['enum_assignments'][village_name] = enum_id
                        daily_assignments[key]['total_households'] += households_per_village
                        
                        revisit_status = str(row['REVISIT STATUS']).strip().upper()
                        if revisit_status == 'YES':
                            revisit_date = (start_date + timedelta(days=day_num+1)).strftime('%Y-%m-%d')
                            daily_assignments[key]['revisits'].add(
                                f"{village_name} (Revisit: {revisit_date})"
                            )
                
                day_num += 1
        
        schedule_rows = []
        for (date, lga, sup_id), details in daily_assignments.items():
            if len(details['villages']) > 0:
                # Create village assignments string with enumerator information
                village_assignments = [
                    f"{village} ({details['enum_assignments'][village]})"
                    for village in details['villages']
                ]
                
                schedule_rows.append({
                    'Survey_Date': date,
                    'LGA': lga,
                    'Supervisor': sup_id,
                    'Ward': ', '.join(sorted(details['wards'])),
                    'Village_Assignments': ', '.join(village_assignments),
                    'Total_Households': details['total_households'],
                    'Revisits': ', '.join(sorted(details['revisits'])) if details['revisits'] else 'No revisits'
                })
        
        if not schedule_rows:
            return pd.DataFrame()
        
        schedule_df = pd.DataFrame(schedule_rows)
        schedule_df = schedule_df.sort_values(['Survey_Date', 'LGA', 'Supervisor'])
        return render.DataGrid(schedule_df)

    @output
    @render.ui
    @reactive.event(input.selected_lga, input.selected_ward)
    def map_output():
        if data() is None or not input.selected_lga():
            return ui.p("Please select an LGA to view the map")
        
        try:
            df = data()
            df = df[df['LGA'] == input.selected_lga()]
            if input.selected_ward():
                df = df[df['Ward'] == input.selected_ward()]
            
            if len(df) == 0:
                return ui.p("No data available for the selected area")
            
            # Create map centered on mean coordinates with high-resolution satellite imagery
            center_lat = df['GPS Latitude'].mean()
            center_lon = df['GPS Longitude'].mean()
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=18,  # Increased zoom level for even better detail
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google Satellite'
            )
            
            # Add OpenStreetMap road network layer
            folium.TileLayer(
                tiles='openstreetmap',
                name='Roads',
                overlay=True,
                opacity=0.5
            ).add_to(m)
            
            # Add a tile layer for place labels
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}',
                attr='Google Labels',
                name='Place Labels',
                overlay=True
            ).add_to(m)

            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='World Imagery'
            ).add_to(m)
            
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Place Labels',
                overlay=True
            ).add_to(m)

            point_group = folium.FeatureGroup(name="Households")
        
            for idx, row in df.iterrows():
                # Determine point color based on Revisit-Status
                point_color = 'red' if row['Revisit-Status'].lower() == 'yes' else 'blue'
                
                popup_text = f"""
                    <div style='min-width: 200px'>
                        <b>Village:</b> {row['Village']}<br>
                        <b>Ward:</b> {row['Ward']}<br>
                        <b>Household ID:</b> {row['HouseholdID']}<br>
                        <b>Head of Household:</b> {row['Name of Head of Household']}<br>
                        <b>Revisit Status:</b> {row['Revisit-Status']}<br>
                        <br>
                        <a href='https://www.google.com/maps/dir/?api=1&destination={row["GPS Latitude"]},{row["GPS Longitude"]}' 
                           target='_blank' 
                           style='background-color: #4CAF50; 
                                  color: white; 
                                  padding: 8px 15px; 
                                  text-decoration: none; 
                                  border-radius: 4px;
                                  display: inline-block;'>
                            Navigate to Household
                        </a>
                    </div>
                """
                
                # Create circle marker (point) with click functionality
                folium.CircleMarker(
                    location=[row['GPS Latitude'], row['GPS Longitude']],
                    radius=8,  # Size of the point
                    popup=folium.Popup(popup_text, max_width=300),
                    color=point_color,
                    fill=True,
                    fill_color=point_color,
                    fill_opacity=0.7,
                    weight=2,
                    opacity=0.8
                ).add_to(point_group)
            
            point_group.add_to(m)
            
            # Add cluster markers for overview
            marker_cluster = plugins.MarkerCluster(name="Clustered View").add_to(m)
            for idx, row in df.iterrows():
                folium.CircleMarker(
                    [row['GPS Latitude'], row['GPS Longitude']],
                    radius=8,
                    color=point_color,
                    fill=True
                ).add_to(marker_cluster)
            
            # Add a legend
            legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; right: 50px; width: 150px; height: 90px; 
                            border:2px solid grey; z-index:9999; font-size:14px;
                            background-color: white;
                            padding: 10px;
                            border-radius: 5px;
                            ">
                    <p style="margin-bottom: 5px;"><b>Legend</b></p>
                    <p style="margin: 0;">
                        <span style="color: red;">●</span> Needs Revisit<br>
                        <span style="color: blue;">●</span> No Revisit Needed
                    </p>
                </div>
                '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Add layer control
            folium.LayerControl(position='topright').add_to(m)
            
            # Add fullscreen button
            plugins.Fullscreen().add_to(m)
            
            # Add location finder
            plugins.LocateControl(
                auto_start=False,
                position='topright',
                strings={'title': 'Show my location'},
                locateOptions={'enableHighAccuracy': True}
            ).add_to(m)
            
            # Add measure tool
            plugins.MeasureControl(
                position='topright',
                primary_length_unit='meters',
                secondary_length_unit='kilometers'
            ).add_to(m)
            
            # Save map to BytesIO object
            bio = BytesIO()
            m.save(bio, close_file=False)
            map_html = bio.getvalue().decode()
            
            # Return the map in an iframe
            return ui.div(
                ui.tags.iframe(
                    srcDoc=map_html,
                    style="width: 100%; height: 600px; border: none;",
                    id="map-frame"
                )
            )
            
        except Exception as e:
            print(f"Error generating map: {str(e)}")
            return ui.p(f"Error generating map: {str(e)}")

#=========================endDeployment================================================

    df1 = reactive.value(None)
    df2 = reactive.value(None)
    cleaning_data = reactive.value(None)
    
    @reactive.effect
    def _():
        file1 = input.file1()
        if file1 is not None:
            try:
                df = pd.read_excel(
                    file1[0]['datapath'],
                    engine='openpyxl'
                )
                df = optimize_df(df)
                df1.set(df)
                gc.collect()
            except Exception as e:
                print(f"Error loading file1: {str(e)}")
    
    @reactive.effect
    def _():
        file2 = input.file2()
        if file2 is not None:
            try:
                df = pd.read_excel(
                    file2[0]['datapath'],
                    engine='openpyxl'
                )
                df = optimize_df(df)
                df2.set(df)
                gc.collect()
            except Exception as e:
                print(f"Error loading file2: {str(e)}")

    @reactive.effect
    def _():
        cleaning_file = input.cleaning_file()
        if cleaning_file is not None:
            try:
                # Read the Excel file
                df = pd.read_excel(
                    cleaning_file[0]['datapath'],
                    engine='openpyxl'
                )
                
                # Create Villagelist column if both required columns exist
                if 'calc_l4_name' in df.columns and 'calc_village_name' in df.columns:
                    l4_name = df['calc_l4_name'].astype(str).replace('nan', '')
                    village_name = df['calc_village_name'].astype(str).replace('nan', '')
                    df['Villagelist'] = l4_name + ' ' + village_name
                
                # Check if calc_household_id exists before trying to find duplicates
                if 'calc_household_id' in df.columns:
                    is_duplicate = df.duplicated(subset=['calc_household_id'], keep=False)
                    df['Duplicate_Status'] = is_duplicate.map({True: '⚠️ Duplicate', False: ''})
                    df = df.sort_values('calc_household_id')
                else:
                    df['Duplicate_Status'] = ''
                    is_duplicate = pd.Series([False] * len(df))
                
                # Reorder columns to put Duplicate_Status near the start
                cols = ['Duplicate_Status'] + [col for col in df.columns if col != 'Duplicate_Status']
                df = df[cols]
                
                # Optimize memory usage
                df = optimize_df(df)
                
                # Store both the display data and the duplicate status
                cleaning_data.set({'df': df, 'is_duplicate': is_duplicate})
                
                # Update LGA choices if the column exists
                if 'calc_l4_name' in df.columns:
                    lga_choices = sorted(df['calc_l4_name'].unique())
                    ui.update_select("lga_filter", choices=lga_choices)
                
                # Update pivot table choices
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                ui.update_select("pivot_index", choices=categorical_cols)
                ui.update_select("pivot_columns", choices=categorical_cols)
                ui.update_select("pivot_values", choices=numeric_cols)
                
                gc.collect()
                
            except Exception as e:
                print(f"Error loading file: {str(e)}")

    @reactive.calc
    def filtered_df():
        """Get the filtered dataframe based on LGA selection"""
        if cleaning_data() is None:
            return None
        
        df = cleaning_data()['df'].copy()
        if not input.show_all() and input.lga_filter() and input.lga_filter() != "":
            return df[df['calc_l4_name'] == input.lga_filter()]
        return df

    @reactive.calc
    def pivot_filtered_df():
        """Get filtered dataframe for pivot analysis with additional cleaning"""
        df = filtered_df()
        if df is None:
            return None
        
        try:
            # Filter based on the specified columns
            mask = (
                (df['HouseholdFound'].str.contains('yes', case=False, na=False)) &
                (
                    (df['FirstVisitPresent'].str.contains('yes', case=False, na=False)) |
                    (df['FirstVisitPresent'].str.contains('no_but_will_return', case=False, na=False))
                ) &
                (df['Consent'].str.contains('yes', case=False, na=False))
            )

            return df[mask]
        except Exception as e:
            print(f"Error filtering pivot data: {str(e)}")
            return df  # Return original dataframe if filtering fails

    @output
    @render.ui
    def cleaned_data_table():
        if cleaning_data() is None:
            return ui.p("Please upload a file to see the cleaned data.", class_="text-muted")
        
        try:
            df = filtered_df()
            is_duplicate = cleaning_data()['is_duplicate']
            
            # Apply show duplicates filter if enabled
            if input.show_duplicates():
                df = df[is_duplicate]
            
            if len(df) == 0:
                return ui.p("No data available for the selected filters.", class_="text-muted")
            
            # Limit the number of rows displayed if necessary
            if len(df) > 100000:
                df = df.head(100000)
                message = ui.p("⚠️ Showing first 100,000 rows for performance reasons.", class_="text-warning")
            else:
                message = ui.p("")
            
            # Create custom CSS for styling
            custom_css = """
            <style>
                .duplicate-row {
                    background-color: #ffebee !important;
                    color: #d32f2f !important;
                }
            </style>
            """
            
            return ui.div(
                ui.HTML(custom_css),
                message,
                ui.HTML(
                    DT(
                        df,
                        maxBytes=0,
                        layout={"top": "searchBuilder"}, 
                        keys=True,
                        classes="display nowrap compact",
                        buttons=["pageLength", "copyHtml5", "csvHtml5", "excelHtml5", 'print'],
                        options={
                            'pageLength': 25,
                            'deferRender': True,
                            'scroller': True,
                            'scrollY': '400px',
                            'createdRow': '''
                                function(row, data, dataIndex) {
                                    if (data['Duplicate_Status'] === '⚠️ Duplicate') {
                                        $(row).addClass('duplicate-row');
                                    }
                                }
                            '''
                        }
                    )
                )
            )
        except Exception as e:
            return ui.p(f"Error displaying data: {str(e)}", class_="text-danger")

    @output
    @render.text
    def total_submissions():
        if cleaning_data() is None:
            return "0"
        df = filtered_df()
        if df is not None:
            total = len(df)
            return f"📊 Total Submissions: {total:,}"
        return "0"

    @output
    @render.text
    def valid_submissions():
        if cleaning_data() is None:
            return "0"
        df = filtered_df()
        if df is not None:
            # Count distinct household IDs (counting one occurrence per household)
            valid = df['calc_household_id'].nunique()
            return f"✅ Valid Submissions: {valid:,}"
        return "0"

    @output
    @render.text
    def duplicate_count():
        if cleaning_data() is None:
            return "0"
        df = filtered_df()
        if df is not None:
            # Count records where household_id appears more than once
            duplicate_counts = df['calc_household_id'].value_counts()
            duplicates = duplicate_counts[duplicate_counts > 1].sum() - duplicate_counts[duplicate_counts > 1].size
            return f"🔄 Duplicate Submissions: {duplicates:,}"
        return "0"

    @render.ui
    def pivot_table():
        if cleaning_data() is None:
            return ui.p("Please upload a file to generate pivot table.", class_="text-muted")
        
        if not all([input.pivot_index(), input.pivot_columns(), input.pivot_values()]):
            return ui.p("Please select all pivot table parameters.", class_="text-muted")
        
        try:
            # df = pivot_filtered_df()
            df = cleaning_data()['df']
            if df is None or len(df) == 0:
                return ui.p("No data available after applying filters.", class_="text-muted")
            
            # Calculate total submissions (count all)
            total_submissions = df.groupby(input.pivot_index())[input.pivot_values()].count()
            
            # Calculate valid submissions (unique calc_household_id)
            valid_submissions = df.groupby(input.pivot_index())['calc_household_id'].nunique()
            
            # Combine into a single DataFrame
            pivot_df = pd.DataFrame({
                'Total Submissions': total_submissions,
                'Valid Submissions': valid_submissions
            }).reset_index()
            
            # Add total row
            total_row = pd.DataFrame({
                input.pivot_index(): ['Total'],
                'Total Submissions': [pivot_df['Total Submissions'].sum()],
                'Valid Submissions': [pivot_df['Valid Submissions'].sum()]
            })
            
            pivot_df = pd.concat([pivot_df, total_row], ignore_index=True)
            
            # Handle NaN values
            pivot_df = pivot_df.fillna(0)
            
            # Format numeric columns to avoid scientific notation
            numeric_cols = ['Total Submissions', 'Valid Submissions']
            for col in numeric_cols:
                pivot_df[col] = pivot_df[col].apply(lambda x: f"{x:,.0f}")
            
            # Optimize pivot table memory
            pivot_df = optimize_df(pivot_df)
            
            # Custom CSS for the table
            custom_css = """
            <style>
                .total-row {
                    background-color: #f5f5f5 !important;
                    font-weight: bold !important;
                }
                .total-submissions {
                    background-color: #e8f5e9 !important;
                }
                .valid-submissions {
                    background-color: #e3f2fd !important;
                }
            </style>
            """
            return ui.div(
                ui.HTML(custom_css),
                ui.HTML(
                    DT(
                        pivot_df,
                        maxBytes=0,
                        layout={"top": "searchBuilder"}, 
                        keys=True,
                        scrollCollapse=True,
                        scrollY= '200px',
                        paging=False, 
                        classes="display nowrap compact",
                        buttons=["pageLength", "copyHtml5", "csvHtml5", "excelHtml5", 'print'],
                        options={
                            'pageLength': 25,
                            'deferRender': True,
                            'scroller': True,
                            'scrollY': '400px',
                            'scrollX': True,  # Enable horizontal scrolling
                            'scrollCollapse': True,  # Enable scroll collapse
                            'fixedHeader': True,  # Keep headers visible while scrolling
                            'autoWidth': True,  # Automatically adjust column widths
                            'createdRow': '''
                                function(row, data, dataIndex) {
                                    if (data[0] === 'Total') {
                                        $(row).addClass('total-row');
                                    }
                                }
                            ''',
                            'columnDefs': [
                                {
                                    'targets': 1,
                                    'createdCell': '''
                                        function(td, cellData, rowData, row, col) {
                                            $(td).addClass('total-submissions');
                                        }
                                    '''
                                },
                                {
                                    'targets': 2,
                                    'createdCell': '''
                                        function(td, cellData, rowData, row, col) {
                                            $(td).addClass('valid-submissions');
                                        }
                                    '''
                                }
                            ]
                        }
                    )
                ),
            )
        except Exception as e:
            return ui.p(f"Error generating pivot table: {str(e)}", class_="text-muted")
#===================Frequencies Section
    @reactive.effect
    def _():
        """Update frequency analysis variable choices when data is loaded"""
        if cleaning_data() is None:
            return
        
        df = cleaning_data()['df']
        # Get categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        ui.update_select("freq_variable", choices=categorical_cols)

    @render.ui
    def freq_table():
        """Generate frequency table based on distinct household IDs"""
        if cleaning_data() is None:
            return ui.p("Please upload a file to generate frequency table.", class_="text-muted")
        
        if not input.freq_variable():
            return ui.p("Please select a variable for analysis.", class_="text-muted")
        
        try:
            df = filtered_df()
            if df is None or len(df) == 0:
                return ui.p("No data available after applying filters.", class_="text-muted")
            
            # Get distinct households
            distinct_df = df.drop_duplicates(subset=['calc_household_id'])
            
            # Calculate frequency table
            freq_df = distinct_df[input.freq_variable()].value_counts().reset_index()
            freq_df.columns = [input.freq_variable(), 'Frequency']
            
            # Calculate percentage
            total = freq_df['Frequency'].sum()
            freq_df['Percentage'] = (freq_df['Frequency'] / total * 100).round(2)
            
            # Format percentage
            freq_df['Percentage'] = freq_df['Percentage'].apply(lambda x: f"{x:.2f}%")
            
            # Add total row
            total_row = pd.DataFrame({
                input.freq_variable(): ['Total'],
                'Frequency': [total],
                'Percentage': ['100.00%']
            })
            
            freq_df = pd.concat([freq_df, total_row], ignore_index=True)
            
            # Custom CSS for styling
            custom_css = """
            <style>
                .total-row {
                    background-color: #f5f5f5 !important;
                    font-weight: bold !important;
                }
            </style>
            """
            
            return ui.div(
                ui.HTML(custom_css),
                ui.HTML(
                    DT(
                        freq_df,
                        maxBytes=0,
                        layout={"top": "searchBuilder"}, 
                        keys=True,
                        scrollCollapse=True,
                        scrollY= '200px',
                        paging=False,
                        classes="display compact",
                        options={
                            'pageLength': 25,
                            'deferRender': True,
                            'scroller': True,
                            'scrollY': '400px',
                            'scrollX': True,  # Enable horizontal scrolling
                            'scrollCollapse': True,  # Enable scroll collapse
                            'fixedHeader': True,  # Keep headers visible while scrolling
                            'autoWidth': True,  # Automatically adjust column widths
                            'createdRow': '''
                                function(row, data, dataIndex) {
                                    if (data[0] === 'Total') {
                                        $(row).addClass('total-row');
                                    }
                                }
                            '''
                        }
                    )
                )
            )
        except Exception as e:
            return ui.p(f"Error generating frequency table: {str(e)}", class_="text-muted")

    @render.plot
    def freq_plot():
        """Generate frequency plots based on distinct household IDs"""
        if cleaning_data() is None or not input.freq_variable() or not input.chart_types():
            return None
        
        try:
            df = filtered_df()
            if df is None or len(df) == 0:
                return None
            
            # Get distinct households
            distinct_df = df.drop_duplicates(subset=['calc_household_id'])
            
            # Calculate frequencies
            freq_series = distinct_df[input.freq_variable()].value_counts()
            
            # Create figure with subplots based on selected chart types
            n_plots = len(input.chart_types())
            fig, axes = plt.subplots(1, n_plots, figsize=(7*n_plots, 6))
            
            if n_plots == 1:
                axes = [axes]
            
            plot_idx = 0
            
            if "Bar Chart" in input.chart_types():
                # Bar plot
                freq_series.plot(kind='bar', ax=axes[plot_idx])
                axes[plot_idx].set_title(f'Bar Chart of {input.freq_variable()} (Distinct Households)')
                axes[plot_idx].set_xlabel(input.freq_variable())
                axes[plot_idx].set_ylabel('Frequency (Distinct Households)')
                plt.setp(axes[plot_idx].xaxis.get_majorticklabels(), rotation=45, ha='right')
                plot_idx += 1
            
            if "Pie Chart" in input.chart_types():
                # Pie plot
                freq_series.plot(kind='pie', ax=axes[plot_idx], autopct='%1.1f%%')
                axes[plot_idx].set_title(f'Pie Chart of {input.freq_variable()} (Distinct Households)')
                plot_idx += 1
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error generating plots: {str(e)}")
            return None
#===================================Check

    df1 = reactive.value(None)
    df2 = reactive.value(None)
    locations = reactive.value([])

    @reactive.effect
    @reactive.event(df1)
    def _update_locations():
        if df1() is not None and 'calc_l4_name' in df1().columns:
            unique_locations = sorted(df1()['calc_l4_name'].unique())
            locations.set(["All"] + list(unique_locations))
        else:
            locations.set([])

    # Fix: Add a proper event trigger to this effect so it only runs when locations changes
    @reactive.effect
    @reactive.event(locations)
    def _update_location_choices():
        ui.update_select(
            "column",
            label="Filter LGA",
            choices=locations(),
            selected="All" if locations() else None
        )

    def filter_by_location(df):
        """Helper function to filter dataframe by selected location"""
        if df is None or input.column() == "All":
            return df
        return df[df['calc_l4_name'] == input.column()]

    TARGET_VARIABLES = [
        "How many people are there in this household?",
        "7. Sleeping spaces",
        "calc_num_campaign_nets_hung",
        "calc_num_campaign_nets_not_hung",
        "10. Are nets used correctly?"
    ]

    @reactive.effect
    @reactive.event(input.file1)
    def _upload_df1():
        file_infos = input.file1()
        if not file_infos:
            df1.set(None)
            return
        df1.set(pd.read_excel(file_infos[0]["datapath"]))

    @reactive.effect
    @reactive.event(input.file2)
    def _upload_df2():
        file_infos = input.file2()
        if not file_infos:
            df2.set(None)
            return
        df2.set(pd.read_excel(file_infos[0]["datapath"]))

    def calculate_similarity(val1, val2):
        str1 = str(val1).lower().strip()
        str2 = str(val2).lower().strip()
        
        if pd.isna(val1) and pd.isna(val2):
            return 1.0
        elif pd.isna(val1) or pd.isna(val2):
            return 0.0
        elif str1 == str2:
            return 1.0
        else:
            return 0.0

    def calculate_score(similarity):
        return 1 if similarity == 1.0 else -1

    @render.text
    def comparison_title():
        df1_filtered = filter_by_location(df1())
        if df1_filtered is None or df1_filtered.empty:
            return "No data available for selected location."
        if df1() is not None and df2() is not None:
            return "Comparison Results for All Target Variables"
        return ""

    @render.code
    def similarity_score():
        if df1() is None or df2() is None:
            return "Please upload both files to see comparisons."
            
        df1_filtered = filter_by_location(df1())
        if df1_filtered is None or df1_filtered.empty:
            return "No data available for selected location."
        
        summary_parts = []
        total_matches = 0
        total_records = 0
        
        line = "=" * 50
        
        summary_parts.append("📊 DETAILED ANALYSIS SUMMARY\n" + line)
        
        for var in TARGET_VARIABLES:
            if var not in df1_filtered.columns or var not in df2().columns:
                continue
                    
            merged_df = pd.merge(
                df1_filtered,
                df2()[[var, 'calc_household_id']],
                on='calc_household_id',
                how='inner',
                suffixes=('_1', '_2')
            )
            
            perfect_matches = 0
            total = len(merged_df)
            
            for _, row in merged_df.iterrows():
                val1 = row[f"{var}_1"] if f"{var}_1" in merged_df.columns else row[var]
                val2 = row[f"{var}_2"]
                similarity = calculate_similarity(val1, val2)
                if similarity == 1.0:
                    perfect_matches += 1
            
            percentage = (perfect_matches / total) * 100 if total > 0 else 0
            total_matches += perfect_matches
            total_records += total
            
            var_stats = f"""
    📌 Variable: {var}
    ├─ Matching Records: {perfect_matches:,}
    ├─ Total Records: {total:,}
    └─ Similarity Rate: {percentage:.2f}%
    """
            summary_parts.append(var_stats)
        
        overall_percentage = (total_matches / total_records) * 100 if total_records > 0 else 0
        
        overall_stats = f"""
    {line}
    📈 OVERALL STATISTICS
    ├─ Total Matching Records: {total_matches:,}
    ├─ Total Records Compared: {total_records:,}
    └─ Overall Similarity Rate: {overall_percentage:.2f}%
    """
        summary_parts.append(overall_stats)
        
        return "\n".join(summary_parts)

    @render.text
    def match_counts():
        if df1() is None or df2() is None:
            return ""
        
        df1_filtered = filter_by_location(df1())
        if df1_filtered is None or df1_filtered.empty:
            return "No data available for selected location."
        
        total_matches = 0
        total_mismatches = 0
        
        for var in TARGET_VARIABLES:
            if var not in df1_filtered.columns or var not in df2().columns:
                continue
                    
            merged_df = pd.merge(
                df1_filtered,
                df2()[[var, 'calc_household_id']],
                on='calc_household_id',
                how='inner',
                suffixes=('_1', '_2')
            )
            
            for _, row in merged_df.iterrows():
                val1 = row[f"{var}_1"] if f"{var}_1" in merged_df.columns else row[var]
                val2 = row[f"{var}_2"]
                similarity = calculate_similarity(val1, val2)
                if similarity == 1.0:
                    total_matches += 1
                else:
                    total_mismatches += 1
        
        total = total_matches + total_mismatches
        return f"""
        Overall Score Distribution:
        ✅ Total Matches: {total_matches}
        ❌ Total Mismatches: {total_mismatches}
        📝 Total Comparisons: {total}
        """

    @render.ui
    def similarity_table():
        if df1() is None or df2() is None:
            return ui.p("Upload files to see comparison results.", class_="text-muted")
        
        df1_filtered = filter_by_location(df1())
        if df1_filtered is None or df1_filtered.empty:
            return ui.p("No data available for selected location.", class_="text-warning")
        
        all_comparisons = []
        
        for var in TARGET_VARIABLES:
            if var not in df1_filtered.columns or var not in df2().columns:
                continue
                    
            merged_df = pd.merge(
                df1_filtered,
                df2()[[var, 'calc_household_id']],
                on='calc_household_id',
                how='inner',
                suffixes=('_1', '_2')
            )
            
            comparison_data = []
            for _, row in merged_df.iterrows():
                val1 = row[f"{var}_1"] if f"{var}_1" in merged_df.columns else row[var]
                val2 = row[f"{var}_2"]
                similarity = calculate_similarity(val1, val2)
                score = calculate_score(similarity)
                
                village = (f"{row['calc_l4_name']} - {row['calc_village_name']}" 
                        if 'calc_l4_name' in merged_df.columns and 'calc_village_name' in merged_df.columns 
                        else 'N/A')
                hh_id = row['calc_household_id']
                
                comparison_data.append({
                    'Variable': var,
                    'Village': village,
                    'Household ID': hh_id,
                    'Main': val1,
                    'Revisit': val2,
                    'Match': '✅ Yes' if similarity == 1.0 else '❌ No',
                    'Score': f"{score:+d}"
                })
            
            all_comparisons.extend(comparison_data)
        
        if not all_comparisons:
            return ui.p("No comparisons could be generated.", class_="text-warning")
                
        result_df = pd.DataFrame(all_comparisons)
        
        return ui.HTML(
            DT(
                result_df,
                maxBytes=0,
                layout={"top": "searchBuilder"}, 
                keys=True,
                scrollCollapse=True,
                scrollY= '200px',
                paging=False,
                classes="display nowrap compact",
                buttons=["pageLength", "copyHtml5", "csvHtml5", "excelHtml5", 'print']
            )
        )  
app = App(app_ui, server)