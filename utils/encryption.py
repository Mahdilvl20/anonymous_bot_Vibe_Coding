import hashlib

def get_anonymous_id(user_id: int, salt: str) -> str:
    # ۱. ترکیب آیدی واقعی کاربر با کلمه نمک (Salt) که در فایل env گذاشتی
    raw_string = f"{user_id}:{salt}"
    
    # ۲. تبدیل متن به بایت و هش کردن با الگوریتم SHA-256
    hash_obj = hashlib.sha256(raw_string.encode())
    
    # ۳. برگرداندن ۸ کاراکتر اول هش به عنوان آیدی مجازی (مثلاً: a1b2c3d4)
    return hash_obj.hexdigest()[:8]