from collections import defaultdict

def case_insensitive_dict(base_class=dict):
    ''' Factory function '''
    
    class CaseInsensitiveDict(base_class):
        '''
        A dictionary which allows case-insensitive lookups 
        
        Unlike the implementation in `requests` (see: https://github.com/
            requests/requests/blob/v1.2.3/requests/structures.py#L37)
        this also supports non-string keys
        '''    
        
        def __init__(self, *args, **kwargs):
            def lower_keys(item):
                if isinstance(item, dict):
                    return { k.lower():v for k, v in item.items() }
                return item
        
            if args:
                args = [lower_keys(i) for i in args]           
            if kwargs:
                kwargs = { k.lower():v for k, v in kwargs.items() }
                
            super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        
        def __setitem__(self, key, value):
            if isinstance(key, str):
                key = key.lower()        
            super(CaseInsensitiveDict, self).__setitem__(key, value)
            
        def __getitem__(self, key):
            if isinstance(key, str):
                key = key.lower()
            return super(CaseInsensitiveDict, self).__getitem__(key)
            
        def __delitem__(self, key):
            if isinstance(key, str):
                key = key.lower()
            super(CaseInsensitiveDict, self).__delitem__(key)
            
    return CaseInsensitiveDict
    
CaseInsensitiveDefaultDict = case_insensitive_dict(defaultdict)