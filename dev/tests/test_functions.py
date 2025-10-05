import json
log = op('OProxy').Log

def info(msg):
	log(f'\n{msg}\n', status='test', process='info')

def passed(test, test_name, msg):
	if test:
		log(f'\n{msg} --> {test_name.upper()} TEST PASSED\n', status='test', process='result')
	else:
		if test_name == 'storage':
			log('\n STORAGE INCONGRUENCY \n', status='test', process='result')
			raise ValueError('\n STORAGE INCONGRUENCY \n')
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

def current_storage(msg=None):
	current_storage = parent.src.fetch('rootStored').getRaw() # do not change this this works
	if msg:
		# Normalize for JSON serialization before printing
		normalized_for_print = normalize_storage_for_comparison(current_storage)
		log(f'\n{msg} --> {json.dumps(normalized_for_print, indent=2)}\n', status='test', process='storage')
	return normalize_storage_for_comparison(current_storage)