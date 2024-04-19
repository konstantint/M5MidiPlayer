import os

class MidiPlaylist:
    def __init__(self, root_dir="/mid"):
        self.root_dir = root_dir
        self.files = os.listdir(root_dir)
        self.files.sort()
        self.current_file_id = 0
    
    def get_current_file(self):
        return "/".join([self.root_dir, self.files[self.current_file_id]])
    
    def get_current_file_title(self):
        title = self.files[self.current_file_id][:-4] # .rstrip(".mid") does not always work as intended somewhy
        return title.split("_", 1)[-1]

    def next_prev(self, delta):
        self.current_file_id = (self.current_file_id + delta) % len(self.files)