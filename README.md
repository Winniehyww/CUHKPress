# CUHKPress

This is an interactive Dash web application for visualizing historical university events and matching them to digitized PDF archives. It integrates timeline exploration, filtering, similarity-based PDF lookup, and inline preview rendering.

## 📚 Data Source

The original event and document data are sourced from the CUHK University Press Archive, available at:

👉 [CUHK University Press Archive](https://repository.lib.cuhk.edu.hk/en/collection/archive/pr)

All event information and PDF documents in this app are processed from the above repository.

## 🔧 Features

### Main Features

- **Interactive Timeline**: Visualize university events chronologically, with color-coded categories for easy identification.
- **Event Filtering**: Search and filter events by date range, topic labels, or keywords.
- **Event Details**: Click any timeline point to view full event details, including title, date, category, tags, and content.
- **PDF Auto-Matching**: Automatically match events to related PDF documents using exact or similarity-based title matching.
- **PDF Preview & Viewer**: Instantly preview the first page of matched PDFs and open the full document in an embedded viewer.
- **Responsive UI**: Built with Dash Bootstrap Components for a clean, modern, and mobile-friendly interface.
- **Category & Tag Analytics**: Pie chart visualization of event distribution by category or tag.
- **Flexible Data Import**: Parses event data from Markdown files and document metadata from Excel.

## 🚀 How It Works

1. **Data Parsing**: Event data is extracted from Markdown files, and document metadata is loaded from Excel.
2. **Categorization**: Events are automatically categorized based on their tags and mapped to color codes.
3. **Visualization**: Timeline and pie chart are generated using Plotly, allowing interactive exploration.
4. **PDF Matching**: When an event is selected, the app finds related PDFs by exact or fuzzy title matching, showing similarity scores.
5. **Preview & Access**: Users can preview the first page of a PDF and open the full document inline.

## 📦 Requirements

- Python 3.8+
- Dash
- dash-bootstrap-components
- pandas
- plotly
- pdf2image
- flask

See `requirements.txt` for full dependencies.

## 📝 License & Attribution

This project is for academic and research purposes. Original data and documents are attributed to CUHK University Press Archive.