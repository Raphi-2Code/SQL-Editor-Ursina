from ursina import *
from ursina.prefabs.file_browser import *
from ursina.prefabs.file_browser_save import *
from ursina.shaders.basic_lighting_shader import *
from math import floor
import csv
import sqlite3

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None


window.borderless = False

app = Ursina()
window.color = color.black
window.fullscreen = False
window.size = (1280, 800)
window.title = 'SQL Editor'
window.fps_counter.enabled = False
window.cog_button.enabled = False
window.cog_menu.enabled = False
window.collider_counter.enabled = False
window.entity_counter.enabled = False
window.exit_button.enabled = False


file_browser = FileBrowser(file_types=['.csv'], enabled=False)
query_input = TextField(max_lines=18, enabled=True)
query_input.text_entity.color=color.cyan
query_input.bg.color=color.hsv(0, 0, 0.1)
load_button = Button(text='Load CSV', color=color.green, scale=(0.3, 0.07), enabled=True)
load_button.text_entity.color=color.black
run_button = Button(text='Run SQL Query', color=color.green, scale=(0.3, 0.07), enabled=True)
run_button.text_entity.color=color.black
input_text = Text(font="IBMPlexMono-Regular.ttf", enabled=True)
output_text = Text(font="IBMPlexMono-Regular.ttf", enabled=True, color=color.green)
filename_text = Text(font="IBMPlexMono-Bold.ttf", enabled=True, color=color.azure)

SIDE_MARGIN = 0.04
GUTTER = 0.035
TOP_MARGIN = 0.065
BOTTOM_MARGIN = 0.055
BUTTON_HEIGHT = 0.07
BUTTON_GAP = 0.005

last_window_size = None

def clamp_value(value, minimum, maximum):
    return max(minimum, min(value, maximum))

def quote_identifier(identifier):
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'

def unique_column_names(columns):
    names = []
    counts = {}
    for index, column in enumerate(columns):
        name = str(column).strip() or f'column_{index + 1}'
        counts[name] = counts.get(name, 0) + 1
        if counts[name] > 1:
            name = f'{name}_{counts[name]}'
        names.append(name)
    return names

def load_csv_into_db(file_path, table_name):
    global db_conn
    if db_conn is None:
        db_conn = sqlite3.connect(':memory:')

    if pd is not None:
        df = pd.read_csv(file_path)
        df.to_sql(table_name, db_conn, index=False, if_exists='replace')
        return

    with open(file_path, newline='', encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader, None)
        if not headers:
            raise ValueError('CSV is empty')

        headers = unique_column_names(headers)
        quoted_table = quote_identifier(table_name)
        quoted_columns = ', '.join(f'{quote_identifier(header)} TEXT' for header in headers)
        placeholders = ', '.join('?' for _ in headers)

        cursor = db_conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS {quoted_table}')
        cursor.execute(f'CREATE TABLE {quoted_table} ({quoted_columns})')
        for row in reader:
            values = row[:len(headers)] + [''] * max(0, len(headers) - len(row))
            cursor.execute(f'INSERT INTO {quoted_table} VALUES ({placeholders})', values)
        db_conn.commit()

def ui_bounds():
    half_width = window.aspect_ratio / 2
    return -half_width + SIDE_MARGIN, half_width - SIDE_MARGIN

def layout_ui():
    global last_window_size
    last_window_size = tuple(window.size)

    left_edge, right_edge = ui_bounds()
    content_width = max(0.1, right_edge - left_edge)
    top_edge = 0.5 - TOP_MARGIN
    bottom_edge = -0.5 + BOTTOM_MARGIN

    button_width = clamp_value(content_width * 0.21, 0.24, 0.34)
    total_button_width = button_width * 2 + BUTTON_GAP
    button_y = top_edge - BUTTON_HEIGHT / 2
    load_button.scale = (button_width, BUTTON_HEIGHT)
    run_button.scale = (button_width, BUTTON_HEIGHT)
    load_button.position = (-total_button_width / 4 - BUTTON_GAP / 4, button_y)
    run_button.position = (total_button_width / 4 + BUTTON_GAP / 4, button_y)

    query_top = button_y - BUTTON_HEIGHT / 2 - 0.055
    query_bottom = bottom_edge + 0.16
    query_height = max(0.22, query_top - query_bottom)

    left_column_width = clamp_value(content_width * 0.34, 0.42, 0.64)
    query_left = left_edge + left_column_width + GUTTER
    if right_edge - query_left < 0.42:
        query_left = left_edge
        query_top -= 0.06
        query_height = max(0.24, query_top - (bottom_edge + 0.24))

    query_width = max(0.3, right_edge - query_left)
    query_input.position = (query_left, query_top)
    query_input.bg.scale_x = query_width
    query_input.bg.scale_y = query_height

    visible_lines = max(4, floor(query_height / (Text.size * query_input.line_height)))
    if query_input.max_lines != visible_lines:
        query_input.max_lines = visible_lines
        query_input.render()

    filename_text.x = left_edge
    filename_text.y = query_top + 0.055
    input_text.x = left_edge
    input_text.y = query_top + 0.03
    output_text.x = left_edge
    output_text.y = bottom_edge + 0.045

db_conn = None

def open_file_browser():
    file_browser.enabled = True
    query_input.enabled = False
    load_button.enabled = False
    run_button.enabled = False
    output_text.enabled = False
    input_text.enabled = False
    filename_text.enabled = False
def file_browser_close():
    file_browser.enabled = False
    query_input.enabled = True
    load_button.enabled = True
    run_button.enabled = True
    output_text.enabled = True
    input_text.enabled = True
    filename_text.enabled = True
i=0
lrows=0
lenrows=0
rounds=0
def load_csv(self):
    global db_conn,lrows,lenrows,rounds
    file_browser_close()
    if file_browser.path == '':
        output_text.text = 'No file selected'
        return
    file_path = f'{file_browser.selection_getter()[0]}'
    filename = str(file_path.split("/")[-1]).rstrip(".csv")
    try:
        load_csv_into_db(file_path, filename)
    except Exception as e:
        output_text.text = f'Error loading CSV: {str(e)}'
        return
    input_text.text += str("\n")*rounds+str("\n\n")+run_query(f"SELECT * FROM {quote_identifier(filename)};")
    filename_text.text+= str("\n")*rounds+str("\n")*(lenrows+2)+str(f"{filename}")
    output_text.text = 'CSV loaded successfully'
    lenrows=lrows
    rounds+=1
def run_query(query, output=False):
    global db_conn, lrows
    if db_conn is None:
        output_text.text = 'Load CSV first'
        return
    try:
        cursor = db_conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        max_widths = [max(len(str(item)) for item in [header] + [row[i] for row in rows]) for i, header in enumerate(headers)]
        formatted_headers = '  '.join(header.ljust(max_widths[i]) for i, header in enumerate(headers))
        formatted_rows = ['  '.join(str(item).ljust(max_widths[i]) for i, item in enumerate(row)) for row in rows]
        df_result = '\n'.join([formatted_headers] + formatted_rows)
        if not output==True:
            lrows=len(rows)
        return df_result
    except Exception as e:
        return f'Error running query: {str(e)}'


def run():
    output_text.text = run_query(query_input.text, output=True)

def update():
    if tuple(window.size) != last_window_size:
        layout_ui()

load_button.on_click = open_file_browser
file_browser.on_submit = load_csv
run_button.on_click = run
file_browser.cancel_button.on_click=file_browser_close
file_browser.cancel_button_2.on_click=file_browser_close
layout_ui()
app.run()
