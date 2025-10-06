import json
import copy
log = op('OProxy').Log
utils = mod('OProxy/utils')

def info(msg):
	log(f'\n{msg}\n', status='test', process='info')

def passed(test_or_expected, test_name, msg):
    if test_name == '_storage() test 1':
        match = {
                "children": {
                    "items": {
                        "children": {},
                        "ops": {
                            "op1": {
                                "op": {
                                    "name": "op1",
                                    "type": "moviefileinTOP",
                                    "path": "/project1/myProject/op1"
                                },
                                "extensions": {}
                            },
                            "op2": {
                                "op": {
                                    "name": "op2",
                                    "type": "moviefileinTOP",
                                    "path": "/project1/myProject/op2"
                                },
                                "extensions": {}
                            },
                            "op3": {
                                "op": {
                                    "name": "op3",
                                    "type": "moviefileinTOP",
                                    "path": "/project1/myProject/op3"
                                },
                                "extensions": {}
                            }
                        },
                        "extensions": {}
                    }
                },
                "extensions": {}
            }
        test_result = test_or_expected == match

    if test_name == 'storage':
        import copy
        actual_storage = current_storage()
        expected_copy = copy.deepcopy(test_or_expected)

        # Handle dynamic timestamps in extensions
        _normalize_timestamps_for_comparison(actual_storage, expected_copy)

        test_result = actual_storage == expected_copy
        if test_result:
            log(f'\n{msg} --> {test_name.upper()} TEST PASSED\n', status='test', process='result')
            return True
        else:
            log('\n STORAGE INCONGRUENCY \n', status='test', process='result')
            # Log the actual vs expected for debugging
            log(f'Expected: {json.dumps(expected_copy, indent=2)}', status='test', process='debug')
            log(f'Actual: {json.dumps(actual_storage, indent=2)}', status='test', process='debug')
            raise ValueError('\n STORAGE INCONGRUENCY \n')
            
    if test_name == '_storage() test 1':
        if test_result:
            log(f'\n{msg} --> {test_name.upper()} TEST PASSED\n', status='test', process='_storage() test 1')
            return True
        else:
            log(f'\n{msg} --> {test_name.upper()} TEST FAILED\n', status='test', process='result')
            raise Exception(f'\n{msg} --> {test_name.upper()} TEST FAILED\n')
    else:
        # Handle regular boolean tests
        if test_or_expected:
            log(f'\n{msg} --> {test_name.upper()} TEST PASSED\n', status='test', process='result')
            return True
        else:
            log(f'\n{msg} --> {test_name.upper()} TEST FAILED\n', status='test', process='result')
            raise Exception(f'\n{msg} --> {test_name.upper()} TEST FAILED\n')
        
        

def normalize_storage_for_comparison(storage):
    """Normalize storage by replacing OP objects and extensions with placeholders for comparison."""
    if isinstance(storage, dict):
        normalized = {}
        for key, value in storage.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'OProxyExtension':
                normalized[key] = "<OPROXY_EXTENSION>"
            elif key == 'op' and hasattr(value, 'name'):  # It's an OP object
                normalized[key] = "<OP_OBJECT>"
            else:
                normalized[key] = normalize_storage_for_comparison(value)
        return normalized
    elif isinstance(storage, list):
        return [normalize_storage_for_comparison(item) for item in storage]
    else:
        # Convert JSON values to Python values for comparison
        if storage is None or str(storage).lower() == 'null':
            return None
        elif str(storage).lower() == 'false':
            return False
        elif str(storage).lower() == 'true':
            return True
        else:
            return storage

def _normalize_timestamps_for_comparison(actual_storage, expected_storage):
    """Normalize timestamps in expected storage to match actual storage for comparison."""
    def _normalize_recursive(actual, expected, path=""):
        if isinstance(actual, dict) and isinstance(expected, dict):
            for key in actual:
                if key in expected:
                    if key == 'created_at' and isinstance(actual[key], (int, float)):
                        # Copy timestamp from actual to expected
                        expected[key] = actual[key]
                    elif isinstance(actual[key], dict) and isinstance(expected[key], dict):
                        _normalize_recursive(actual[key], expected[key], f"{path}.{key}")
                    elif isinstance(actual[key], list) and isinstance(expected[key], list):
                        for i, (a_item, e_item) in enumerate(zip(actual[key], expected[key])):
                            if isinstance(a_item, dict) and isinstance(e_item, dict):
                                _normalize_recursive(a_item, e_item, f"{path}.{key}[{i}]")

    _normalize_recursive(actual_storage, expected_storage)

def current_storage(msg=None):
	current_storage = parent.src.fetch('rootStored').getRaw() # do not change this this works
	if msg:
		# Normalize for JSON serialization before printing
		normalized_for_print = normalize_storage_for_comparison(current_storage)
		log(f'\n{msg} --> {json.dumps(normalized_for_print, indent=2)}\n', status='test', process='storage')
	return normalize_storage_for_comparison(current_storage)
