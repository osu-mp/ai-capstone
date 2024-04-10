from datetime import datetime
import pytz

def mst_to_utc_with_dst(mst_datetime_str, date_format="%Y-%m-%d"):
    mst_timezone = pytz.timezone('America/Denver')  # MST timezone
    mst_datetime = datetime.strptime(mst_datetime_str, f"{date_format} %H:%M:%S")
    mst_datetime = mst_timezone.localize(mst_datetime, is_dst=None)  # Handling ambiguous times
    utc_timezone = pytz.utc
    utc_datetime = mst_datetime.astimezone(utc_timezone)
    return utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

# Example usage
mst_datetime_str = "2024-04-09 10:30:00"  # MST datetime string
utc_timestamp = mst_to_utc_with_dst(mst_datetime_str)
print("UTC Timestamp:", utc_timestamp)
