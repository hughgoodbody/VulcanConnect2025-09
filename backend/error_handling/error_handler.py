# Error handling

import traceback
import logging
import json

logging.basicConfig(filename='error.log', level=logging.ERROR)

def log_exception(base_url, api_path, module_name, function_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                line = tb[-1].lineno if tb else 'N/A'
                full_api_url = f"{base_url}{api_path}"
                error_info = {
                    'API Call': full_api_url,
                    'Error': str(e),
                    'Module': module_name,
                    'Function': function_name,
                    'Line Number': line,
                }
                logging.error(json.dumps(error_info, indent=2))
                return error_info
        return wrapper
    return decorator
