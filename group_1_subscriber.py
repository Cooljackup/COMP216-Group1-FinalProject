# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk

# Broker connection and Topic.
### TEMPORARY. Just for testing locally.
BROKER = "127.0.0.1"
TOPIC = "TOPIC"

# Subscriber class.
### TEMPORARY. Just to have it set up.
class Subscriber:
    def __init__(self):
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

# SubscriberGUI class that creates and displays the GUI.
class SubscriberGUI:
    def __init__(self, root):
        self.root = root
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # GUI setup.
    def gui_setup(self):
        self.root.title("Subscriber")
        self.root.geometry("400x400")

        self.text = tk.Text(self.root, height=15, width=40)
        self.text.pack(pady=10)

        tk.Button(self.root, text="Start", command=self.start).pack(pady=10)
        tk.Button(self.root, text="Stop", command=self.stop).pack(pady=10)

    ### TEMPORARY. Just have to set it up.
    def start(self):
        print("Start")

    ### TEMPORARY. Just have to set it up.
    def stop(self):
        print("Stop")

# Main class to run Subscriber.
if __name__ == "__main__":
    root = tk.Tk()
    app = SubscriberGUI(root)
    root.mainloop()