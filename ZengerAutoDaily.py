from phBot import *
from threading import Timer
from time import gmtime, strftime
import QtBind, struct

YEAR = 25    #change year 
START_MONTH = 5 #change start 
END_MONTH = 31  # change end 

# Initialize GUI
gui = QtBind.init(__name__, "ZengerAutoDaily")
QtBind.createLabel(gui, "ZengerSro - Daily Login Rewards System", 21, 11)
btnAuto   = QtBind.createButton(gui, 'btnAuto_clicked',   "  Auto Check-In  ", 21, 33)
btnScroll = QtBind.createButton(gui, 'btnScroll_clicked', "  Get Reverse Scroll  ", 21, 65)
btnHammer = QtBind.createButton(gui, 'btnHammer_clicked', "  Get Repair Hammer  ", 21, 95)
lblStatus = QtBind.createLabel(gui, "Status: Disconnected", 21, 130)
QtBind.createLabel(gui, "it work Automatic after login make check-in + get reverse + hummer only just put it in plugin ,  ", 25, 170)
QtBind.createLabel(gui, "and change start month and end month and year in code line 7/8/9  some mounth end 28 or 29 or 31 to work with Calendar check in ,  ", 25, 200)
QtBind.createLabel(gui, "ZengerSro - Made By Ahmed Atef [May 2025] ", 21, 280)

# Global states
is_connected     = False
rewards_claimed  = {1: False, 8: False}  # IDs: 1=Scroll, 8=Hammer

def connected():
    global is_connected, rewards_claimed
    is_connected = False
    rewards_claimed = {1: False, 8: False}
    QtBind.setText(gui, lblStatus, "Status: Disconnected")

def joined_game():
    global is_connected
    if get_locale() in [18, 65, 52, 56]:
        is_connected = True
        QtBind.setText(gui, lblStatus, "Status: Connected")
        start_auto_sequence()

def handle_joymax(opcode, data):
    # Attendance confirmation
    if opcode == 0xB4DD and data[0] == 0x02 and data[1] == 0x01:
        log("[SUCCESS] Attendance checked!")
        # هنا نستدعي استلام الجوائز بعد التأكد من الحضور
        start_reward_claim()
        return True

    # Reward reception
    if opcode == 0xB034 and data[0] == 0x01:
        if len(data) >= 12:
            item_id = struct.unpack_from("<i", data, 8)[0]
            item_info = get_item(item_id)
            if item_info:
                log(f"[REWARD] Received: {item_info['name']}")
            else:
                log(f"[REWARD] Received unknown item with ID: {item_id}")
        return True

    return True

def start_auto_sequence():
    """تسلسل تلقائي: تسجيل الحضور ثم استلام الجوائز."""
    if not validate_date():
        return
    # 1) تسجيل الحضور
    send_packet(0x74DD, bytearray([0x01]), 1.0)
    send_packet(0x74DD, bytearray([0x02]), 3.0)
    # 2) بعد تأكيد الحضور (نفس التأخير التقريبي) استدعاء استلام الجوائز
    Timer(5.0, start_reward_claim).start()

def start_reward_claim():
    """ابدأ جدولة استلام كل جائزة."""
    if not is_connected:
        return
    # جدول زمني لاستلام الجوائز
    Timer(0.0, claim_reward, args=(1,)).start()   # Reverse Scroll فورًا
    Timer(7.0, claim_reward, args=(8,)).start()   # Repair Hammer بعد 7 ثوانٍ

def send_packet(opcode, data, delay=0.0):
    if delay > 0:
        Timer(delay, inject_joymax, (opcode, data, False)).start()
    else:
        inject_joymax(opcode, data, False)

def validate_date():
    date = gmtime()
    yy = int(strftime("%y", date))
    mm = int(strftime("%m", date))
    return yy == YEAR and START_MONTH <= mm <= END_MONTH

def claim_reward(item_id):
    """Generic function to claim a reward by its ID."""
    global is_connected, rewards_claimed
    if not is_connected or rewards_claimed[item_id]:
        return

    # 1) افتح نافذة الجوائز
    send_packet(0x74DD, bytearray([0x01]), 0.0)
    # 2) اذهب للصفحة الثانية
    send_packet(0x74DD, bytearray([0x03]), 1.0)
    # 3) اختر الجائزة
    send_packet(0x74DD, bytearray([0x04]) + struct.pack('<i', item_id), 2.0)
    # 4) استلم الجائزة
    packet = bytearray([0x05]) \
           + struct.pack('<i', item_id) \
           + struct.pack('<i', 1)
    send_packet(0x74DD, packet, 3.5)

    rewards_claimed[item_id] = True
    log(f"[AUTO] Claimed reward ID={item_id}")

# Buttons
def btnAuto_clicked():
    if is_connected:
        start_auto_sequence()

def btnScroll_clicked():
    claim_reward(1)

def btnHammer_clicked():
    claim_reward(8)

log("[ZengerAutoDaily] Plugin loaded successfully!")
