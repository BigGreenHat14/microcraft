import elevate
elevate.elevate()
import copy
try:
    import uflash
except ImportError:
    import os, sys
    os.system(sys.orig_argv[0] + " -m pip install uflash")
    import uflash
import tkinter as tk
from tkinter import ttk
block_types = {
    0: {"name": "Air", "color": "white"},
    1: {"solid": True, "pixel": 9, "name": "Bedrock", "color": "black", "time": -1},
    2: {"solid": True, "pixel": 6, "name": "Grass", "color": "green", "time": 1},
    3: {"solid": True, "pixel": 4, "name": "Dirt", "color": "orange", "time": 0.65},
    4: {"solid": True, "pixel": 0, "name": "World Border", "color": "lightgray", "time": -1},
    5: {"solid": True, "pixel": 2, "name": "Stone", "color": "gray", "time": 1.5}
}
block_properties = copy.deepcopy(block_types)
del block_properties[0]
SCRIPT = """_J='callback'
_I='interval'
_H='last_run'
_G='down'
_F=True
_E=False
_D=None
_C='right'
_B='left'
_A='up'
from microbit import*
class RunEvery:
	def __init__(self):self._tasks=[]
	def add(self,callback,ms=0):
		if ms<=0:raise ValueError('Interval must be greater than 0 milliseconds.')
		self._tasks.append({_I:ms,_J:callback,_H:running_time()})
	def update(self):
		now=running_time()
		for task in self._tasks:
			if now-task[_H]>=task[_I]:task[_H]=now;task[_J]()
runner=RunEvery()
from math import floor
def play_frequency(freq,ms):
	import math,audio
	def generate_square_wave_frames(frequency,duration_ms):
		frames_needed=int(duration_ms/1000*7812.5/32)
		for _ in range(frames_needed):
			frame=audio.AudioFrame()
			for i in range(32):
				t=i/7812.5
				if math.sin(2*math.pi*frequency*t)>0:sample=255
				else:sample=0
				frame[i]=sample
			yield frame
	frames=list(generate_square_wave_frames(freq,ms));audio.play(frames,pin=_D)
for pin in(pin8,pin13,pin14,pin15,pin16):pin.set_pull(pin.PULL_UP)
cbx,cby=pin2.read_analog(),pin1.read_analog()
def joystick_direction():x=round((pin2.read_analog()-cbx)/1023*9)+5;y=round((pin1.read_analog()-cby)/1023*9)+5;return{_B:x==10,_C:x==1,_A:y==0,_G:y==9}
def yellow_button():return pin16.read_digital()==0
def inventory_button():return pin13.read_digital()==0
def place_button():return pin15.read_digital()==0
block_properties=BLOCKPROP
regions=[]
cutouts={}
def a(x,y,block_type):cutouts[x,y]=block_type
def f(x1,y1,x2,y2,block_type):regions.append((min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2),block_type))
def get_block_id(pos):
	if pos in cutouts:return cutouts[pos]
	for region in regions:
		x1,y1,x2,y2,block_type=region
		if x1<=pos[0]<=x2 and y1<=pos[1]<=y2:return block_type
def get_properties(pos):return block_properties.get(get_block_id(pos),_D)
def check_collision(pos):properties=get_properties(pos);return properties['solid']if properties else _E
def is_on_ground():return check_collision((player.x,player.y+1))
def apply_gravity():
	global jumped
	if jumped:jumped=_E;return
	new_pos=player.x,player.y+1
	if not check_collision(new_pos):player.y+=1
def render():
	runner.update();buffer=Image()
	for x in range(5):
		for y in range(5):
			world_x=player.x-2+x;world_y=player.y-2+y;props=get_properties((world_x,world_y))
			if props:buffer.set_pixel(x,y,props['pixel'])
	buffer.set_pixel(2,2,9);display.show(buffer)
inventory={}
def mine_block():
	A='time';direction=joystick_direction()
	if direction[_C]:target=player.x+1,player.y
	elif direction[_B]:target=player.x-1,player.y
	elif direction[_G]:target=player.x,player.y+1
	elif direction[_A]:target=player.x,player.y-1
	else:return
	props=get_properties(target)
	if props:
		start_time=running_time();play_frequency(150,10)
		while(running_time()-start_time<props[A]*1000 if props[A]>=0 else _F)and yellow_button():sleep(200);play_frequency(150,10)
		if yellow_button():
			block_id=get_block_id(target)
			if block_id and block_id in block_properties and block_properties[block_id][A]>=0:inventory[block_id]=inventory.get(block_id,0)+1
			a(target[0],target[1],0)
		apply_gravity();new_pos=player.x,player.y-1
		if direction[_A]and is_on_ground()and not check_collision(new_pos):
			jumped=_F;player.y-=1
			while joystick_direction()[_A]:render()
		if direction[_C]:
			new_pos=player.x+1,player.y
			if not check_collision(new_pos):player.x+=1
		if direction[_B]:
			new_pos=player.x-1,player.y
			if not check_collision(new_pos):player.x-=1
		render()
def inventory_mode():
	while inventory_button():0
	items=list(inventory.keys())
	if not items:display.show(Image.NO);sleep(300);return
	selection=0
	while _F:
		runner.update();img=Image(5,5)
		for(i,block_id)in enumerate(items):
			col=i%5;row=i//5
			if row<5:brightness=block_properties[block_id]['pixel'];img.set_pixel(col,row,brightness)
		sel_col=selection%5;sel_row=selection//5
		if running_time()//400%2==0:img.set_pixel(sel_col,sel_row,9)
		display.show(img);dirs=joystick_direction()
		if dirs[_B]and selection%5>0:selection-=1;sleep(200)
		elif dirs[_C]and selection%5<4 and selection<len(items)-1:selection+=1;sleep(200)
		elif dirs[_A]and selection>=5:selection-=5;sleep(200)
		elif dirs[_G]and selection+5<len(items):selection+=5;sleep(200)
		elif inventory_button():display.scroll(block_properties[items[selection]]['name'],80);sleep(200)
		if yellow_button():sleep(300);return items[selection]
def place_instant():
	global placement_mode_active,current_placement_block;dirs=joystick_direction()
	if dirs[_C]:target=player.x+1,player.y
	elif dirs[_B]:target=player.x-1,player.y
	elif dirs[_A]:target=player.x,player.y-1
	elif dirs[_G]:target=player.x,player.y+1
	else:target=player.x+1,player.y
	if not check_collision(target):
		a(target[0],target[1],current_placement_block);inventory[current_placement_block]=inventory.get(current_placement_block,0)-1
		if inventory[current_placement_block]<=0:placement_mode_active=_E;del inventory[current_placement_block];current_placement_block=_D
		sleep(300)
placement_mode_active=_E
current_placement_block=_D
WORLDDATA
class Player:
	def __init__(self,x=2,y=2):self.x=x;self.y=y
	def pos(self):return self.x,self.y
player=Player()
jumped=_E
runner.add(apply_gravity,ms=500)
while _F:
	direction=joystick_direction()
	if inventory_button():
		if not placement_mode_active:
			selected=inventory_mode()
			if selected is not _D:placement_mode_active=_F;current_placement_block=selected
			sleep(300)
		else:placement_mode_active=_E;current_placement_block=_D;sleep(300)
	if yellow_button():
		if placement_mode_active:place_instant()
		else:mine_block()
	new_pos=player.x,player.y-1
	if direction[_A]and is_on_ground()and not check_collision(new_pos):
		jumped=_F;player.y-=1
		while joystick_direction()[_A]:runner.update();render()
		if yellow_button():
			if placement_mode_active:place_instant()
			else:mine_block()
	if direction[_C]:
		new_pos=player.x+1,player.y
		if not check_collision(new_pos):
			player.x+=1
			while joystick_direction()[_C]:render()
			if yellow_button():
				if placement_mode_active:place_instant()
				else:mine_block()
	if direction[_B]:
		new_pos=player.x-1,player.y
		if not check_collision(new_pos):
			player.x-=1
			while joystick_direction()[_B]:render()
			if yellow_button():
				if placement_mode_active:place_instant()
				else:mine_block()
	render()"""
# ----- Configuration -----
CELL_SIZE = 30      # pixels per cell

# Infinite scroll bounds (in cell units converted to pixels)
SCROLL_LEFT = -10000
SCROLL_TOP = -10000
SCROLL_RIGHT = 10000
SCROLL_BOTTOM = 10000

SPAWN_POS = (2, 2)  # Spawn cell position (always drawn black and non-editable)


# ----- Global World Data -----
# world is a dictionary with key=(x,y) and value = block id. If not present, cell is empty.
world = {}
# Ensure spawn cell is always empty.
world[SPAWN_POS] = 0

current_block = 1  # default selected block type (BEDROCK)

# ----- Tkinter GUI Setup -----
root = tk.Tk()
root.title("MicroCraft Editor")

# Create a frame to hold the canvas and scrollbars.
frame = tk.Frame(root)
frame.grid(row=0, column=0, columnspan=4)

# Visible canvas size (in pixels)
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# Set scroll region for an infinite grid.
canvas = tk.Canvas(frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white",
                   scrollregion=(SCROLL_LEFT, SCROLL_TOP, SCROLL_RIGHT, SCROLL_BOTTOM))
canvas.grid(row=0, column=0)

# Create horizontal and vertical scrollbars.
h_scroll = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
h_scroll.grid(row=1, column=0, sticky="ew")
v_scroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
v_scroll.grid(row=0, column=1, sticky="ns")
canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

# ----- Drawing Functions -----
def draw_grid(x_start, y_start, x_end, y_end):
    """Draw grid lines for cells from (x_start, y_start) to (x_end, y_end) in cell coordinates."""
    # Vertical lines.
    for x in range(x_start, x_end + 1):
        canvas.create_line(x * CELL_SIZE, y_start * CELL_SIZE,
                           x * CELL_SIZE, y_end * CELL_SIZE, fill="lightgray", tags="grid")
    # Horizontal lines.
    for y in range(y_start, y_end + 1):
        canvas.create_line(x_start * CELL_SIZE, y * CELL_SIZE,
                           x_end * CELL_SIZE, y * CELL_SIZE, fill="lightgray", tags="grid")

def draw_world():
    canvas.delete("cell")
    # Get visible area in canvas (in canvas coordinates) then convert to cell coordinates.
    x0 = int(canvas.canvasx(0) // CELL_SIZE)
    y0 = int(canvas.canvasy(0) // CELL_SIZE)
    x1 = int(canvas.canvasx(CANVAS_WIDTH) // CELL_SIZE) + 1
    y1 = int(canvas.canvasy(CANVAS_HEIGHT) // CELL_SIZE) + 1

    for y in range(y0, y1):
        for x in range(x0, x1):
            # Spawn cell always drawn black.
            if (x, y) == SPAWN_POS:
                color = "black"
            else:
                block = world.get((x, y), 0)
                color = block_types[block]["color"] if block in block_types else "white"
            x1_pixel = x * CELL_SIZE
            y1_pixel = y * CELL_SIZE
            x2_pixel = x1_pixel + CELL_SIZE
            y2_pixel = y1_pixel + CELL_SIZE
            canvas.create_rectangle(x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                                    fill=color, outline="", tags="cell")
    canvas.delete("grid")
    draw_grid(x0, y0, x1, y1)

# ----- Event Handlers -----
def canvas_click(event):
    # Compute cell coordinates accounting for scrolling.
    x = int(canvas.canvasx(event.x) // CELL_SIZE)
    y = int(canvas.canvasy(event.y) // CELL_SIZE)
    if (x, y) == SPAWN_POS:
        return
    world[(x, y)] = current_block
    draw_world()

def canvas_erase(event):
    x = int(canvas.canvasx(event.x) // CELL_SIZE)
    y = int(canvas.canvasy(event.y) // CELL_SIZE)
    if (x, y) == SPAWN_POS:
        return
    world[(x, y)] = 0
    draw_world()

canvas.bind("<Button-1>", canvas_click)
canvas.bind("<Button-3>", canvas_erase)

# ----- Palette UI -----
def set_current_block(val):
    global current_block
    current_block = int(val)

palette_label = tk.Label(root, text="Select Block:")
palette_label.grid(row=1, column=0)
palette_combo = ttk.Combobox(root, values=[f"{k}: {block_types[k]['name']}" for k in block_types if k != 0],
                             state="readonly", width=20)
palette_combo.grid(row=1, column=1)
palette_combo.current(0)
palette_combo.bind("<<ComboboxSelected>>", lambda e: set_current_block(palette_combo.get().split(":")[0]))

# ----- World Optimization and Code Generation -----
def optimize_world(world_dict):
    """
    Converts the world dictionary (only cells with nonzero block) into two lists:
      regions: each is (x1, y1, x2, y2, block_type) for contiguous rectangles.
      cutouts: list of (x, y, block_type) for individual cells that could not be merged.
    Works over all defined cells (including negative coordinates).
    """
    # Collect all cells that are nonzero and not the spawn.
    cells = [(x, y, b) for ((x, y), b) in world_dict.items() if b != 0 and (x, y) != SPAWN_POS]
    if not cells:
        return [], []
    xs = [x for (x, y, b) in cells]
    ys = [y for (x, y, b) in cells]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for (x, y, b) in cells:
        grid[y - min_y][x - min_x] = b

    visited = [[False]*width for _ in range(height)]
    regions = []
    cutouts = []
    for i in range(height):
        for j in range(width):
            if visited[i][j] or grid[i][j] == 0:
                visited[i][j] = True
                continue
            b = grid[i][j]
            max_j = j
            while max_j < width and grid[i][max_j] == b and not visited[i][max_j]:
                max_j += 1
            max_i = i
            valid = True
            while valid and max_i < height:
                for col in range(j, max_j):
                    if grid[max_i][col] != b or visited[max_i][col]:
                        valid = False
                        break
                if valid:
                    max_i += 1
            for ii in range(i, max_i):
                for jj in range(j, max_j):
                    visited[ii][jj] = True
            if (max_j - j) * (max_i - i) > 1:
                regions.append((j + min_x, i + min_y, max_j - 1 + min_x, max_i - 1 + min_y, b))
            else:
                cutouts.append((j + min_x, i + min_y, b))
    return regions, cutouts

def generate_worlddata():
    regions_list, cutouts_list = optimize_world(world)
    code_lines = []
    for (x1, y1, x2, y2, b) in regions_list:
        code_lines.append(f"f({x1},{y1},{x2},{y2},{b})")
    for (x, y, b) in cutouts_list:
        code_lines.append(f"a({x}, {y}, {b})")
    return "\n".join(code_lines)
def generate_code():
    return SCRIPT.replace("WORLDDATA",generate_worlddata()).replace("BLOCKPROP",block_properties.__repr__())

def show_code():
    code = generate_code()
    code_window = tk.Toplevel(root)
    code_window.title("Generated Micro:bit Code")
    text = tk.Text(code_window, wrap="none", width=60, height=20)
    text.insert("1.0", code)
    text.pack(fill="both", expand=True)
    btn_flash = tk.Button(code_window, text="Flash To Micro:Bit", command=flash_microbit)
    btn_flash.pack(pady=5)
def flash_microbit():
    open("_toflash.py","wb").write(bytes(generate_code(),'utf-8'))
    uflash.main(["_toflash.py"])
btn_generate = tk.Button(root, text="Generate Code", command=show_code)
btn_generate.grid(row=1, column=2)

# Redraw the world when the canvas is scrolled or resized.
def update(*_):
    draw_world()
    root.after(16, update)
root.after(16, update)

draw_world()
root.mainloop()