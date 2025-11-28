from nicegui import ui
import json, os

with open('data.json') as f:
    data = json.load(f)

editable_rows = []

def process_data():
    updated_data = []
    for row in editable_rows:
        updated = {
            'Part Number': row['Part Number'].text,
            'Thickness': int(row['Thickness'].text),
            'Material': row['Material'].text,
            'Quantity': int(row['Quantity'].text),
            'Adjust Qty': int(row['Adjust Qty'].value),
            'Undersize': row['Undersize'].text,
            'Holes': row['Holes'].text,
            'Drill Template': bool(row['Drill Template'].value),
            'Process': row['Process'].text,
            'Notes' : 'Example: Exceeds bed size',
        }
        updated_data.append(updated)
    with open('updated_data.json', 'w') as f:
        json.dump(updated_data, f, indent=4)
    ui.notify('Saved updates to updated_data.json')

# Header
with ui.row().classes('w-full font-bold'):
    for col in data[0].keys():
        ui.label(col).classes('w-40 p-1')

# Rows
for row in data:
    editor = {}
    with ui.row().classes('w-full items-center'):
        for key in row:
            if key == 'Material' and str(row[key]).strip().upper() == 'CR4':
                editor[key] = ui.label(str(row[key])).classes('w-40 p-1 bg-green-100').style('background-color:#d1fae5;')
            elif key == 'Adjust Qty':
                editor[key] = ui.number(value=row[key], min=-9999, max=9999, step=1).classes('w-40 p-1')
            elif key == 'Drill Template':
                editor[key] = ui.switch(value=bool(row[key])).classes('w-44 p-1')
            else:
                editor[key] = ui.label(str(row[key])).classes('w-40 p-1')
    editable_rows.append(editor)


ui.button('Process Data', on_click=process_data).classes('mt-4')

PORT = int(os.getenv('PORT', '8051'))
ui.run(host='127.0.0.1', port=PORT, reload=False)