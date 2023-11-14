from pynput import keyboard, mouse
from pynput.mouse import Button
from queue import Queue
import threading
import time
import json
import argparse

import pyautogui


# Queues for mouse and keyboard events
keyboard_events = Queue()
mouse_events = Queue()

start_time = time.time()

stop_threads = False  # Shared flag to signal the worker threads to stop

def keyboard_worker():
    global stop_threads
    """ Worker for processing keyboard events """
    while not stop_threads:
        key, is_pressed = keyboard_events.get()
        if is_pressed:
            event = {"type": "keyboard", "key": str(key), "action": "press"}
        else:
            event = {"type": "keyboard", "key": str(key), "action": "release"}
            if key == keyboard.Key.esc:
                stop_threads = True
        with open('events-' + str(start_time)+'.txt', 'a') as f:
            f.write(json.dumps(event) + '\n')

def mouse_worker():
    global stop_threads
    """ Worker for processing mouse events """
    while not stop_threads:
        x, y, button, is_pressed = mouse_events.get()
        action = "press" if is_pressed else "release"
        event = {"type": "mouse", "x": x, "y": y, "button": str(button), "action": action}
        with open('events-' + str(start_time)+'.txt', 'a') as f:
            f.write(json.dumps(event) + '\n')

def on_key_press(key):
    keyboard_events.put((key, True))

def on_key_release(key):
    keyboard_events.put((key, False))
    if key == keyboard.Key.esc:
        return False  # Stop the listener

def on_click(x, y, button, pressed):
    mouse_events.put((x, y, button, pressed))

def replay_events(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
        event = json.loads(line.strip())
        if event['type'] == 'keyboard':
            key = event['key'].replace("'", "")
            if 'Key.' in event['key']:
                key = event['key'].split('.')[1]
            if event['action'] == 'press':
                pyautogui.keyDown(key)
            else:
                pyautogui.keyUp(key)
        else:
            x, y = event['x'], event['y']
            button = event['button'].split('.')[1]
            if event['action'] == 'press':
                pyautogui.mouseDown(x, y, button)
            else:
                pyautogui.mouseUp(x, y, button)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay', help='The filename of the events to replay')
    args = parser.parse_args()

    if args.replay:
        replay_events(args.replay)
    else:
        # Set up workers for processing the input events
        threading.Thread(target=keyboard_worker, daemon=True).start()
        threading.Thread(target=mouse_worker, daemon=True).start()

        # Set up listeners that add events to the queues
        with mouse.Listener(on_click=on_click) as mouse_listener, \
             keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as keyboard_listener:
            keyboard_listener.join()  # Block until 'Esc' is released
            mouse_listener.join()  # Note: This join is never reached in practice