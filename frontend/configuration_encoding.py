from nicegui import ui
import sys
import traceback
from backend.configuration_handling.configHandler import encode_configuration_string
from nicegui.elements.number import Number

def encode_config(ui_state, update_notifier):
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
            update_notifier("⚠️ No valid configuration values found.")
            #ui.notify("⚠️ No valid configuration values found.")
            return

        doc_url = ui_state.url_input.strip()
        if not doc_url:
            #ui.notify("❌ Document URL is missing.")
            update_notifier("❌ Document URL is missing.")
            return

        encoded = encode_configuration_string(doc_url, parameter_list)
        #ui.notify(f"✅ Encoded Configuration String:\n{encoded}")
        update_notifier(f"✅ Encoded Configuration String:\n{encoded}")
        #ui_state.tabs.set_value(ui_state.results_tab)
        ui_state.config_string = encoded
        print(encoded)
        return encoded

    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()
        #ui.notify(f"❌ Failed to encode: {e}", type='negative')
        update_notifier(f"❌ Failed to encode: {e}", type='negative')