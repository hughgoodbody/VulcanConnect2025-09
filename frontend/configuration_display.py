from nicegui import ui
def configuration_display(results, ui_state):

    with ui.tabs().classes('w-full') as tabs:
        ui_state.results_tab = ui.tab('Configuration Results')            

    with ui.tab_panels(tabs).classes('w-full'):
        with ui.tab_panel(ui_state.results_tab):
            parameters = results.get('configurationParameters', [])
            #parameters = None
            if not parameters:
                with ui_state.results_tab:
                    ui.label('⚠️ No configuration parameters found.')
                return
            with ui_state.results_tab:
                ui.label('CONFIGURATIONS:').classes('font-bold text-lg')
                with ui.row().classes('w-full gap-4 flex-nowrap') as config_row:
                    with ui.column().classes('w-1/3 gap-2') as enum_col:
                        ui.label('🔘 Enum Parameters').classes('font-bold')
                    with ui.column().classes('w-1/3 gap-2 items-center') as bool_col:
                        ui.label('☑️ Boolean Parameters').classes('font-bold')
                    with ui.column().classes('w-1/3 gap-2') as qty_col:
                        ui.label('📏 Quantity Parameters').classes('font-bold')      
                    
            for param in parameters:
                try:
                    type_name = param.get('btType')
                    name = param.get('parameterName', 'Unnamed')
                    param_id = param.get('parameterId', 'unknown')

                    if type_name.startswith('BTMConfigurationParameterEnum'):
                        options = [opt.get('optionName', 'Unnamed') for opt in param.get('options', [])]
                        with enum_col:
                            dropdown = ui.select(options=options, label=f"{name} (Enum)").classes('w-full')
                            ui_state.config_controls[param_id] = dropdown

                    elif type_name.startswith('BTMConfigurationParameterBoolean'):
                        default = param.get('defaultValue', False)
                        with bool_col:
                            checkbox = ui.checkbox(name, value=default)
                            ui_state.config_controls[param_id] = checkbox

                    elif type_name.startswith('BTMConfigurationParameterQuantity'):
                        range_msg = param.get('rangeAndDefault', {})
                        min_val = range_msg.get('minValue', 0)
                        max_val = range_msg.get('maxValue', 1000)
                        default_val = range_msg.get('defaultValue', min_val)
                        units = range_msg.get('units', 'mm')

                        with qty_col:
                            number = ui.number(label=f"{name} ({units})", value=default_val, min=min_val, max=max_val).classes('w-full')
                            ui_state.config_controls[param_id] = number
                    else:
                        with ui_state.results_tab:
                            ui.label(f"⚠️ Unsupported parameter type: {type_name}")

                except Exception as e:
                    with ui_state.results_tab:
                        ui.label(f"❌ Exception processing param: {e}")