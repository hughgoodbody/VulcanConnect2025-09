import json
from nicegui import ui
import sys
import traceback

def table_display(data, material_list, undersize_options):
    try:
        with open("user_data/hugh/SupplierDetails.json", "r") as f:
            suppliers = json.load(f)
            supplier_list = [s["Name"] for s in suppliers]

        def extract_processes_by_supplier(details):
            mapping = {}
            for s in details:
                name = s.get('Name')
                processes = [p for p in s.get('Process', []) if isinstance(p, str)]
                mapping[name] = processes
            return mapping

        supplier_to_processes = extract_processes_by_supplier(suppliers)

        # ===== helpers =======================================================

        editable_rows = []  # list of per-row editor dicts (for saving)

        def _bind_supplier_to_process(s_comp, p_comp):
            def refresh_process(_=None, s=s_comp, p=p_comp):
                supplier = s.value or ''
                opts = supplier_to_processes.get(supplier, []) or []
                # If current selection not valid for this supplier, pick first valid (or None)
                if p.value not in opts:
                    p.value = opts[0] if opts else None
                p.options = opts
                if not opts:
                    p.props('placeholder=Select supplier first')
                p.update()
            refresh_process()
            s_comp.on('update:model-value', refresh_process)

        def _material_select(initial_val, size_class):
            # keep user's current value even if it's not in the list
            if initial_val and initial_val not in material_list:
                options = [initial_val] + [m for m in material_list if m != initial_val]
            else:
                options = material_list

            comp = ui.select(
                options=options,
                value=initial_val,
                clearable=False,
            ).classes(size_class).props('use-input input-debounce=0')

            def toggle_highlight(_=None, c=comp):
                if c.value in (None, ''):
                    c.style('background-color:#FFFF00;')
                else:
                    c.style('background-color:transparent;')

            toggle_highlight()
            comp.on('update:model-value', toggle_highlight)
            comp.on('clear', toggle_highlight)
            return comp

        def _supplier_select(initial_val, size_class):
            # Keep JSON value even if not in the list so it displays
            if initial_val and initial_val not in supplier_list:
                options = [initial_val] + [s for s in supplier_list if s != initial_val]
            else:
                options = supplier_list

            s_comp = ui.select(
                options=options,
                value=initial_val,
                clearable=False,
            ).classes(size_class)

            # Prevent empty value being set
            prev_value = initial_val
            def enforce_non_empty(e, c=s_comp):
                nonlocal prev_value
                if e.value in (None, ''):
                    c.value = prev_value
                else:
                    prev_value = e.value
            s_comp.on('update:model-value', enforce_non_empty)

            if initial_val in (None, ''):
                s_comp.props('placeholder=Select supplier')

            return s_comp

        def _process_select(initial_process, selected_supplier, size_class):
            proc_options = supplier_to_processes.get(selected_supplier or '', []) or []
            if initial_process in proc_options:
                start_val = initial_process
            else:
                start_val = proc_options[0] if proc_options else None

            p_comp = ui.select(
                options=proc_options,
                value=start_val,
                clearable=False,
            ).classes(size_class)

            if not proc_options:
                p_comp.props('placeholder=Select supplier first')

            return p_comp

        def add_row_ui(row):
            """Render a single editable row and register it in editable_rows."""
            editor = {}

            with ui.row().classes('w-full items-center'):
                
                for key in row:
                    size_class = (
                        'flex-[0.5] p-1' if key in ['Thickness', 'Quantity', 'Adjust Qty', 'Drill Template']
                        else ('flex-[2] p-1' if key == 'Notes' else 'flex-1 p-1')
                    )

                    if key == 'Material':
                        initial_val = '' if row[key] in (None, 'None') else str(row[key])
                        comp = _material_select(initial_val, size_class)
                        editor[key] = comp

                    elif key == 'Supplier':
                        initial_val = '' if row[key] in (None, 'None') else str(row[key])
                        s_comp = _supplier_select(initial_val, size_class)
                        editor[key] = s_comp
                        if 'Process' in editor:
                            _bind_supplier_to_process(s_comp, editor['Process'])

                    elif key == 'Process':
                        initial_process = '' if row[key] in (None, 'None') else str(row[key])
                        selected_supplier = ''
                        # supplier value from the row dict (if present) or will be bound when Supplier comp exists
                        if 'Supplier' in row and row['Supplier'] not in (None, 'None'):
                            selected_supplier = str(row['Supplier'])
                        p_comp = _process_select(initial_process, selected_supplier, size_class)
                        editor[key] = p_comp
                        # will be bound after Supplier component exists (below), if present

                    elif key == 'Undersize Holes':
                        initial_val = '' if row[key] in (None, 'None') else str(row[key])
                        start_val = initial_val if initial_val in undersize_options else (undersize_options[0] if undersize_options else None)
                        u_comp = ui.select(
                            options=undersize_options,
                            value=start_val,
                            clearable=False,
                        ).classes(size_class)
                        editor[key] = u_comp

                    elif key == 'Adjust Qty':
                        editor[key] = ui.number(value=row[key], min=-9999, max=9999, step=1).classes(size_class)

                    elif key == 'Drill Template':
                        editor[key] = ui.switch(value=bool(row[key])).classes(size_class)

                    else:
                        # non-editable labels
                        editor[key] = ui.label(str(row[key])).classes(size_class)

                # extra "Notes" column to stay aligned with header
                ui.label('Notes').classes('flex-[2] p-1')

            # now that both Supplier & Process components may exist, bind if possible
            if 'Supplier' in editor and 'Process' in editor:
                _bind_supplier_to_process(editor['Supplier'], editor['Process'])

            editable_rows.append(editor)

        def process_data():
            updated_data = []
            for row in editable_rows:
                # Try to read values defensively (label vs select/number/switch)
                def read_text(comp):
                    try:
                        return comp.text
                    except Exception:
                        return comp.value

                updated = {
                    'Part Number': read_text(row.get('Part Number')),
                    'Thickness': int(read_text(row.get('Thickness'))),
                    'Material': row.get('Material').value if row.get('Material') else None,
                    'Quantity': int(read_text(row.get('Quantity'))),
                    'Adjust Qty': int((row.get('Adjust Qty').value if hasattr(row.get('Adjust Qty'), 'value') else read_text(row.get('Adjust Qty'))) or 0),
                    'Undersize Holes': (row.get('Undersize Holes').value if row.get('Undersize Holes') else read_text(row.get('Undersize Holes'))),
                    'Drill Template': bool(row.get('Drill Template').value) if row.get('Drill Template') else False,
                    'Process': row.get('Process').value if row.get('Process') else read_text(row.get('Process')),
                    'Supplier': row.get('Supplier').value if row.get('Supplier') else read_text(row.get('Supplier')),
                    'Notes': 'Example: Exceeds bed size',
                }
                updated_data.append(updated)

            with open('updated_data.json', 'w') as f:
                json.dump(updated_data, f, indent=4)
            ui.notify('Saved updates to updated_data.json')

        # ===== header ========================================================
        with ui.card().classes('w-full'):
            ui.label('Parts for export:').classes('text-lg font-semibold')
            with ui.row().classes('w-full font-bold'):            
                for col in data[0].keys():
                    if col in ['Thickness', 'Quantity', 'Adjust Qty', 'Drill Template']:
                        ui.label(col).classes('flex-[0.5] p-1')
                    elif col == 'Notes':
                        ui.label(col).classes('flex-[2] p-1')
                    else:
                        ui.label(col).classes('flex-1 p-1')
                ui.label('Notes').classes('flex-[2] p-1')

            # ===== existing rows =================================================

            for row in data:
                add_row_ui(row)

        # ===== add-configuration panel ======================================

        ui.separator().classes('my-2')

        part_numbers = sorted({str(r.get('Part Number')) for r in data if r.get('Part Number')})
        with ui.card().classes('w-full'):
            ui.label('Add configuration').classes('text-lg font-semibold')

            with ui.row().classes('w-full items-end gap-3'):
                sel_part = ui.select(
                    options=part_numbers,
                    label='Part Number',
                    clearable=False,
                ).classes('flex-1 p-1')

                inp_thk = ui.number(label='Thickness', value=None, min=0, step=1).classes('flex-1 p-1')
                inp_qty = ui.number(label='Quantity', value=None, min=0, step=1).classes('flex-1 p-1')
                sel_mat = ui.select(options=material_list, label='Material', clearable=False).classes('flex-1 p-1')
               

                def do_add():
                    if not sel_part.value:
                        ui.notify('Pick a Part Number', color='negative'); return
                    if inp_thk.value in (None, ''):
                        ui.notify('Enter Thickness', color='negative'); return
                    if inp_qty.value in (None, ''):
                        ui.notify('Enter Quantity', color='negative'); return
                    if not sel_mat.value:
                        ui.notify('Pick a Material', color='negative'); return

                    # inherit baseline fields from first matching existing row
                    base = next((r for r in data if str(r.get('Part Number')) == str(sel_part.value)), {})
                    new_row = {
                        'Part Number': str(sel_part.value),
                        'Thickness': str(int(inp_thk.value)),
                        'Material': sel_mat.value,
                        'Quantity': int(inp_qty.value),
                        'Adjust Qty': int(base.get('Adjust Qty', 0) or 0),
                        'Undersize Holes': base.get('Undersize Holes', undersize_options[0] if undersize_options else 'Ignore'),
                        'Process': base.get('Process', ''),
                        'Drill Template': bool(base.get('Drill Template', False)),
                        'Supplier': base.get('Supplier', ''),
                        # 'Notes' is visual-only in header; we keep consistent shape via save
                    }

                    # append to UI and in-memory list
                    data.append(new_row)
                    add_row_ui(new_row)
                    ui.notify(f"Added configuration for {new_row['Part Number']}")

                    # reset inputs (keep same part for rapid entry)
                    inp_thk.value = None
                    inp_qty.value = None
                    sel_mat.value = None

                ui.button('Add', on_click=do_add).classes('min-w-[6rem]')

            # Optional: save button here too (keeps your original flow)
            ui.button('Save all changes', on_click=lambda: process_data()).classes('mt-3')

    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        if exc_tb:
            print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()
