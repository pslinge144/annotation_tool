import Tkinter as tk
import ttk
import tkFileDialog, tkMessageBox
import os
from PIL import ImageTk, Image


class TrainingSetBuilder(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.crop_w = 672
        self.crop_h = 672
        self.chip_w = 224
        self.chip_h = 224
        self.buffer_w = 16
        self.buffer_h = 16
        self.pref_chip_thumb_h = 64.
        self.classes = ['pos', 'neg']
        self.input_dir = None
        self.output_exts = ['.jpg', '.png']
        self.chips = []
        self.create_widgets()
        self.context_viewer = None
        self.initialize_content()
        self.pack()

    def initialize_content(self):
        if self.context_viewer:
            self.context_viewer.destroy()
        self.context_viewer = ContextViewer()
        self.crop_canvas.delete(tk.ALL)
        self.crop_canvas.config(width=self.crop_w, height=self.crop_h)
        self.crop_manager = CropManager(crop_w=self.crop_w, crop_h=self.crop_h,
                                        buffer_w=self.buffer_w, buffer_h=self.buffer_h)
        self.chip_tree.delete(*self.chip_tree.get_children())
        self.chip_manager = ChipManager(chip_w=self.chip_w, chip_h=self.chip_h)
        self.img = None # the img to be chipped and labelled
        self.crop = None # the crop to labelled and saved

    def create_widgets(self):
        # set style of ttk widgets
        style = ttk.Style(self.master)
        style.configure('Treeview', rowheight=int((self.pref_chip_thumb_h + 6)))
        # put all image options at top of window
        self.io_frame = tk.Frame(self)
        self.io_frame.pack(side='top')
        self.load_img_btn = tk.Button(self.io_frame, text='Load Image', command=self.update_image)
        self.load_img_btn.grid(row=0, column=0, sticky=tk.W)
        self.update_crop_settings_btn = tk.Button(self.io_frame, text='Update Crop Settings',
                                                  command=self.update_crop_settings)
        self.update_crop_settings_btn.grid(row=1, column=0)
        tk.Label(self.io_frame, text='Crop Width:').grid(row=0, column=1)
        self.crop_w_entry_str = tk.StringVar()
        self.crop_w_entry_str.set(str(self.crop_w))
        self.crop_w_entry = tk.Entry(self.io_frame, textvariable=self.crop_w_entry_str)
        self.crop_w_entry.grid(row=0, column=2)
        tk.Label(self.io_frame, text='Crop Height:').grid(row=0, column=3)
        self.crop_h_entry_str = tk.StringVar()
        self.crop_h_entry_str.set(str(self.crop_h))
        self.crop_h_entry = tk.Entry(self.io_frame, textvariable=self.crop_h_entry_str)
        self.crop_h_entry.grid(row=0, column=4)
        tk.Label(self.io_frame, text='Chip Width:').grid(row=1, column=1)
        self.chip_w_entry_str = tk.StringVar()
        self.chip_w_entry_str.set(str(self.chip_w))
        self.chip_w_entry = tk.Entry(self.io_frame, textvariable=self.chip_w_entry_str)
        self.chip_w_entry.grid(row=1, column=2)
        tk.Label(self.io_frame, text='Chip Height:').grid(row=1, column=3)
        self.chip_h_entry_str = tk.StringVar()
        self.chip_h_entry_str.set(str(self.chip_h))
        self.chip_h_entry = tk.Entry(self.io_frame, textvariable=self.chip_h_entry_str)
        self.chip_h_entry.grid(row=1, column=4)
        tk.Label(self.io_frame, text='Buffer Width:').grid(row=2, column=1)
        self.buffer_w_entry_str = tk.StringVar()
        self.buffer_w_entry_str.set(str(self.buffer_w))
        self.buffer_w_entry = tk.Entry(self.io_frame, textvariable=self.buffer_w_entry_str)
        self.buffer_w_entry.grid(row=2, column=2)
        tk.Label(self.io_frame, text='Buffer Height:').grid(row=2, column=3)
        self.buffer_h_entry_str = tk.StringVar()
        self.buffer_h_entry_str.set(str(self.buffer_h))
        self.buffer_h_entry = tk.Entry(self.io_frame, textvariable=self.buffer_h_entry_str)
        self.buffer_h_entry.grid(row=2, column=4)
        tk.Label(self.io_frame, text='Class Selection').grid(row=0, column=5)
        self.class_cb = ttk.Combobox(self.io_frame, values=self.classes)
        self.class_cb.grid(row=0, column=6, sticky=tk.E)
        self.clear_classes_btn = tk.Button(self.io_frame, text='Clear Classes', command=self.clear_classes)
        self.clear_classes_btn.grid(row=1, column=5)
        self.class_entry_str = tk.StringVar()
        self.class_entry = tk.Entry(self.io_frame, textvariable=self.class_entry_str)
        self.class_entry.grid(row=1, column=6)
        self.append_class_btn = tk.Button(self.io_frame, text='Append Class', command=self.append_class)
        self.append_class_btn.grid(row=1, column=7)
        tk.Label(self.io_frame, text='Output Extension').grid(row=0, column=8)
        self.output_ext_cb = ttk.Combobox(self.io_frame, values=self.output_exts)
        self.output_ext_cb.grid(row=0, column=9, sticky=tk.E)
        self.export_chips_btn = tk.Button(self.io_frame, text='Export Chips', command=self.export_chips)
        self.export_chips_btn.grid(row=1, column=9, sticky=tk.E)

        self.select_all_bool = tk.BooleanVar()
        self.select_all_bool.set(False)
        self.select_all_chkbtn = tk.Checkbutton(self.io_frame, text='Select All',
                                                variable=self.select_all_bool,
                                                command=self.select_all_chips)
        self.select_all_chkbtn.grid(row=2, column=7, sticky=tk.E)
        self.auto_opposite_bool = tk.BooleanVar()
        self.auto_opposite_bool.set(False)
        self.auto_opposite_chkbtn = tk.Checkbutton(self.io_frame, text='Auto Opposite',
                                                    variable=self.auto_opposite_bool,
                                                    command=self.auto_opposite_export)
        self.auto_opposite_chkbtn.grid(row=2, column=8, sticky=tk.E)
        # put crop on left of window
        self.crop_canvas = tk.Canvas(self)
        self.crop_canvas.pack(fill=tk.BOTH, side='left')
        # put all navigation buttons in one frame
        self.nav_frame = tk.Frame(self)
        self.nav_frame.pack(side='left')
        self.prev_crop_btn = tk.Button(self.nav_frame, text='Left Crop', command=self.send_left_crop_to_labeller)
        self.prev_crop_btn.grid(row=1, column=0)
        self.next_crop_btn = tk.Button(self.nav_frame, text='Right Crop', command=self.send_right_crop_to_labeller)
        self.next_crop_btn.grid(row=1, column=2)
        self.prev_crop_btn = tk.Button(self.nav_frame, text='Lower Crop', command=self.send_lower_crop_to_labeller)
        self.prev_crop_btn.grid(row=2, column=1)
        self.next_crop_btn = tk.Button(self.nav_frame, text='Upper Crop', command=self.send_upper_crop_to_labeller)
        self.next_crop_btn.grid(row=0, column=1)
        # keyboard bindings to buttons
        self.master.bind('<Left>', self.left_key)
        self.master.bind('<Right>', self.right_key)
        self.master.bind('<Up>', self.up_key)
        self.master.bind('<Down>', self.down_key)
        # put all chip components in one frame
        self.chip_frame = tk.Frame(self, width=100, height=self.crop_h)
        self.chip_frame.pack(side='left')
        self.chip_tree = ttk.Treeview(self.chip_frame, columns=['Chip'], displaycolumns='#all', selectmode='extended')
        ysb = ttk.Scrollbar(self.chip_frame, orient='vertical', command=self.chip_tree.yview)
        self.chip_tree.configure(yscroll=ysb.set)
        self.chip_tree.grid(row=0, column=0)
        ysb.grid(row=0, column=1, sticky='ns')
    
    def select_all_chips(self):
        if self.select_all_bool.get():
            self.chip_tree.selection_set(self.chip_tree.get_children())
        else:
            self.chip_tree.selection_remove(self.chip_tree.get_children())
    
    def auto_opposite_export(self):
        pass

    def append_class(self):
        class_entry_str = self.class_entry_str.get()
        if class_entry_str != '':
            self.classes.append(class_entry_str)
            self.class_cb.configure(values=self.classes)

    def clear_classes(self):
        self.classes = []
        self.class_cb.configure(values=self.classes)

    def update_crop_settings(self):
        try:
            self.crop_w = int(self.crop_w_entry_str.get())
            self.crop_h = int(self.crop_h_entry_str.get())
            self.chip_w = int(self.chip_w_entry_str.get())
            self.chip_h = int(self.chip_h_entry_str.get())
            self.initialize_content()
        except:
            tkMessageBox.showwarning('Crop Settings Warning', 'Invalid input to crop settings')

    def update_image(self):
        img = self.open_img()
        if img:
            self.img = img
            self.context_viewer.set_thumb(self.img.copy())
            self.crop_manager.set_image(self.img)
            self.update_crop()

    def open_img(self):
        initialdir = os.path.expanduser('~')
        if self.input_dir:
            initialdir = self.input_dir
        img_filename = tkFileDialog.askopenfilename(title='Open Image File',
                                                        filetypes=[('PNG files', '.png'), ('JPEG files', '.jpg')],
                                                        initialdir=initialdir)
        if img_filename:
            self.img_filename = img_filename
            self.input_dir = os.path.dirname(self.img_filename)
            img = Image.open(self.img_filename)
            return img
        return None

    def update_crop(self):
        self.crop_canvas.delete(tk.ALL)
        self.crop = self.crop_manager.get_crop()
        if self.crop:
            self.crop_img = ImageTk.PhotoImage(self.crop)
            self.crop_canvas.create_image(0, 0, anchor=tk.NW, image=self.crop_img)
            self.chip_manager.set_crop(self.crop)
        crop_params = self.crop_manager.get_crop_params()
        if crop_params:
            self.context_viewer.display_crop(crop_params)
        self.update_chips()

    def update_chips(self):
        self.chip_tree.delete(*self.chip_tree.get_children())
        self.select_all_bool.set(False)
        if self.crop:
            self.chips = self.chip_manager.get_chips()
            self.chip_thumbs = []
            for chip in self.chips:
                self.chip_thumbs.append(self.scale_chip_to_thumbnail(chip.copy()))
                self.chip_tree.insert('', 'end', image=self.chip_thumbs[len(self.chip_thumbs)-1])
            # use this to draw pattern on crop
            chip_params = self.chip_manager.get_chip_parameters()
            if chip_params:
                for params in chip_params:
                    self.display_chip(params)

    def export_chips(self):
        class_label = None
        if self.classes:
            for idx, label in enumerate(self.classes):
                if not os.path.exists(label):
                    os.makedirs(class_label)
                if idx == self.class_cb.current():
                    class_label = self.classes[idx]
                else:
                    opp_label = self.classes[idx]
        basename = os.path.basename(self.img_filename)
        basename_noext = os.path.splitext(basename)[0]
        crop_start_x, crop_start_y, _, _ = self.crop_manager.get_crop_params().get()
        output_ext = self.output_exts[self.output_ext_cb.current()]
        selected_chip_thumbs = self.chip_tree.selection()
        for selection in selected_chip_thumbs:
            chip_idx = self.chip_tree.index(selection)
            chip_start_x, chip_start_y, _, _ = self.chip_manager.get_chip_parameters(chip_idx).get()
            start_x = crop_start_x + chip_start_x - self.buffer_w
            start_y = crop_start_y + chip_start_y - self.buffer_h
            filename = basename_noext + '_' + str(start_x) + '_' + str(start_y) + output_ext
            save_path = filename
            if class_label:
                save_path = os.path.join(class_label, filename)
            buffered_chip_params = (start_x, start_y,
                                    start_x + self.chip_w + 2 * self.buffer_w,
                                    start_y + self.chip_h + 2 * self.buffer_h)
            chip = self.img.crop(buffered_chip_params)
            chip.save(save_path)
        if self.auto_opposite_bool.get():
            for child in self.chip_tree.get_children():
                if child not in selected_chip_thumbs:
                    chip_idx = self.chip_tree.index(child)
                    chip_start_x, chip_start_y, _, _ = self.chip_manager.get_chip_parameters(chip_idx).get()
                    start_x = crop_start_x + chip_start_x - self.buffer_w
                    start_y = crop_start_y + chip_start_y - self.buffer_h
                    filename = basename_noext + '_' + str(start_x) + '_' + str(start_y) + output_ext
                    save_path = filename
                    if opp_label:
                        save_path = os.path.join(opp_label, filename)
                    buffered_chip_params = (start_x, start_y,
                                            start_x + self.chip_w + 2 * self.buffer_w,
                                            start_y + self.chip_h + 2 * self.buffer_h)
                    chip = self.img.crop(buffered_chip_params)
                    chip.save(save_path)
    

    def scale_chip_to_thumbnail(self, chip):  # 1600, 800
        self.scale = 1.
        w, h = chip.size
        if h > self.pref_chip_thumb_h:
            self.scale = self.pref_chip_thumb_h / h
        chip.thumbnail((int(w * self.scale), int(h * self.scale)), Image.ANTIALIAS)
        return ImageTk.PhotoImage(chip)

    def display_chip(self, chip_params):
        self.crop_canvas.create_rectangle(chip_params.get(), outline='red')

    def left_key(self, event):
        self.send_left_crop_to_labeller()

    def right_key(self, event):
        self.send_right_crop_to_labeller()

    def up_key(self, event):
        self.send_upper_crop_to_labeller()

    def down_key(self, event):
        self.send_lower_crop_to_labeller()

    def send_left_crop_to_labeller(self):
        self.crop_manager.move_left()
        self.update_crop()

    def send_right_crop_to_labeller(self):
        self.crop_manager.move_right()
        self.update_crop()

    def send_lower_crop_to_labeller(self):
        self.crop_manager.move_down()
        self.update_crop()

    def send_upper_crop_to_labeller(self):
        self.crop_manager.move_up()
        self.update_crop()


class CropParameters():
    def __init__(self, start_x=0, start_y = 0, crop_w=672, crop_h=672):
        self.start_x = start_x
        self.start_y = start_y
        self.crop_w = crop_w
        self.crop_h = crop_h

    def get(self):
        return (self.start_x, self.start_y, self.start_x + self.crop_w, self.start_y + self.crop_h)

    def get_scaled_copy(self, scale):
        return CropParameters(scale * self.start_x, scale * self.start_y,
                                scale * self.crop_w, scale * self.crop_h)
    

class CropManager():
    def __init__(self, crop_w=672, crop_h=672, buffer_w=0, buffer_h=0):
        self.crop_w = crop_w
        self.crop_h = crop_h
        self.buffer_w = buffer_w
        self.buffer_h = buffer_h
        self.image = None
        self.reset_crop_grid()

    def get_num_crops_in_width(self):
        if self.image:
            img_w = self.image.size[0] - (2 * self.buffer_w)
            num_crops = img_w / self.crop_w
            if (img_w % self.crop_w) > 0:
                num_crops += 1
            return num_crops
        return 0

    def move_down(self):
        self.move_crop_position(self.get_num_crops_in_width())

    def move_up(self):
        self.move_crop_position(-self.get_num_crops_in_width())

    def move_left(self):
        self.move_crop_position(-1)

    def move_right(self):
        self.move_crop_position(1)

    def move_crop_position(self, crop_idx_shift):
        if self.crop_grid:
            self.crop_idx += crop_idx_shift
            if self.crop_idx >= len(self.crop_grid):
                self.crop_idx -= len(self.crop_grid)
            elif self.crop_idx <= - len(self.crop_grid):
                self.crop_idx += len(self.crop_grid)

    def get_crop(self):
        if self.crop_grid:
            crop_params = self.crop_grid[self.crop_idx]
            return self.image.crop(crop_params.get())

    def get_crop_params(self):
        if self.crop_grid:
            return self.crop_grid[self.crop_idx]
        else:
            return None

    def set_image(self, img):
        self.image = img
        self.reset_crop_grid()

    def reset_crop_grid(self):
        self.crop_idx = 0
        self.crop_grid = []
        if self.image:
            img_w, img_h = self.image.size[:]
            for i in range(self.buffer_h, img_h, self.crop_h):
                for j in range(self.buffer_w, img_w, self.crop_w):
                    # check if the next crop is valid, based on image size
                    crop_w = self.crop_w
                    crop_h = self.crop_h
                    if (j + crop_w) > (img_w - self.buffer_w - 1):
                        crop_w = (img_w - 1) - j
                    if (i + crop_h) > (img_h - self.buffer_h - 1):
                        crop_h = (img_h - 1) - i
                    # build crop parameters based on valid crop size
                    self.crop_grid.append(CropParameters(j, i, crop_w, crop_h))


class ChipManager():
    def __init__(self, chip_w, chip_h):
        self.chip_w = chip_w
        self.chip_h = chip_h
        self.crop = None
        self.chips = []
        self.reset_chip_grid()

    def reset_chip_grid(self):
        self.chip_grid = []
        if self.crop:
            crop_w, crop_h = self.crop.size[:]
            num_chips_w = (crop_w / self.chip_w)
            num_chips_h = (crop_h / self.chip_h)
            chip_buffer_w = (crop_w % self.chip_w) / num_chips_w
            chip_buffer_h = (crop_h % self.chip_h) / num_chips_h
            for i in range(num_chips_h):
                for j in range(num_chips_w):
                    start_x = j * (chip_buffer_w + self.chip_w)
                    start_y = i * (chip_buffer_h + self.chip_h)
                    self.chip_grid.append(CropParameters(start_x=start_x, start_y=start_y,
                                                         crop_w=self.chip_w, crop_h=self.chip_h))

    def set_crop(self, crop):
        self.crop = crop
        self.reset_chip_grid()

    def get_chips(self):
        self.chips = []
        if self.crop:
            for chip_params in self.chip_grid:
                self.chips.append(self.crop.crop(chip_params.get()))
        return self.chips
    
    def get_chip(self, chip_idx):
        if self.crop:
            chip_params = self.chip_grid[chip_idx]
            return self.crop.crop(chip_params.get())

    def get_chip_parameters(self, chip_idx=None):
        if chip_idx is not None:
            return self.chip_grid[chip_idx]
        return self.chip_grid        


class ContextViewer(tk.Toplevel):
    def __init__(self, desired_width=None, desired_height=None):
        tk.Toplevel.__init__(self)
        self.desired_width = desired_width
        self.desired_height = desired_height
        self._set_window_dimensions()
        self.scale = 1.
        self.thumb = None
        self.create_widgets()

    def _set_window_dimensions(self):
        if not (self.desired_width and self.desired_height):
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            self.desired_width = screen_width - 100
            self.desired_height = screen_height - 100

    def create_widgets(self):
        self.thumb_canvas = tk.Canvas(self)
        self.thumb_canvas.pack(fill=tk.BOTH)

    def set_thumb(self, img):
        self.thumb_canvas.delete(tk.ALL)
        self.thumb = self.scale_to_thumbnail(img)
        self.thumb_canvas.config(width=self.thumb.width(), height=self.thumb.height())
        self.thumb_canvas.create_image(0, 0, anchor=tk.NW, image=self.thumb)

    def scale_to_thumbnail(self, img):  # 1600, 800
        self.scale = 1.
        width_scale = 1.
        height_scale = 1.
        w, h = img.size
        if w > self.desired_width:
            width_scale = float(self.desired_width) / float(w)
        if h > self.desired_height:
            height_scale = float(self.desired_height) / float(h)
        self.scale = min(width_scale, height_scale)
        img.thumbnail((int(w * self.scale), int(h * self.scale)), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)

    def display_crop(self, crop_params):
        if self.thumb:
            scaled_crop_params = crop_params.get_scaled_copy(self.scale)
            self.thumb_canvas.create_rectangle(scaled_crop_params.get(), outline='red')

root = tk.Tk()
app = TrainingSetBuilder(master=root)
app.mainloop()