import tkinter as tk
from tkinter import messagebox
import random
import time

# --- Configuration & Constants ---

CONFIG = {
    "EASY": {
        "N": 4,
        "BOX_H": 2, "BOX_W": 2,
        "REMOVE": 6, # Number of cells to clear
        "TIME": 3 * 60, # 3 minutes
        "BG": "#E0FFE0", # Lighter Green (Game Window Background)
        "TITLE_FONT": ("Comic Sans MS", 20, "bold")
    },
    "MEDIUM": {
        "N": 9,
        "BOX_H": 3, "BOX_W": 3,
        "REMOVE": 40,
        "TIME": 12 * 60, # 12 minutes
        "BG": "#FFFACD", # Lighter Mustard (Lemon Chiffon)
        "TITLE_FONT": ("Helvetica", 20, "bold")
    },
    "HARD": {
        "N": 16,
        "BOX_H": 4, "BOX_W": 4,
        "REMOVE": 150, 
        "TIME": 30 * 60, # 30 minutes
        "BG": "#FFE0E0", # Lighter Red
        "TITLE_FONT": ("Times New Roman", 20, "bold")
    }
}

# Helper to handle 16x16 single-char representation (1-9, A-G)
def val_to_char(v):
    if v is None or v == 0: return ""
    if 1 <= v <= 9: return str(v)
    # 10=A, 11=B, ... 16=G
    return chr(ord('A') + v - 10)

def char_to_val(c):
    if not c: return 0
    if c.isdigit(): return int(c)
    # A=10, B=11...
    return ord(c.upper()) - ord('A') + 10

# --- Sudoku Logic ---

class SudokuLogic:
    def __init__(self, n, box_h, box_w):
        self.n = n
        self.box_h = box_h
        self.box_w = box_w
        self.board = [[0]*n for _ in range(n)]

    def is_valid(self, board, r, c, num):
        # Row check
        for j in range(self.n):
            if board[r][j] == num: return False
        # Col check
        for i in range(self.n):
            if board[i][c] == num: return False
        # Box check
        start_r = (r // self.box_h) * self.box_h
        start_c = (c // self.box_w) * self.box_w
        for i in range(self.box_h):
            for j in range(self.box_w):
                if board[start_r + i][start_c + j] == num:
                    return False
        return True

    def fill_board(self, board):
        # Find empty
        empty = None
        for r in range(self.n):
            for c in range(self.n):
                if board[r][c] == 0:
                    empty = (r, c)
                    break
            if empty: break
        
        if not empty:
            return True # Solved
        
        r, c = empty
        nums = list(range(1, self.n + 1))
        random.shuffle(nums)
        
        for num in nums:
            if self.is_valid(board, r, c, num):
                board[r][c] = num
                if self.fill_board(board):
                    return True
                board[r][c] = 0
        return False

    def generate_game(self, remove_count):
        # 1. Start with empty
        self.board = [[0]*self.n for _ in range(self.n)]
        
        # 2. Fill Diagonal boxes independently (optimization)
        for i in range(0, self.n, self.box_h):
            nums = list(range(1, self.n + 1))
            random.shuffle(nums)
            idx = 0
            for r in range(i, i + self.box_h):
                for c in range(i, i + self.box_w):
                    # Ensure indices are within bounds for non-square boxes (though not an issue for N=4, 9, 16)
                    if r < self.n and c < self.n:
                         self.board[r][c] = nums[idx]
                         idx += 1
                    
        # 3. Solve the rest
        self.fill_board(self.board)
        
        # 4. Save solution
        solution = [row[:] for row in self.board]
        
        # 5. Remove numbers
        initial = [row[:] for row in self.board]
        attempts = remove_count
        while attempts > 0:
            r = random.randint(0, self.n - 1)
            c = random.randint(0, self.n - 1)
            if initial[r][c] != 0:
                initial[r][c] = 0
                attempts -= 1
                
        return initial, solution

# --- UI Application ---

class GameWindow(tk.Toplevel):
    def __init__(self, parent, difficulty, on_close_callback):
        super().__init__(parent)
        self.parent = parent
        self.on_close_callback = on_close_callback
        self.cfg = CONFIG[difficulty]
        self.n = self.cfg["N"]
        self.bg_color = self.cfg["BG"]
        
        self.title(f"Sudoku - {difficulty}")
        self.configure(bg=self.bg_color)
        # RESTORED: Initial balanced window size
        self.geometry("950x750") 
        
        # Game State
        self.logic = SudokuLogic(self.n, self.cfg["BOX_H"], self.cfg["BOX_W"])
        self.initial_board, self.solution = self.logic.generate_game(self.cfg["REMOVE"])
        self.time_left = self.cfg["TIME"]
        self.timer_running = True
        self.hints_left = 3
        
        self.entries = {} # Map (r,c) -> Entry widget
        
        # Layout Frames
        header_frame = tk.Frame(self, bg=self.bg_color)
        header_frame.pack(side="top", fill="x", pady=10)
        
        tk.Label(header_frame, text=f"Level: {difficulty}", font=self.cfg["TITLE_FONT"], bg=self.bg_color).pack()
        
        content_frame = tk.Frame(self, bg=self.bg_color)
        content_frame.pack(side="top", expand=True, fill="both", padx=20)
        
        # Board Frame - This frame's background color acts as the grid line color
        self.board_frame = tk.Frame(content_frame, bg="#333333", bd=0) # Dark Grey for borders
        self.board_frame.pack(side="left", padx=20, pady=20)
        
        # Controls Frame (Right Side)
        controls_frame = tk.Frame(content_frame, bg=self.bg_color)
        controls_frame.pack(side="right", fill="y", padx=20, pady=20)
        
        # --- Build UI Components ---
        self.create_board_grid()
        self.create_controls(controls_frame)
        
        # Submit Button (Below Board)
        submit_btn = tk.Button(self, text="SUBMIT BOARD", bg="#4CAF50", fg="white", 
                               font=("Arial", 14, "bold"), command=self.submit_board, width=22, height=2)
        submit_btn.pack(side="bottom", pady=20)
        
        # Start Timer
        self.update_timer()
        
        # Handle Window Close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_board_grid(self):
        # Valid input register
        vcmd = (self.register(self.validate_input), '%P')
        
        # Cell size calculation based on N (RESTORED initial sizes)
        if self.n == 16:
            cell_width = 4 # Reverted to 4
            font_size = 18 # Reverted to 18
        else:
            cell_width = 5 # Reverted to 5
            font_size = 24 # Reverted to 24
        
        for r in range(self.n):
            for c in range(self.n):
                
                # --- Border/Spacing Logic (Thick lines for boxes) ---
                
                # Default padding (1px on all sides, resulting in 2px line between cells)
                padx = 1 
                pady = 1

                # Extra padding for major box boundaries (creating a thick line)
                # Apply extra padding to the right and bottom edges of the box
                if (c + 1) % self.cfg["BOX_W"] == 0 and c != self.n - 1:
                    padx = (1, 3) # (left, right) -> 3px padding on the right
                else:
                    padx = (1, 1) # Standard padding

                if (r + 1) % self.cfg["BOX_H"] == 0 and r != self.n - 1:
                    pady = (1, 3) # (top, bottom) -> 3px padding on the bottom
                else:
                    pady = (1, 1) # Standard padding

                # Use a single Frame container for the cell. This frame uses the padding 
                # against the dark board_frame background to draw the grid lines.
                cell_frame = tk.Frame(self.board_frame, 
                                      highlightthickness=0, bd=0)
                
                cell_frame.grid(row=r, column=c, padx=padx, pady=pady, sticky="nsew")
                
                val = self.initial_board[r][c]
                is_readonly = val != 0
                
                # The Entry widget itself
                e = tk.Entry(cell_frame, width=cell_width, justify="center", 
                             font=("Arial", font_size, "bold"),
                             validate="key", validatecommand=vcmd,
                             relief="ridge", bd=1, 
                             highlightthickness=0) 
                
                e.pack(fill="both", expand=True, padx=0, pady=0) # No internal padding on pack
                
                if is_readonly:
                    txt = val_to_char(val)
                    e.insert(0, txt)
                    # Fixed background for read-only cells (no changes here)
                    e.config(state="disabled", disabledbackground="#e8e8e8", disabledforeground="black")
                else:
                    # Set editable cell background back to standard white
                    e.config(bg="#ffffff")
                
                self.entries[(r, c)] = e

    def create_controls(self, parent):
        # Timer
        self.timer_label = tk.Label(parent, text="00:00", font=("Courier", 28, "bold"), 
                                    bg="black", fg="red", width=8)
        self.timer_label.pack(pady=20)
        
        btn_style = {"font": ("Arial", 14), "width": 18, "pady": 8}
        
        # Hints
        self.hint_status_lbl = tk.Label(parent, text=f"Hints Left: {self.hints_left}", 
                                        bg=self.bg_color, font=("Arial", 12))
        self.hint_status_lbl.pack(pady=(10, 0))
        
        tk.Button(parent, text="Get Hint", bg="orange", command=self.use_hint, **btn_style).pack(pady=5)
        
        # Verify
        tk.Button(parent, text="Verify Cell", bg="#2196F3", fg="white", 
                  command=self.verify_board_visual, **btn_style).pack(pady=20)
        
        # Show Solution
        tk.Button(parent, text="Show Solution", bg="#f44336", fg="white", 
                  command=self.show_solution, **btn_style).pack(pady=5)
        
        # New Game
        tk.Button(parent, text="New Game", bg="#9C27B0", fg="white", 
                  command=self.restart_game, **btn_style).pack(pady=20)

    # --- Logic Methods ---

    def validate_input(self, P):
        if P == "": return True
        if len(P) > 1: return False # Single char only
        
        P = P.upper()
        
        if self.n == 4:
            return P in "1234"
        elif self.n == 9:
            return P in "123456789"
        elif self.n == 16:
            # 1-9 and A-G
            return P in "123456789ABCDEFG"
        return False

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            m, s = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{m:02d}:{s:02d}")
            self.time_left -= 1
            self.after(1000, self.update_timer)
        elif self.time_left == 0 and self.timer_running:
            self.timer_running = False
            self.timer_label.config(text="00:00")
            messagebox.showinfo("Time's Up", "You ran out of time!")
            self.disable_board()

    def use_hint(self):
        if not self.timer_running: return
        if self.hints_left <= 0:
            messagebox.showwarning("No Hints", "You have used all your hints!")
            return
            
        # Find empty or incorrect cells
        candidates = []
        for r in range(self.n):
            for c in range(self.n):
                if self.initial_board[r][c] == 0: # User editable
                    entry = self.entries[(r,c)]
                    val = entry.get().upper()
                    correct_val = val_to_char(self.solution[r][c])
                    
                    if val != correct_val:
                        candidates.append((r, c))
        
        if not candidates:
            messagebox.showinfo("Great!", "The board is already filled correctly!")
            return
            
        # Pick random
        r, c = random.choice(candidates)
        correct_char = val_to_char(self.solution[r][c])
        
        entry = self.entries[(r,c)]
        entry.delete(0, tk.END)
        entry.insert(0, correct_char)
        # Using a fixed font size for hints
        entry.config(fg="blue", font=("Arial", 18, "bold")) 
        
        self.hints_left -= 1
        self.hint_status_lbl.config(text=f"Hints Left: {self.hints_left}")

    def verify_board_visual(self):
        if not self.timer_running: return
        
        for r in range(self.n):
            for c in range(self.n):
                if self.initial_board[r][c] == 0:
                    entry = self.entries[(r, c)]
                    val = entry.get().upper()
                    
                    base_color = "#ffffff"
                    
                    if val:
                        correct = val_to_char(self.solution[r][c])
                        if val == correct:
                            entry.config(bg="#C8E6C9") # Light Green (Correct)
                        else:
                            entry.config(bg="#FFCDD2") # Light Red (Incorrect)
                    else:
                        entry.config(bg=base_color) # Reset to white

    def submit_board(self):
        if not self.timer_running: return
        
        # Check completeness and correctness
        is_full = True
        is_correct = True
        
        for r in range(self.n):
            for c in range(self.n):
                entry = self.entries[(r, c)]
                val = entry.get().upper()
                correct = val_to_char(self.solution[r][c])
                
                if val == "":
                    is_full = False
                if val != correct:
                    is_correct = False
        
        if not is_full:
            messagebox.showwarning("Incomplete", "Please fill in all numbers before submitting.")
        elif is_correct:
            self.timer_running = False
            messagebox.showinfo("Victory!", "Congratulations! You solved the puzzle!")
            self.disable_board()
        else:
            messagebox.showerror("Incorrect", "There are errors in your solution. Keep trying!")

    def show_solution(self):
        if not self.timer_running: return
        if not messagebox.askyesno("Confirm", "Show solution? This will end the game."):
            return
            
        self.timer_running = False
        for r in range(self.n):
            for c in range(self.n):
                entry = self.entries[(r, c)]
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, val_to_char(self.solution[r][c]))
                entry.config(state="disabled", disabledbackground="#FFF9C4", disabledforeground="purple")

    def disable_board(self):
        for entry in self.entries.values():
            entry.config(state="disabled")

    def restart_game(self):
        if messagebox.askyesno("New Game", "Return to Main Menu?"):
            self.on_close()

    def on_close(self):
        self.timer_running = False
        self.destroy()
        self.on_close_callback()

# --- Main Menu Window ---

class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Master - Project")
        self.root.geometry("500x500") 
        self.root.configure(bg="#f0f0f0")
        
        # Title
        tk.Label(root, text="SUDOKU", font=("Helvetica", 40, "bold"), 
                 bg="#f0f0f0", fg="#333").pack(pady=50)
        
        tk.Label(root, text="Select Difficulty:", font=("Arial", 16), 
                 bg="#f0f0f0").pack(pady=15)
        
        # Buttons
        btn_config = {"width": 25, "height": 2, "font": ("Arial", 14, "bold"), "bd": 0, "fg": "white"} 
        
        # Darker Colors for Main Menu Buttons
        tk.Button(root, text="EASY (4x4)", bg="#66BB6A", 
                  command=lambda: self.start_game("EASY"), **btn_config).pack(pady=10)
                  
        tk.Button(root, text="MEDIUM (9x9)", bg="#FFCA28", 
                  command=lambda: self.start_game("MEDIUM"), **btn_config).pack(pady=10)
                  
        tk.Button(root, text="HARD (16x16)", bg="#EF5350", 
                  command=lambda: self.start_game("HARD"), **btn_config).pack(pady=10)

    def start_game(self, difficulty):
        self.root.withdraw() # Hide menu
        GameWindow(self.root, difficulty, self.show_menu)

    def show_menu(self):
        self.root.deiconify() # Show menu

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()