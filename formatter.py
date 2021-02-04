def safe_strftime(d, format_str='%Y-%m-%d %H:%M:%S') -> str:
    try:
        return d.strftime(format_str)
    except Exception:
        return ''
