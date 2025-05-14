import pandas as pd
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State
from pdf2image import convert_from_path
import base64
from flask import send_from_directory, Response
import re
import os
from pathlib import Path
import random
import uuid
import mimetypes
import difflib
import json

# Add PDF info file
pdf_info_file = './1983articles.xlsx'
pdf_df = pd.read_excel(pdf_info_file)

# Parse data from Markdown files
def parse_markdown_files(directory):
    """Parse all Markdown files in the directory and extract event data."""
    all_data = []
    all_labels = set()
    
    # Get all Markdown files in the directory
    markdown_files = list(Path(directory).glob('*.md'))
    if not markdown_files:
        # If it's a relative path issue, try a test file
        with open('1983_part_1.md', 'r', encoding='utf-8') as file:
            markdown_files = ['1983_part_1.md']
    
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Use regex to extract event blocks
                event_blocks = re.findall(r'## (.+?)\s+\*\*Date:\*\* (.+?)\s+\*\*Content:\*\* (.+?)\s+\*\*Labels:\*\* (.+?)(?=\n---|\Z)', content, re.DOTALL)
                
                for block in event_blocks:
                    title = block[0].strip()
                    date = block[1].strip()
                    content = block[2].strip()
                    labels_text = block[3].strip()
                    
                    # Extract labels
                    labels = re.findall(r'#(\w+)', labels_text)
                    all_labels.update(labels)
                    
                    all_data.append({
                        'Article Title': title,
                        'Date': date,
                        'Content': content,
                        'Raw Labels': labels_text,
                        'Labels': labels
                    })
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
    
    return pd.DataFrame(all_data), list(all_labels)

# Use test file path
data_directory = 'F:/data'  # Data directory
df, all_labels = parse_markdown_files(data_directory)

# Convert Date column to datetime format
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

# Define category mapping based on labels
category_mapping = {
    'Academic': ['AcademicLecture', 'Education', 'Science', 'Research', 'EducationProgram', 'ScheduleChange'],
    'Cultural': ['CulturalHeritage', 'Music', 'ArtExhibition', 'CulturalActivities', 'CulturalEngagement'],
    'Community': ['CommunityEngagement', 'CommunitySupport', 'PublicAccess'],
    'Student Affairs': ['StudentSupport', 'StudentRecruitment', 'Scholarship', 'StudentSupport'],
    'University Events': ['AnniversaryEvent', 'UniversityEvent', 'FacilityOpening'],
    'Professional Development': ['ProfessionalDevelopment', 'BusinessEducation', 'TechnologyUpgrade'],
    'Conferences': ['InternationalConference', 'EducationSeminar'],
    'Research & Innovation': ['Research', 'HistoricalStudy', 'TechnologyUpgrade'],
    'Scholarships & Funding': ['Scholarship', 'FacilityOpening', 'CommunitySupport', 'Donation'],
    'Faculty Affairs': ['AcademicOpportunity', 'PartTimeStudy']
}

# Categorize events based on labels
def categorize_by_labels(labels, mapping):
    """Categorize events into predefined categories based on labels"""
    for label in labels:
        for category, related_labels in mapping.items():
            if label in related_labels:
                return category
    return "Other"

df['Category'] = df['Labels'].apply(lambda labels: categorize_by_labels(labels, category_mapping))

# Define color mapping
CATEGORY_COLORS = {
    'Academic': '#636EFA',
    'Cultural': '#00CC96',
    'Community': '#AB63FA',
    'Student Affairs': '#FFA15A',
    'University Events': '#EF553B',
    'Professional Development': '#19D3F3',
    'Conferences': '#B6E880',
    'Research & Innovation': '#FECB52',
    'Scholarships & Funding': '#FF97FF',
    'Faculty Affairs': '#00B5F7',
    'Other': '#999999'
}

# Define FACULTY_COLORS (if needed for faculty categorization)
FACULTY_COLORS = {
    # Add faculty color mapping as needed
    'Default': '#636EFA'
}

# Randomly select 50 labels as filter options
dropdown_labels = all_labels if len(all_labels) <= 50 else random.sample(all_labels, 50)

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)

# Create timeline and pie chart
def create_timeline(df, group='Category'):
    color_map = CATEGORY_COLORS if group == 'Category' else FACULTY_COLORS

    # Check if dataframe is empty
    if df.empty:
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            specs=[[{"type": "scatter"}, {"type": "domain"}]],
            horizontal_spacing=0.1
        )
        fig.update_layout(
            title="No matching data found",
            title_x=0.5,
            height=600
        )
        return fig

    # Create subplots: one for timeline, one for pie chart
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        specs=[[{"type": "scatter"}, {"type": "domain"}]],
        horizontal_spacing=0.1
    )

    # Add timeline traces
    for key, color in color_map.items():
        group_df = df[df[group] == key]
        if not group_df.empty:
            fig.add_trace(go.Scatter(
                x=group_df['Date'],
                y=[key] * len(group_df),
                mode='markers+lines',  # Add lines connecting points
                marker=dict(size=10, color='white', line=dict(width=2, color=color)),  # White center, colored border
                line=dict(color=color),  # Connection line color
                name=key,
                text=[f"Date: {date.strftime('%Y-%m-%d')}<br>Title: {title}" for date, title in zip(group_df['Date'], group_df['Article Title'])],  # Hover text
                hoverinfo='text',
                customdata=group_df.index  # For click events
            ), row=1, col=1)

    # Add pie chart
    pie_values = df[group].value_counts()
    fig.add_trace(go.Pie(
        labels=pie_values.index,
        values=pie_values.values,
        marker=dict(colors=[color_map.get(cat, '#ccc') for cat in pie_values.index]),
        hole=0.3,
        textinfo='label+percent',
        showlegend=False
    ), row=1, col=2)

    # Set year range display
    start_year = df['Date'].min().year
    end_year = df['Date'].max().year
    year_range = f"{start_year}" if start_year == end_year else f"{start_year}-{end_year}"

    fig.update_layout(
        hovermode='closest',
        xaxis_title='Date',
        yaxis_title='Category',
        legend_title=group,
        title=f'University Event Timeline ({year_range})',
        title_x=0.5,
        template='plotly_white',
        height=600
    )

    return fig

initial_fig = create_timeline(df)

# Define app layout
app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("University Events Timeline Visualization", className='text-center mb-4'), width=12)]),
    dbc.Row([
        dbc.Col(dbc.Input(id='search-input', placeholder='Search events...', type='text', className='mb-3'), width=6),
        dbc.Col(dcc.Dropdown(
            id='label-dropdown',
            options=[{'label': label, 'value': label} for label in sorted(dropdown_labels)],
            multi=True,
            placeholder='Filter by topic',
            className='mb-3'
        ), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.DatePickerRange(
            id='date-picker-range',
            min_date_allowed=df['Date'].min(),
            max_date_allowed=df['Date'].max(),
            start_date=df['Date'].min(),
            end_date=df['Date'].max(),
            display_format='YYYY-MM-DD',
            className='mb-3'
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='timeline-graph', figure=initial_fig), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.RangeSlider(
            id='time-slider',
            min=df['Date'].min().timestamp(),
            max=df['Date'].max().timestamp(),
            value=[df['Date'].min().timestamp(), df['Date'].max().timestamp()],
            marks={int(timestamp): pd.to_datetime(timestamp, unit='s').strftime('%Y-%m') 
                  for timestamp in pd.date_range(df['Date'].min(), df['Date'].max(), freq='MS').astype(int) // 10**9},
            step=86400
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='event-details', style={'margin-top': '20px', 'padding': '15px', 'border': '1px solid #ddd', 'border-radius': '5px'}), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            # Add storage components to initial layout
            dcc.Store(id='current-pdf-index', data=0),
            dcc.Store(id='pdf-paths', data=[]),
            dcc.Store(id='pdf-similarities', data={}),
            dcc.Store(id='direct-match-info', data=False),
            html.Div(id='pdf-selector', style={'margin-top': '20px'}),
            html.Div(id='pdf-preview', style={'margin-top': '20px'}),
            html.Div(id='pdf-viewer', style={'margin-top': '20px'})
        ], width=12)
    ])
], fluid=True)

# Define callback functions
@app.callback(
    [Output('timeline-graph', 'figure'),
     Output('time-slider', 'value'),
     Output('date-picker-range', 'start_date'),
     Output('date-picker-range', 'end_date')],
    [Input('search-input', 'value'),
     Input('label-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('time-slider', 'value')]
)
def update_timeline_and_sync_controls(search_text, selected_labels, start_date, end_date, time_slider):
    # Determine which control triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    filtered_df = df.copy()

    # Sync date picker and slider
    if trigger_id in ['date-picker-range']:
        # Date picker was updated, sync slider
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        slider_values = [start_date.timestamp(), end_date.timestamp()]
    elif trigger_id == 'time-slider':
        # Slider was updated, sync date picker
        start_date = pd.to_datetime(time_slider[0], unit='s')
        end_date = pd.to_datetime(time_slider[1], unit='s')
    else:
        # Other controls triggered callback, use current values
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            slider_values = [start_date.timestamp(), end_date.timestamp()]
        else:
            start_date = pd.to_datetime(time_slider[0], unit='s')
            end_date = pd.to_datetime(time_slider[1], unit='s')
            
    # Filter by date
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
    
    # Filter by search text
    if search_text:
        filtered_df = filtered_df[
            filtered_df['Article Title'].str.contains(search_text, case=False, na=False) |
            filtered_df['Content'].str.contains(search_text, case=False, na=False)
        ]
    
    # Filter by labels
    if selected_labels:
        filtered_df = filtered_df[filtered_df['Labels'].apply(lambda labels: any(label in selected_labels for label in labels))]
    
    # Update timeline
    timeline_fig = create_timeline(filtered_df, 'Category')
    
    # Convert to timestamp values
    slider_values = [start_date.timestamp(), end_date.timestamp()]
    
    return timeline_fig, slider_values, start_date, end_date

# Click event to display event details
@app.callback(
    [Output('event-details', 'children'),
     Output('pdf-selector', 'children'),
     Output('pdf-paths', 'data'),
     Output('pdf-preview', 'children'),
     Output('pdf-similarities', 'data'),
     Output('direct-match-info', 'data'),
     Output('current-pdf-index', 'data')],
    [Input('timeline-graph', 'clickData')]
)
def display_event_details(clickData):
    if not clickData:
        return html.P("Click on a point in the timeline to view details"), html.Div(), [], html.Div(), {}, False, 0
    
    # Initialize similarity_scores as empty list
    similarity_scores = []
    pdf_similarities = {}  # Dictionary to store similarity scores for each PDF
    direct_match_found = False  # Flag to track if direct matches were found
    
    point_index = clickData['points'][0]['customdata']
    event = df.iloc[point_index]
    event_title = event['Article Title']
    
    # Find related PDF files using flexible matching
    related_pdfs = pdf_df[
        # Check if PDF title contains event title
        pdf_df['Article Title'].str.contains(event_title, case=False, na=False) | 
        # Or if event title contains PDF title
        pdf_df['Article Title'].apply(lambda x: x.lower() in event_title.lower() if isinstance(x, str) else False)
    ]
    
    # If direct matches found, set similarity to 100%
    if not related_pdfs.empty:
        direct_match_found = True
        # Set 100% similarity for all directly matched PDFs
        for idx in related_pdfs.index:
            pdf_similarities[idx] = 1.0  # 100% similarity
    
    # If no related PDFs found, find the most similar ones
    if related_pdfs.empty:
        # Calculate similarity between event title and each PDF title
        for idx, row in pdf_df.iterrows():
            pdf_title = row['Article Title']
            if isinstance(pdf_title, str) and isinstance(event_title, str):
                # Use SequenceMatcher to calculate similarity
                similarity = difflib.SequenceMatcher(None, pdf_title.lower(), event_title.lower()).ratio()
                similarity_scores.append((idx, similarity))
                pdf_similarities[idx] = similarity  # Save similarity score for each PDF
        
        # Sort by similarity in descending order
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 3 most similar PDFs
        top_similar_indices = [idx for idx, _ in similarity_scores[:3]]
        related_pdfs = pdf_df.iloc[top_similar_indices]
    
    # Create event details display
    event_details = [
        html.H4(event['Article Title']),
        html.P(f"Date: {event['Date'].strftime('%Y-%m-%d')}"),
        html.P(f"Category: {event['Category']}"),
        html.P(f"Tags: {event['Raw Labels']}"),
        html.H5("Content:"),
        html.P(event['Content'])
    ]
    
    # If related PDFs found, create PDF selector
    if not related_pdfs.empty:
        pdf_files = related_pdfs['pdf Name'].tolist()
        pdf_buttons = []
        
        # 创建索引映射字典，保存按钮索引到原始PDF索引的映射
        index_mapping = {}
        for i, (idx, row) in enumerate(related_pdfs.iterrows()):
            index_mapping[i] = idx
        
        # 将索引映射添加到pdf_similarities中
        pdf_similarities['index_mapping'] = index_mapping
        
        # Generate preview for first PDF
        preview_element = generate_preview_image(f"./pdf/{pdf_files[0]}")
        
        for i, (idx, row) in enumerate(related_pdfs.iterrows()):
            pdf_file = row['pdf Name']
            button_style = {'margin': '5px', 'backgroundColor': '#007bff' if i == 0 else '#6c757d'}
            
            # Add similarity score to button in percentage format
            similarity_text = ""
            if idx in pdf_similarities:
                # Convert similarity to percentage format
                similarity_percentage = int(pdf_similarities[idx] * 100)
                similarity_text = f" (Match: {similarity_percentage}%)"
                
            pdf_buttons.append(
                dbc.Button(
                    f"Doc {i+1}: {pdf_file[:15]}...{similarity_text}",
                    id={'type': 'pdf-button', 'index': i},
                    style=button_style,
                    className="me-2"
                )
            )
        
        pdf_selector = [
            html.H5("Related Documents:" + (" (Direct Match)" if direct_match_found else " (Similarity Match)")),
            html.Div(pdf_buttons, style={'display': 'flex', 'flexWrap': 'wrap'})
        ]
        
        # 将相似度信息转换为可JSON序列化的格式
        pdf_similarities_json = {str(k): v for k, v in pdf_similarities.items()}
        
        return event_details, pdf_selector, pdf_files, preview_element, pdf_similarities_json, direct_match_found, 0
    else:
        return event_details, html.Div("No related documents for this event"), [], html.Div(), {}, False, 0

# Helper function to generate PDF preview image
def generate_preview_image(pdf_path):
    # Check if file exists
    if not os.path.exists(pdf_path):
        return html.Div(f"File not found: {pdf_path}")
    
    try:
        # Create custom temp directory
        custom_temp_dir = "./temp"
        os.makedirs(custom_temp_dir, exist_ok=True)
        
        # Generate unique temp file name
        temp_file_path = os.path.join(custom_temp_dir, f"preview_{uuid.uuid4().hex}.jpg")
        
        # Convert first page of PDF to image
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        
        if images:
            # Save image to custom temp directory
            images[0].save(temp_file_path, 'JPEG')
            
            # Read image and convert to base64
            with open(temp_file_path, 'rb') as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode()
            
            # Delete temp file
            try:
                os.remove(temp_file_path)
            except:
                pass  # Continue if deletion fails
            
            # Return preview image with button next to the title
            return html.Div([
                html.Div([
                    html.H5("PDF Preview", style={"display": "inline-block", "margin-right": "15px"}),
                    dbc.Button(
                        "View Full Document", 
                        id="show-full-pdf", 
                        color="primary",
                        size="sm",
                        className="align-middle"
                    )
                ]),
                html.Img(src=f"data:image/jpeg;base64,{img_base64}", 
                         style={"max-width": "100%", "max-height": "700px", "margin-bottom": "15px"})
            ])
    except Exception as e:
        return html.Div([
            html.P(f"Cannot generate preview (Error: {str(e)})", style={"color": "red"})
        ])


@app.callback(
    [Output('current-pdf-index', 'data', allow_duplicate=True),
     Output('pdf-preview', 'children', allow_duplicate=True),
     Output('pdf-selector', 'children', allow_duplicate=True)],
    [Input({'type': 'pdf-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('pdf-paths', 'data'),
     State('current-pdf-index', 'data'),
     State('direct-match-info', 'data'),
     State('pdf-similarities', 'data')],
    prevent_initial_call=True  
)
def update_selected_pdf(button_clicks, pdf_paths, current_index, direct_match, pdf_similarities):
    ctx = dash.callback_context
    
    if not ctx.triggered or pdf_paths is None or len(pdf_paths) == 0:
        return current_index, dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        clicked_index = json.loads(button_id)['index']
    except:
        return current_index, dash.no_update, dash.no_update
    
    if clicked_index < 0 or clicked_index >= len(pdf_paths):
        return current_index, dash.no_update, dash.no_update
    
    # 生成新的预览
    preview = generate_preview_image(f"./pdf/{pdf_paths[clicked_index]}")
    
    # 创建新的按钮组，更新所选按钮的颜色
    pdf_buttons = []
    
    # 获取索引映射
    index_mapping = None
    if pdf_similarities and 'index_mapping' in pdf_similarities:
        try:
            index_mapping = pdf_similarities['index_mapping']
        except:
            pass
    
    for i, pdf_file in enumerate(pdf_paths):
        # 当前选中的按钮为蓝色，其他为灰色
        button_style = {'margin': '5px', 'backgroundColor': '#007bff' if i == clicked_index else '#6c757d'}
        
        # 添加相似度文本
        similarity_text = ""
        if pdf_similarities and index_mapping and str(i) in index_mapping:
            # 使用映射找到原始PDF索引
            original_idx = str(index_mapping[str(i)])
            if original_idx in pdf_similarities:
                similarity_percentage = int(float(pdf_similarities[original_idx]) * 100)
                similarity_text = f" (Match: {similarity_percentage}%)"
        
        pdf_buttons.append(
            dbc.Button(
                f"Doc {i+1}: {pdf_file[:15]}...{similarity_text}",
                id={'type': 'pdf-button', 'index': i},
                style=button_style,
                className="me-2"
            )
        )
    
    # 创建新的选择器组件
    updated_selector = [
        html.H5("Related Documents:" + (" (Direct Match)" if direct_match else " (Similarity Match)")),
        html.Div(pdf_buttons, style={'display': 'flex', 'flexWrap': 'wrap'})
    ]
    
    return clicked_index, preview, updated_selector


@app.callback(
    Output('pdf-viewer', 'children'),
    [Input('show-full-pdf', 'n_clicks'),
     Input('current-pdf-index', 'data'),
     Input('pdf-paths', 'data')]
)
def display_full_pdf(n_clicks, pdf_index, pdf_paths):
    if not n_clicks or not pdf_paths:
        return html.Div()  # 如果按钮未点击或无PDF，则返回空div
    
    # 确保索引在范围内
    if pdf_index >= len(pdf_paths):
        pdf_index = 0
    
    # 使用合适的尺寸显示完整PDF
    return html.Div([
        html.Iframe(
            src=f"/pdf_viewer/{pdf_paths[pdf_index]}",
            style={"width": "100%", "height": "800px", "border": "none"}
        )
    ])

# Add route to serve PDF files with proper headers
@app.server.route('/pdf_viewer/<path:path>')
def serve_pdf(path):
    response = send_from_directory('./pdf', path)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=%s' % path
    return response



app = dash.Dash(__name__)
server = app.server  # Expose server for gunicorn

app.layout = html.Div([
    html.H1("Welcome to CUHKPress"),
    html.P("This is your live Dash app deployed on Railway.")
])
