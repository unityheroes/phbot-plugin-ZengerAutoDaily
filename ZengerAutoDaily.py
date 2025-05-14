from phBot import *
from threading import Timer
from time import gmtime, strftime
import QtBind, struct

# ==================== Configuration ====================
YEAR = 25            # Two-digit year to validate (e.g., 25 for 2025)
START_MONTH = 5      # Beginning of allowed month day range (1 or date you start script)
END_MONTH = 31       # End of allowed month day range (28-31)

# ==================== Reward Toggles ====================
# Set to False to skip claiming the corresponding reward
CLAIM_SCROLL = True      # Reverse Scroll reward
CLAIM_HAMMER = False     # Repair Hammer reward

# ==================== GUI Setup ====================
# Initialize the plugin window
gui = QtBind.init(__name__, "ZengerAutoDaily")
QtBind.createLabel(gui, "ZengerSro - Daily Login Rewards System", 21, 11)
btnAuto   = QtBind.createButton(gui, 'btnAuto_clicked',   "  Auto Check-In  ", 21, 33)
btnScroll = QtBind.createButton(gui, 'btnScroll_clicked', "  Get Reverse Scroll  ", 21, 65)
btnHammer = QtBind.createButton(gui, 'btnHammer_clicked', "  Get Repair Hammer  ", 21, 95)
lblStatus = QtBind.createLabel(gui, "Status: Disconnected", 21, 130)
# Instructions: direct users to modify script variables
QtBind.createLabel(gui, "Configure YEAR, START_MONTH, and END_MONTH and use the toggles below to enable auto check-in and select which rewards to claim.", 25, 170)
# Updated: clearer in-script toggles description
QtBind.createLabel(gui, "In-script toggles: set CLAIM_SCROLL to claim Reverse Scroll and CLAIM_HAMMER to claim Repair Hammer.", 25, 200)
QtBind.createLabel(gui, "ZengerSro by Ahmed Atef (IGN: DarkFighter) – May 2025", 21, 280)

# ==================== Global State ====================
is_connected = False            # Tracks if the player is connected and in-game
rewards_claimed = {1: False, 8: False}  # Reward IDs: 1 = Scroll, 8 = Hammer


def connected():
    """
    Handle disconnect event: reset connection state and hide status.
    """
    global is_connected, rewards_claimed
    is_connected = False
    rewards_claimed = {1: False, 8: False}
    QtBind.setText(gui, lblStatus, "Status: Disconnected")


def joined_game():
    """
    Handle successful login into game: enable automation if locale matches.
    """
    global is_connected
    allowed_locales = [18, 65, 52, 56]
    if get_locale() in allowed_locales:
        is_connected = True
        QtBind.setText(gui, lblStatus, "Status: Connected")
        start_auto_sequence()


def handle_joymax(opcode, data):
    """
    Intercept Joymax packets:
      - Confirm attendance success and trigger reward claims
      - Log incoming reward items
    Returns True to indicate packet was handled.
    """
    # Check for attendance confirmation packet
    if opcode == 0xB4DD and data[0] == 0x02 and data[1] == 0x01:
        log("[SUCCESS] Attendance checked!")
        start_reward_claim()
        return True

    # Check for reward reception packet
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


def validate_date():
    """
    Ensure current date (YY and MM) is within configured range.
    Returns True if within YEAR and START_MONTH..END_MONTH.
    """
    now = gmtime()
    current_year = int(strftime("%y", now))
    current_month = int(strftime("%m", now))
    return current_year == YEAR and START_MONTH <= current_month <= END_MONTH


def start_auto_sequence():
    """
    Perform automatic attendance check and schedule reward claims.
    """
    if not validate_date():
        return
    # Send attendance packets with delays
    send_packet(0x74DD, bytearray([0x01]), 1.0)  # Open attendance window
    send_packet(0x74DD, bytearray([0x02]), 3.0)  # Confirm attendance
    # After attendance is confirmed, delay before claiming rewards
    Timer(5.0, start_reward_claim).start()


def start_reward_claim():
    """
    Schedule each reward claim according to toggles and fixed delays.
    """
    if not is_connected:
        return
    # Claim Reverse Scroll after 2 seconds if enabled
    if CLAIM_SCROLL:
        Timer(2.0, claim_reward, args=(1,)).start()
    # Claim Repair Hammer after 7 seconds if enabled
    if CLAIM_HAMMER:
        Timer(7.0, claim_reward, args=(8,)).start()


def send_packet(opcode, data, delay=0.0):
    """
    Inject Joymax packet after optional delay.
    """
    if delay > 0:
        Timer(delay, inject_joymax, (opcode, data, False)).start()
    else:
        inject_joymax(opcode, data, False)


def claim_reward(item_id):
    """
    Generic reward claim function:
      1) Open rewards window
      2) Navigate to second page
      3) Select specific reward by ID
      4) Receive the reward
    """
    global is_connected, rewards_claimed
    # Skip if not connected or already claimed
    if not is_connected or rewards_claimed[item_id]:
        return

    # Step 1: Open rewards UI
    send_packet(0x74DD, bytearray([0x01]), 0.0)
    # Step 2: Go to page 2 of rewards
    send_packet(0x74DD, bytearray([0x03]), 1.0)
    # Step 3: Select reward item
    send_packet(0x74DD, bytearray([0x04]) + struct.pack('<i', item_id), 2.0)
    # Step 4: Claim the reward
    packet = bytearray([0x05]) + struct.pack('<i', item_id) + struct.pack('<i', 1)
    send_packet(0x74DD, packet, 3.5)

    # Mark reward as claimed to prevent duplicate requests
    rewards_claimed[item_id] = True
    log(f"[AUTO] Claimed reward ID={item_id}")

# ==================== Button Callbacks ====================
def btnAuto_clicked():
    """Handler for manual 'Auto Check-In' button."""
    if is_connected:
        start_auto_sequence()


def btnScroll_clicked():
    """Handler for manual 'Get Reverse Scroll' button."""
    if CLAIM_SCROLL:
        claim_reward(1)


def btnHammer_clicked():
    """Handler for manual 'Get Repair Hammer' button."""
    if CLAIM_HAMMER:
        claim_reward(8)

# Notify successful plugin load
log("[ZengerAutoDaily] Plugin loaded successfully!")
