import pandas as pd
import geopandas as gpd
from dash import Dash, dash_table, dcc, html, Input, Output, no_update

# MassSave + REJ data file
GEOJSON_PATH = "data/rej_with_masssave_participation.geojson"
CSV_OUTPUT_PATH = "data/rej_with_masssave_participation_table.csv"

def load_table(path: str) -> pd.DataFrame:
    gdf = gpd.read_file(path)
    # Only tabular properties for the table view
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    return df

df_full = load_table(GEOJSON_PATH)
# Uncomment in the case that the GeoJSON data changes
# df_full.to_csv(CSV_OUTPUT_PATH, index=False)
# print(f"Table data saved to {CSV_OUTPUT_PATH}")

# Infer Dash column types
def dash_col_type(s: pd.Series) -> str:
    return "numeric" if pd.api.types.is_numeric_dtype(s) else "text"

columns = [{"name": c, "id": c, "type": dash_col_type(df_full[c])} for c in df_full.columns]

app = Dash(__name__)
app.title = "REJ + MassSave Participation Table"

app.layout = html.Div(
    style={"fontFamily": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", "padding": "12px"},
    children=[
        html.H2("REJ × MassSave Participation (Preview)", style={"marginBottom": "8px"}),
        html.Div(
            "Simple browser table for quick QA: sort, per-column filters (top row), pagination at 50 rows, plus a global contains filter.",
            style={"color": "#444", "marginBottom": "12px"}
        ),
        html.Div(
            [
                html.Label("Global contains filter (matches any column):", style={"marginRight": "8px"}),
                dcc.Input(id="global-filter", type="text", placeholder="e.g., ACTON or 29.388", debounce=True, style={"width": "320px"}),
                html.Span(id="row-count", style={"marginLeft": "12px", "color": "#666"})
            ],
            style={"marginBottom": "8px"}
        ),
        dash_table.DataTable(
            id="rej-table",
            data=df_full.to_dict("records"),
            columns=columns,
            page_size=50,
            sort_action="native",
            filter_action="native",  # per-column simple filtering UI
            row_deletable=False,
            editable=False,
            cell_selectable=False,
            style_table={"height": "78vh", "overflowY": "auto"},
            style_cell={
                "minWidth": "100px",
                "width": "150px",
                "maxWidth": "400px",
                "whiteSpace": "normal",
                "textOverflow": "ellipsis",
                "padding": "6px",
                "fontSize": "12px",
            },
            style_header={
                "fontWeight": "600",
                "backgroundColor": "#f7f7f7",
                "border": "1px solid #ddd",
            },
            style_data={"border": "1px solid #eee"},
        ),
    ],
)

@app.callback(
    Output("rej-table", "data"),
    Output("row-count", "children"),
    Input("global-filter", "value"),
)
def apply_global_contains_filter(q):
    if not q:
        return df_full.to_dict("records"), f"{len(df_full):,} rows"
    q = str(q).strip().lower()
    if not q:
        return df_full.to_dict("records"), f"{len(df_full):,} rows"
    # Simple contains across all columns
    mask = pd.Series(False, index=df_full.index)
    for c in df_full.columns:
        s = df_full[c]
        # Convert to string for uniform contains; handle NaN
        mask = mask | s.astype(str).str.lower().str.contains(q, na=False)
    filtered = df_full[mask]
    return filtered.to_dict("records"), f"{len(filtered):,} rows (filtered)"

if __name__ == "__main__":
    app.run(debug=True)