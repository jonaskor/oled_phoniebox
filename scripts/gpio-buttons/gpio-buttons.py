#!/usr/bin/env python3
"""
GPIO buttons for OLED Phoniebox — Bookworm-safe version.

This file does NOT force a gpiozero pin factory (no RPiGPIOFactory forcing).
It adds a software debounce wrapper for when_pressed handlers so the rapid
spurious edges produced by some backends are filtered out while keeping
when_held behavior intact.
"""

import time
from time import sleep
from subprocess import check_call
from signal import pause

from gpiozero import Button

# Path to phoniebox/jukebox scripts (adjust if different in your install)
jukebox4kidsPath = "/home/pi/RPi-Jukebox-RFID"

# --- action functions ------------------------------------------------------
def def_volU():
    check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=volumeup", shell=True)

def def_volD():
    check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=volumedown", shell=True)

def def_vol0():
    check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=mute", shell=True)

def def_next():
    for x in range(0, 19):
        if btn_next.is_pressed:
            sleep(0.1)
        else:
            check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=playernext", shell=True)
            break

def def_contrastup():
    if btn_prev.is_pressed:
        check_call("/usr/bin/touch /tmp/o4p_overview.temp", shell=True)
    else:
        check_call("/usr/bin/python3 /home/pi/oled_phoniebox/scripts/contrast/contrast_up.py", shell=True)

def def_contrastdown():
    if btn_next.is_pressed:
        check_call("/usr/bin/touch /tmp/o4p_overview.temp", shell=True)
    else:
        check_call("/usr/bin/python3 /home/pi/oled_phoniebox/scripts/contrast/contrast_down.py", shell=True)

def def_prev():
    for x in range(0, 19):
        if btn_prev.is_pressed:
            sleep(0.1)
        else:
            check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=playerprev", shell=True)
            break

def def_halt():
    for x in range(0, 19):
        if btn_halt.is_pressed:
            sleep(0.1)
        else:
            check_call(jukebox4kidsPath + "/scripts/playout_controls.sh -c=playerpause", shell=True)
            break

def toggle_display():
    check_call("/home/pi/oled_phoniebox/scripts/toggle_display/toggle_display.sh", shell=True)

# --- software debounce wrapper --------------------------------------------
# We use a timestamp filter keyed by pin number so the first event runs
# and further events within DEBOUNCE_MS are ignored. This is backend-agnostic.
_last_event = {}
DEBOUNCE_MS = 120  # milliseconds: tune between 60..200 depending on your tests

def debounce_by_pin(pin_number, fn, debounce_ms=DEBOUNCE_MS):
    def wrapped(*a, **k):
        now = int(time.time() * 1000)
        last = _last_event.get(pin_number, 0)
        if now - last < debounce_ms:
            # ignore as bounce/duplicate
            return
        _last_event[pin_number] = now
        try:
            return fn(*a, **k)
        except Exception:
            # prevent exception from killing the service; let it be visible in journal
            import traceback
            traceback.print_exc()
    return wrapped

# --- Buttons configuration -----------------------------------------------
# Keep pull_up and hold_time/hold_repeat behaviour from original script.
# We do NOT force a pin factory here (so it will use the distro/default one).
# You can increase bounce_time if desired, but the debounce wrapper will be the main defense.
btn_volup = Button(7, pull_up=True, hold_time=0.3, hold_repeat=True, bounce_time=0.01)
btn_voldown = Button(13, pull_up=True, hold_time=0.3, hold_repeat=True, bounce_time=0.01)
btn_next = Button(8, pull_up=True, hold_time=2.0, hold_repeat=False, bounce_time=0.01)
btn_prev = Button(27, pull_up=True, hold_time=2.0, hold_repeat=False, bounce_time=0.01)
btn_halt = Button(12, pull_up=True, hold_time=2.0, hold_repeat=False, bounce_time=0.01)

# Attach handlers: wrap only the when_pressed handlers (keep when_held direct)
btn_volup.when_pressed = debounce_by_pin(7, def_volU)
btn_volup.when_held = def_volU

btn_voldown.when_pressed = debounce_by_pin(13, def_volD)
btn_voldown.when_held = def_volD

btn_next.when_pressed = debounce_by_pin(8, def_next)
btn_next.when_held = def_contrastup

btn_prev.when_pressed = debounce_by_pin(27, def_prev)
btn_prev.when_held = def_contrastdown

btn_halt.when_pressed = debounce_by_pin(12, def_halt)
btn_halt.when_held = toggle_display

pause()
