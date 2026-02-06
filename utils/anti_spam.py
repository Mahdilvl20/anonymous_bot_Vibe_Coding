import time

# ذخیره زمان آخرین پیام کاربران
last_message_times = {}

def is_spaming(user_id: int, limit: float = 2.0) -> bool:
    """
    بررسی اسپم با دقت میلی‌ثانیه.
    اگر فاصله کمتر از limit باشد، True برمی‌گرداند.
    """
    current_time = time.time()
    last_time = last_message_times.get(user_id, 0)
    
    if current_time - last_time < limit:
        return True
    
    last_message_times[user_id] = current_time
    return False