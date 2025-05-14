from phBot import *
from threading import Timer
from time import gmtime, strftime
import QtBind, struct

# ==================== Configuration ====================
YEAR = 25            # Two-digit year (e.g., 25 for 2025)
START_MONTH = 5      # Start month (1-12) for script to run
END_MONTH = 12       # End month (1-12) for script to run

# ==================== Reward Toggles ====================
CLAIM_SCROLL = True  # Claim Reverse Scroll
CLAIM_HAMMER = False # Claim Repair Hammer

# ==================== GUI Setup ====================
gui = QtBind.init(__name__, "ZengerAutoDaily")
QtBind.createLabel(gui, "ZengerSro - Daily Login Rewards System", 21, 11)
btnAuto   = QtBind.createButton(gui, 'btnAuto_clicked',   "  Auto Check-In  ", 21, 33)
btnScroll = QtBind.createButton(gui, 'btnScroll_clicked', "  Get Reverse Scroll  ", 21, 65)
btnHammer = QtBind.createButton(gui, 'btnHammer_clicked', "  Get Repair Hammer  ", 21, 95)
lblStatus = QtBind.createLabel(gui, "Status: Disconnected", 21, 130)
QtBind.createLabel(gui, "Configure YEAR, START_MONTH, END_MONTH and toggles below to select rewards.", 25, 170)
QtBind.createLabel(gui, "ZengerSro by Ahmed Atef (IGN: DarkFighter) – May 2025", 21, 280)

# ==================== Global State ====================
is_connected = False
rewards_claimed = {1: False, 8: False}


def connected():
    global is_connected, rewards_claimed
    is_connected = False
    rewards_claimed = {1: False, 8: False}
    QtBind.setText(gui, lblStatus, "Status: Disconnected")


def joined_game():
    global is_connected
    # Only enable for allowed locales
    if get_locale() in [18, 65, 52, 56]:
        is_connected = True
        QtBind.setText(gui, lblStatus, "Status: Connected")
        # Wait 10 seconds after login before starting check-in
        Timer(10.0, start_auto_sequence).start()


def handle_joymax(opcode, data):
    # Attendance confirmation packet
    if opcode == 0xB4DD and data[0] == 0x02 and data[1] == 0x01:
        log("[SUCCESS] Attendance checked!")
        start_reward_claim()
        return True
    # Reward reception packet
    if opcode == 0xB034 and data[0] == 0x01 and len(data) >= 12:
        # Unpack as unsigned to avoid negative IDs
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
    if not is_connected or not validate_date():
        return
    # Open attendance window after delay
    send_packet(0x74DD, bytearray([0x01]), 1.0)
    # Confirm attendance
    send_packet(0x74DD, bytearray([0x02]), 3.0)
    # After attendance, schedule rewards
    Timer(10.0, start_reward_claim).start()


def start_reward_claim():
    if not is_connected:
        return
    if CLAIM_SCROLL:
        Timer(2.0, claim_reward, args=(1,)).start()
    if CLAIM_HAMMER:
        Timer(7.0, claim_reward, args=(8,)).start()


def send_packet(opcode, data, delay=0.0):
    if delay > 0:
        Timer(delay, inject_joymax, (opcode, data, False)).start()
    else:
        inject_joymax(opcode, data, False)


def claim_reward(item_id):
    global rewards_claimed
    if not is_connected or rewards_claimed.get(item_id, True):
        return
    # Claim sequence
    send_packet(0x74DD, bytearray([0x01]), 0.0)
    send_packet(0x74DD, bytearray([0x03]), 1.0)
    send_packet(0x74DD, bytearray([0x04]) + struct.pack('<I', item_id), 2.0)
    packet = bytearray([0x05]) + struct.pack('<I', item_id) + struct.pack('<I', 1)
    send_packet(0x74DD, packet, 3.5)
    rewards_claimed[item_id] = True
    log(f"[AUTO] Claimed reward ID={item_id}")

# Button callbacks
def btnAuto_clicked():
    if is_connected:
        # Manual override, also wait 5s
        Timer(5.0, start_auto_sequence).start()

def btnScroll_clicked():
    if CLAIM_SCROLL:
        claim_reward(1)

def btnHammer_clicked():
    if CLAIM_HAMMER:
        claim_reward(8)

# Plugin loaded
log("[ZengerAutoDaily] Plugin loaded successfully!")
