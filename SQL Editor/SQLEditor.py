from ursina import *
from ursina.prefabs.file_browser import *
from ursina.prefabs.file_browser_save import *
from ursina.shaders.basic_lighting_shader import *
import pandas as pd
import sqlite3


window.borderless = True

app = Ursina()
window.color=color.black
window.fullscreen=True
window.fps_counter.enabled = False
window.cog_button.enabled = False
window.cog_menu.enabled = False
window.collider_counter.enabled = False
window.entity_counter.enabled = False
window.exit_button.enabled = False


file_browser = FileBrowser(file_types=['.csv'], enabled=False)
query_input = TextField(position=(-0.25, .2), max_lines=18, enabled=True)
query_input.text_entity.color=color.cyan
query_input.bg.color=color.hsv(0, 0, 0.1)
load_button = Button(text='Load CSV', position=(-0.1, .3), color=color.green, scale=(0.3, 0.07), enabled=True)
load_button.text_entity.color=color.black
run_button = Button(text='Run SQL Query', position=(.2, .3), color=color.green, scale=(0.3, 0.07), enabled=True)
run_button.text_entity.color=color.black
input_text = Text(x=-.875, y=.3, font="IBMPlexMono-Regular.ttf", enabled=True)
output_text = Text(x=-.875, y=-.3, font="IBMPlexMono-Regular.ttf", enabled=True, color=color.green)
filename_text = Text(x=-.875, y=.325, font="IBMPlexMono-Bold.ttf", enabled=True, color=color.azure)

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
    filename = str(file_path.split("\\")[-1]).rstrip(".csv")
    df = pd.read_csv(file_path)
    if db_conn is None:
        db_conn = sqlite3.connect(':memory:')
    df.to_sql(filename, db_conn, index=False, if_exists='replace')
    input_text.text += str("\n")*rounds+str("\n\n")+run_query(f"SELECT * FROM {filename};")
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

load_button.on_click = open_file_browser
file_browser.on_submit = load_csv
run_button.on_click = run
file_browser.cancel_button.on_click=file_browser_close
file_browser.cancel_button_2.on_click=file_browser_close
app.run()
