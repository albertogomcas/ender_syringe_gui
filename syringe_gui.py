import dearpygui.dearpygui as dpg
import serial
import serial.tools.list_ports
import math

TARGET_VID = 0x1EAF  # 7855 decimal
TARGET_PID = 0x0004  # 4 decimal

ser = None  # global serial connection


def apply_calibration():
    """No need to call this function every time, just once."""
    current = 400  # mA
    if ser and ser.is_open:
        ser.write(f"M906 X{current} Y{current} Z{current} E{current} H20\n".encode())
        log(f"[INFO] Applied current limit calibration: {current} mA")
        ser.write(b"M92 Z400\n")  # steps/mm with the ender Z screw
        log(f"[INFO] Applied steps/mm calibration: 400 steps/mm")
        ser.write(b"M500\n")  # Save to EEPROM
        log(f"[INFO] Saved calibration to EEPROM")

def find_serial_device(vid, pid):
    """Find the first serial port with matching VID and PID."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == vid and port.pid == pid:
            return port.device
    return None

def connect_serial():
    global ser
    port_name = find_serial_device(TARGET_VID, TARGET_PID)
    if port_name:
        try:
            ser = serial.Serial(port_name, baudrate=115200, timeout=1)
            log(f"[OK] Connected to {port_name} (VID={TARGET_VID}, PID={TARGET_PID})")
        except Exception as e:
            log(f"[ERROR] Failed to open {port_name}: {e}")
    else:
        log(f"[WARN] No device found with VID={TARGET_VID}, PID={TARGET_PID}")

def update_calculations(sender=None, app_data=None):
    """Update expected distance and time."""
    diameter = dpg.get_value("Diameter")  # mm
    flow_rate = dpg.get_value("Speed")    # mL/min
    volume = dpg.get_value("Volume")      # mL

    radius = diameter / 2.0
    area = math.pi * (radius ** 2)

    # Distance in mm
    distance_mm = (volume * 1000.0) / area

    # Time in seconds
    if flow_rate > 0:
        time_s = (volume / flow_rate) * 60
    else:
        time_s = float('inf')

    dpg.set_value("DistanceTimeText", f"{distance_mm:.2f}mm in {time_s:.1f}s ({distance_mm/time_s:.2f} mm/s)")

def start_callback(sender, app_data):
    if ser and ser.is_open:
        diameter = dpg.get_value("Diameter")  # mm
        flow_rate = dpg.get_value("Speed")    # mL/min
        volume = dpg.get_value("Volume")      # mL

        # Cross-sectional area of syringe (mm²)
        radius = diameter / 2.0
        area = math.pi * (radius ** 2)

        # Travel distance (mm)
        distance_mm = (volume * 1000.0) / area

        # Speed in mm/s
        speed_mms = (flow_rate * 1000.0) / (60.0 * area)

        # Build relative G-code
        gcode = f"G92 Z0\nG91\nG1 Z{distance_mm:.3f} F{speed_mms*60:.1f}\nG90\n"

        ser.write(gcode.encode())
        log(f"[INFO] Sent G-code")
    else:
        log("[WARN] Serial not connected!")

def move10(direction):
    speed = 1000
    if ser and ser.is_open:

        if direction == "forward":
            distance_mm = 10
        elif direction == "backward":
            distance_mm = -10
        gcode = f"G92 Z0\nG91\nG1 Z{distance_mm:.3f} F{speed}\nG90\n"
        ser.write(gcode.encode())
    else:
        log("[WARN] Serial not connected!")

def disable_steppers_callback(sender, app_data):
    if ser and ser.is_open:
        ser.write(b"M18\n")  # or M84
        log("[INFO] Motor is off")
    else:
        log("[WARN] Serial not connected!")

def stop_callback(sender, app_data):
    if ser and ser.is_open:
        ser.write(b"M410\n")
        log("[STOP] Sent stop (M410)")
        ser.write(b"M18\n")
    else:
        log("[WARN] Serial not connected!")

def log(msg):
    """Append a line to the log."""
    old_text = dpg.get_value("LogText")
    new_text = f"{old_text}\n{msg}" if old_text else msg
    dpg.set_value("LogText", new_text)
    dpg.add_spacer(height=1, parent="LogChild")
    dpg.set_y_scroll("LogChild", dpg.get_y_scroll_max("LogChild"))

# --- DearPyGui Setup ---
dpg.create_context()
with dpg.font_registry():
    font = dpg.add_font("C:\\Windows\\Fonts\\seguisym.ttf", 24)  # 24pt font
dpg.bind_font(font)
dpg.create_viewport(title="Syringe GUI 0.0.1\t\t Alberto Gomez-Casado", width=600, height=550)
dpg.setup_dearpygui()

with dpg.window(label="", no_title_bar=True, pos=[0,0], width=600, height=550, no_move=True, no_resize=True):
    dpg.add_text("Positioning:")
    with dpg.group(horizontal=True):
        dpg.add_button(label="-10 mm", callback=lambda x: move10("backward"))
        dpg.add_button(label="Free motor", callback=disable_steppers_callback)
        dpg.add_button(label="+10 mm", callback=lambda x: move10("forward"))

    dpg.add_spacer(height=25)
    dpg.add_separator()
    dpg.add_text("Injection parameters:")
    dpg.add_input_float(label="Syringe diameter (mm)", default_value=20.0, step=1.0, format="%.2f", tag="Diameter", width=200)
    dpg.add_input_float(label="Flow rate (mL/min)", default_value=5.0, step=0.1, format="%.2f", tag="Speed", width=200)
    dpg.add_input_float(label="Dispense volume (mL)", default_value=1.0, step=0.1, format="%.2f", tag="Volume", width=200)
    with dpg.group(horizontal=True):
        dpg.add_text("", tag="DistanceTimeText")

    dpg.add_spacer(height=10)  # 10 pixels vertical spacing
    with dpg.group(horizontal=True):
        dpg.add_button(label="Start", callback=start_callback, width=150, height=50)
        dpg.add_button(label="Stop", callback=stop_callback, width=150, height=50)

    dpg.add_spacer(height=10)
    dpg.add_separator()

    for tag in ["Diameter", "Speed", "Volume"]:
        dpg.set_item_callback(tag, update_calculations)


    with dpg.child_window(width=-1, height=90, border=True, tag="LogChild"):
        dpg.add_text("", tag="LogText", wrap=-1)  # empty at start

log("[INFO] GUI started")
# Try connecting when the GUI starts
connect_serial()
#apply_calibration()
dpg.show_viewport()
update_calculations()
dpg.start_dearpygui()
dpg.destroy_context()

# Close serial on exit
if ser and ser.is_open:
    ser.close()
