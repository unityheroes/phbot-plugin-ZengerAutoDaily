from phBot import *
from threading import Timer
from time import gmtime, strftime
import QtBind, struct

# ==================== Configuration ====================
YEAR = 25            # Two-digit year (e.g., 25 for 2025)
START_MONTH = 5      # Start month (1-12) for script to run
END_MONTH = 12       # End month (1-12) for script to run

# ==================== Reward Toggles ====================
CLAIM_SCROLL = True              # Reverse Scroll (ID=1)
CLAIM_RESURRECT_SCROLL = True    # Resurrection Scroll (ID=2)
CLAIM_PANDORA_BOX = True         # Pandora's Box (ID=3)
CLAIM_GLOBAL_CHAT = True         # Global Chatting (ID=4)
CLAIM_EXTENSION_GEAR = True      # Extension Gear (ID=5)
CLAIM_CLOCK_REINC = True         # Clock of Reincarnation 7d (ID=6)
CLAIM_PREMIUM = True             # Premium 7d (ID=7)
CLAIM_HAMMER = False             # Repair Hammer (ID=8)

# ==================== GUI Setup ====================
gui = QtBind.init(__name__, "ZengerAutoDaily ")
QtBind.createLabel(gui, "ZengerSro - Daily Login & Bonus Rewards", 15, 11)
QtBind.createLabel(gui, " By Ahmed Atef – 29-June 2025", 15, 23)
# Buttons for attendance and individual rewards
btnAuto   = QtBind.createButton(gui, 'btnAuto_clicked',   "  Auto Check-In  ", 15, 35)
btnScroll = QtBind.createButton(gui, 'btnScroll_clicked', "  Get Rev Scroll  ", 15, 65)
btnRS     = QtBind.createButton(gui, 'btnRS_clicked',     "  Get Resurrect Scroll  ", 15, 95)
btnPandora= QtBind.createButton(gui, 'btnPandora_clicked',"  Get Pandora's Box  ", 15, 125)
btnGlobal= QtBind.createButton(gui, 'btnGlobal_clicked', "  Get Global Chat  ", 15, 155)
btnExtend= QtBind.createButton(gui, 'btnExtend_clicked', "  Get Extension Gear  ", 15, 185)
btnClock = QtBind.createButton(gui, 'btnClock_clicked',  "  Get Clock Reinc 7d  ", 15, 215)
btnPremium=QtBind.createButton(gui, 'btnPremium_clicked',"  Get Premium 7d  ", 15, 245)
btnHammer = QtBind.createButton(gui, 'btnHammer_clicked', "  Get Repair Hammer  ", 15, 275)
lblStatus = QtBind.createLabel(gui, "Status: Disconnected", 15, 315)
QtBind.createLabel(gui, "Configure YEAR, START_MONTH, END_MONTH and toggles for each reward.", 18, 350)


# ==================== Global State ====================
is_connected = False
# Initialize all reward flags as not claimed
rewards_claimed = {i: False for i in range(1, 9)}

# ==================== Event Handlers ====================

def connected():
    global is_connected, rewards_claimed
    is_connected = False
    rewards_claimed = {i: False for i in range(1, 9)}
    QtBind.setText(gui, lblStatus, "Status: Disconnected")


def joined_game():
    global is_connected
    if get_locale() in [18, 65, 52, 56]:
        is_connected = True
        QtBind.setText(gui, lblStatus, "Status: Connected")
        Timer(10.0, start_auto_sequence).start()


def handle_joymax(opcode, data):
    if opcode == 0xB4DD and data[0] == 0x02 and data[1] == 0x01:
        log("[SUCCESS] Attendance checked!")
        start_reward_claim()
        return True
    if opcode == 0xB034 and data[0] == 0x01 and len(data) >= 12:
        item_id = struct.unpack_from('<I', data, 8)[0]
        info = get_item(item_id)
        name = info['name'] if info else f"ID {item_id}"
        log(f"[REWARD] Received: {name}")
        return True
    return True


def validate_date():
    now = gmtime()
    yy = int(strftime('%y', now))
    mm = int(strftime('%m', now))
    return yy == YEAR and START_MONTH <= mm <= END_MONTH


def start_auto_sequence():
    if not is_connected or not validate_date(): return
    send_packet(0x74DD, bytearray([0x01]), 1.0)
    send_packet(0x74DD, bytearray([0x02]), 3.0)
    Timer(10.0, start_reward_claim).start()


def start_reward_claim():
    if not is_connected: return
    # Check each toggle and schedule claim
    if CLAIM_SCROLL:          Timer(2.0, claim_reward, args=(1,)).start()
    if CLAIM_RESURRECT_SCROLL:Timer(4.0, claim_reward, args=(2,)).start()
    if CLAIM_PANDORA_BOX:     Timer(6.0, claim_reward, args=(3,)).start()
    if CLAIM_GLOBAL_CHAT:     Timer(8.0, claim_reward, args=(4,)).start()
    if CLAIM_EXTENSION_GEAR:  Timer(10.0, claim_reward, args=(5,)).start()
    if CLAIM_CLOCK_REINC:     Timer(12.0, claim_reward, args=(6,)).start()
    if CLAIM_PREMIUM:         Timer(14.0, claim_reward, args=(7,)).start()
    if CLAIM_HAMMER:          Timer(16.0, claim_reward, args=(8,)).start()


def send_packet(opcode, data, delay=0.0):
    if delay > 0:
        Timer(delay, inject_joymax, (opcode, data, False)).start()
    else:
        inject_joymax(opcode, data, False)


def claim_reward(item_id):
    global rewards_claimed
    if not is_connected or rewards_claimed.get(item_id, True): return
    send_packet(0x74DD, bytearray([0x01]), 0.0)
    send_packet(0x74DD, bytearray([0x03]), 1.0)
    send_packet(0x74DD, bytearray([0x04]) + struct.pack('<I', item_id), 2.0)
    packet = bytearray([0x05]) + struct.pack('<I', item_id) + struct.pack('<I', 1)
    send_packet(0x74DD, packet, 3.5)
    rewards_claimed[item_id] = True
    log(f"[AUTO] Claimed reward ID={item_id}")

# ==================== Button Callbacks ====================

def btnAuto_clicked():
    if is_connected: Timer(5.0, start_auto_sequence).start()

def btnScroll_clicked():
    if CLAIM_SCROLL: claim_reward(1)

def btnRS_clicked():
    if CLAIM_RESURRECT_SCROLL: claim_reward(2)

def btnPandora_clicked():
    if CLAIM_PANDORA_BOX: claim_reward(3)

def btnGlobal_clicked():
    if CLAIM_GLOBAL_CHAT: claim_reward(4)

def btnExtend_clicked():
    if CLAIM_EXTENSION_GEAR: claim_reward(5)

def btnClock_clicked():
    if CLAIM_CLOCK_REINC: claim_reward(6)

def btnPremium_clicked():
    if CLAIM_PREMIUM: claim_reward(7)

def btnHammer_clicked():
    if CLAIM_HAMMER: claim_reward(8)

# Plugin loaded
log("[ZengerAutoDaily] V2 plugin loaded successfully!")
