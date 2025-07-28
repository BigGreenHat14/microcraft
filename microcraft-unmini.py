from microbit import *
class RunEvery:
    def __init__(self):
        self._tasks = []
    def add(self, callback, ms=0):
        if ms <= 0:
            raise ValueError("Interval must be greater than 0 milliseconds.")
        self._tasks.append({
            "interval": ms,
            "callback": callback,
            "last_run": running_time()
        })
    def update(self):
        now = running_time()
        for task in self._tasks:
            if now - task["last_run"] >= task["interval"]:
                task["last_run"] = now
                task["callback"]()
runner = RunEvery()
from math import floor
def play_frequency(freq,ms):
    import math, audio
    def generate_square_wave_frames(frequency, duration_ms):
        frames_needed = int((duration_ms / 1000) * 7812.5 / 32)
        for _ in range(frames_needed):
            frame = audio.AudioFrame()
            for i in range(32):
                t = i / 7812.5
                if math.sin(2 * math.pi * frequency * t) > 0:
                    sample = 255
                else:
                    sample = 0
                frame[i] = sample
            yield frame
    frames = list(generate_square_wave_frames(freq, ms))
    audio.play(frames, pin=None)
for pin in (pin8, pin13, pin14, pin15, pin16):pin.set_pull(pin.PULL_UP)
cbx, cby = pin2.read_analog(), pin1.read_analog()
def joystick_direction():
    x = round(((pin2.read_analog() - cbx) / 1023) * 9) + 5
    y = round(((pin1.read_analog() - cby) / 1023) * 9) + 5
    return {
        "left": x == 10,
        "right": x == 1,
        "up": y == 0,
        "down": y == 9
    }
def yellow_button():return pin16.read_digital() == 0
def inventory_button():return pin13.read_digital() == 0
def place_button():return pin15.read_digital() == 0
block_properties = BLOCKPROP
regions = []
cutouts = {}
def a(x, y, block_type):cutouts[(x, y)] = block_type
def f(x1, y1, x2, y2, block_type):regions.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), block_type))
def get_block_id(pos):
    if pos in cutouts:
        return cutouts[pos]
    for region in regions:
        x1, y1, x2, y2, block_type = region
        if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2:
            return block_type
    return None
def get_properties(pos):return block_properties.get(get_block_id(pos), None)
def check_collision(pos):
    properties = get_properties(pos)
    return properties["solid"] if properties else False
def is_on_ground():return check_collision((player.x, player.y + 1))
def apply_gravity():
    global jumped
    if jumped:
        jumped = False
        return
    new_pos = (player.x, player.y + 1)
    if not check_collision(new_pos):
        player.y += 1
def render():
    runner.update()
    buffer = Image()
    for x in range(5):
        for y in range(5):
            world_x = player.x - 2 + x
            world_y = player.y - 2 + y
            props = get_properties((world_x, world_y))
            if props:
                buffer.set_pixel(x, y, props["pixel"])
    buffer.set_pixel(2, 2, 9)
    display.show(buffer)
inventory = {}
def mine_block():
    direction = joystick_direction()
    if direction["right"]:
        target = (player.x + 1, player.y)
    elif direction["left"]:
        target = (player.x - 1, player.y)
    elif direction["down"]:
        target = (player.x, player.y + 1)
    elif direction["up"]:
        target = (player.x, player.y - 1)
    else:
        return
    props = get_properties(target)
    if props:
        start_time = running_time()
        play_frequency(150, 10)
        while ((running_time() - start_time < props["time"] * 1000) if props["time"] >= 0 else True) and yellow_button():
            sleep(200)
            play_frequency(150, 10)
        if yellow_button():
            block_id = get_block_id(target)
            if block_id and block_id in block_properties and block_properties[block_id]["time"] >= 0:
                inventory[block_id] = inventory.get(block_id, 0) + 1
            a(target[0], target[1], 0)
        apply_gravity()
        new_pos = (player.x, player.y - 1)
        if (direction["up"]) and is_on_ground() and not check_collision(new_pos):
            jumped = True
            player.y -= 1
            while joystick_direction()["up"]:
                render()
        
        if direction["right"]:
            new_pos = (player.x + 1, player.y)
            if (not check_collision(new_pos)):
                player.x += 1
        if direction["left"]:
            new_pos = (player.x - 1, player.y)
            if (not check_collision(new_pos)):
                player.x -= 1
        render()
def inventory_mode():
    items = list(inventory.keys())
    if not items:
        display.show(Image.NO)
        sleep(300)
        return None
    selection = 0
    while True:
        runner.update()
        img = Image(5, 5)
        for i, block_id in enumerate(items):
            col = i % 5
            row = i // 5
            if row < 5:
                brightness = block_properties[block_id]["pixel"]
                img.set_pixel(col, row, brightness)
        sel_col = selection % 5
        sel_row = selection // 5
        if (running_time() // 400) % 2 == 0:
            img.set_pixel(sel_col, sel_row, 9)
        display.show(img)
        dirs = joystick_direction()
        if dirs["left"] and selection % 5 > 0:
            selection -= 1
            sleep(200)
        elif dirs["right"] and selection % 5 < 4 and selection < len(items) - 1:
            selection += 1
            sleep(200)
        elif dirs["up"] and selection >= 5:
            selection -= 5
            sleep(200)
        elif dirs["down"] and selection + 5 < len(items):
            selection += 5
            sleep(200)
        elif inventory_button():
            display.scroll(items[selection]["name"],80)
            sleep(200)
        if yellow_button():
            sleep(300)
            return items[selection]
def place_instant():
    global placement_mode_active, current_placement_block
    dirs = joystick_direction()
    if dirs["right"]:
        target = (player.x + 1, player.y)
    elif dirs["left"]:
        target = (player.x - 1, player.y)
    elif dirs["up"]:
        target = (player.x, player.y - 1)
    elif dirs["down"]:
        target = (player.x, player.y + 1)
    else:
        target = (player.x + 1, player.y)
    if not check_collision(target):
        a(target[0], target[1], current_placement_block)
        inventory[current_placement_block] = inventory.get(current_placement_block, 0) - 1
        if inventory[current_placement_block] <= 0:
            placement_mode_active = False
            del inventory[current_placement_block]
            current_placement_block = None
        sleep(300)
placement_mode_active = False
current_placement_block = None
WORLDDATA
class Player:
    def __init__(self, x=2, y=2):
        self.x = x
        self.y = y
    def pos(self):
        return self.x, self.y
player = Player()
jumped = False
runner.add(apply_gravity,ms=500)
while True:
    direction = joystick_direction()
    if inventory_button():
        if not placement_mode_active:
            selected = inventory_mode()
            if selected is not None:
                placement_mode_active = True
                current_placement_block = selected
            sleep(300)
        else:
            placement_mode_active = False
            current_placement_block = None
            sleep(300)
    if yellow_button():
        if placement_mode_active:
            place_instant()
        else:
            mine_block()
    new_pos = (player.x, player.y - 1)
    if (direction["up"]) and is_on_ground() and not check_collision(new_pos):
        jumped = True
        player.y -= 1
        while joystick_direction()["up"]:
            runner.update()
            render()
        if yellow_button():
            if placement_mode_active:
                place_instant()
            else:
                mine_block()
    if direction["right"]:
        new_pos = (player.x + 1, player.y)
        if (not check_collision(new_pos)):
            player.x += 1
            while joystick_direction()["right"]:
                render()
            if yellow_button():
                if placement_mode_active:
                    place_instant()
                else:
                    mine_block()
    if direction["left"]:
        new_pos = (player.x - 1, player.y)
        if (not check_collision(new_pos)):
            player.x -= 1
            while joystick_direction()["left"]:
                render()
            if yellow_button():
                if placement_mode_active:
                    place_instant()
                else:
                    mine_block()
    render()