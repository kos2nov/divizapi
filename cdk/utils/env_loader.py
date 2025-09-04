import os
from pathlib import Path
from typing import Dict, Optional

def load_env_file(env_file: str = '.env') -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    Returns a dictionary of key-value pairs.
    """
    env_path = Path(env_file)
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
        
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            not (line.startswith('#') or '=' not in line) and (
                key_value := line.split('=', 1)
            ) and env_vars.update({key_value[0].strip(): key_value[1].strip('"\' ')})
    
    return env_vars

def get_env() -> Dict[str, str]:
    """
    Get environment variables, loading from .env file if it exists.
    Environment variables already set take precedence over .env file values.
    """
    env_vars = {}
    
    # Load from .env file first
    env_vars.update(load_env_file())
    
    # Override with actual environment variables
    env_vars.update(os.environ)
    
    return env_vars
