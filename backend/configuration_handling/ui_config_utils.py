from nicegui import ui
import sys
import traceback
from backend.configuration_handling.configHandler import get_configurations, encode_configuration_string
from nicegui.elements.number import Number

def get_configs(ui_state):
    ui_state.config_area.clear()
    ui_state.error_output.value = ''
    ui_state.config_controls.clear()

    doc_url = ui_state.url_input.value.strip()
    if not doc_url:
        ui_state.error_output.value = '❌ Please paste a valid URL.'
        return

    result = get_configurations(doc_url)

    if isinstance(result, dict) and 'Error' in result:
        ui_state.error_output.value = (
            f"❌ Error: {result['Error']}\n"
            f"🔗 API Call: {result['API Call']}\n"
            f"📄 Module: {result['Module']}\n"
            f"🔧 Function: {result['Function']}\n"
            f"📍 Line: {result['Line Number']}"
        )
        return

    parameters = result.get('configurationParameters', [])
    if not parameters:
        with ui_state.config_area:
            ui.label('⚠️ No configuration parameters found.')
        return

    with ui_state.config_area:
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
                with ui_state.config_area:
                    ui.label(f"⚠️ Unsupported parameter type: {type_name}")

        except Exception as e:
            with ui_state.config_area:
                ui.label(f"❌ Exception processing param: {e}")

def encode_config(ui_state):
    def extract_control_values():
        result = {}
        for param_id, element in ui_state.config_controls.items():
            try:
                value = element.value
                if isinstance(element, Number):
                    label = getattr(element, 'label', '')
                    if '(' in label and ')' in label:
                        unit = label.split('(')[-1].split(')')[0].strip()
                        value = f"{value}_{unit}"
                result[param_id] = value
            except Exception as e:
                result[param_id] = f"⚠️ Error reading value: {e}"
        return result

    config_values = extract_control_values()

    try:
        parameter_list = [
            {"parameterId": pid, "parameterValue": val}
            for pid, val in config_values.items()
            if not str(val).startswith("⚠️")
        ]

        if not parameter_list:
            ui.notify("⚠️ No valid configuration values found.")
            return

        doc_url = ui_state.url_input.value.strip()
        if not doc_url:
            ui.notify("❌ Document URL is missing.")
            return

        encoded = encode_configuration_string(doc_url, parameter_list)
        ui.notify(f"✅ Encoded Configuration String:\n{encoded}")
        ui_state.tabs.set_value(ui_state.results_tab)

    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()
        ui.notify(f"❌ Failed to encode: {e}", type='negative')