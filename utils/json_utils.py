"""
JSON utility functions for handling special data types conversions.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Union

def json_serialize(obj: Any) -> Any:
    """
    Custom JSON serializer that handles pandas Timestamps, numpy types, datetimes, etc.
    
    Args:
        obj: The object to serialize
        
    Returns:
        JSON serializable version of the object
    """
    # Handle pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    # Handle numpy types
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, 
                        np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    # Handle Python's datetime types
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    # Handle Decimal
    elif isinstance(obj, Decimal):
        return float(obj)
    
    # Handle sets
    elif isinstance(obj, set):
        return list(obj)
    
    # Raise TypeError for anything else
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def make_json_serializable(data: Any) -> Any:
    """
    Recursively process a data structure to make all elements JSON serializable.
    
    Args:
        data: The data structure to process (dict, list, or single value)
        
    Returns:
        A JSON serializable version of the data structure
    """
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(make_json_serializable(item) for item in data)
    try:
        # Try standard JSON serialization first
        json.dumps(data)
        return data
    except (TypeError, OverflowError):
        # If that fails, try our custom serializer
        try:
            return json_serialize(data)
        except TypeError:
            # If all else fails, convert to string
            return str(data)

def to_serializable_dict(data: Dict) -> Dict:
    """
    Convert a dictionary to a JSON-serializable dictionary.
    
    Args:
        data: Dictionary to convert
        
    Returns:
        JSON-serializable dictionary
    """
    return make_json_serializable(data)