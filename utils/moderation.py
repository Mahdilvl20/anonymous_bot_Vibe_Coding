import os

BLACKLIST_FILE = "blacklist.txt"

def ban_user(anon_id: str):
    with open(BLACKLIST_FILE, "a") as f:
        f.write(f"{anon_id}\n")

def is_banned(anon_id: str) -> bool:
    if not os.path.exists(BLACKLIST_FILE):
        return False
    with open(BLACKLIST_FILE, "r") as f:
        banned_ids = f.read().splitlines()
    return anon_id in banned_ids
def unban_user(anon_id: str):
    if not os.path.exists(BLACKLIST_FILE):
        return
    
    with open(BLACKLIST_FILE, "r") as f:
        lines = f.readlines()
    
    # بازنویسی فایل بدون آیدی مورد نظر
    with open(BLACKLIST_FILE, "w") as f:
        for line in lines:
            if line.strip("\n") != anon_id:
                f.write(line)