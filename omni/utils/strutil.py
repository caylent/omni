def chunk_string_by_bytes(input_string: str, chunk_size: int) -> list:
    """
    Splits a string into chunks of a specified byte size.
    
    Args:
        input_string (str): The string to be split.
        chunk_size (int): The size of each chunk in bytes.
    """
    encoded_string = input_string.encode('utf-8')
    return [encoded_string[i:i+chunk_size].decode('utf-8', errors='ignore') for i in range(0, len(encoded_string), chunk_size)]
