# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk
import paho.mqtt.client as mqtt
import json
import uuid
import time
import threading

# Import DataGenerator.
from group_1_data_generator import DataGenerator

# Broker connection and Topic.
### TEMPORARY. Just for testing locally.
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "TEMPERATURE"

# Publisher class that sends the data to the broker.
class Publisher:
    def __init__(self):
        self.client = mqtt.Client()
        self.generator = DataGenerator()
        self.running = False
        self.interval = 10  # default
        self.state = "STOPPED"
    
    # Format data class that formats the data into a json.
    def format_data(self, value):
        return json.dumps({"packet_id": str(uuid.uuid4()), "timestamp": time.time(), "value": value})
    
    # Start class that connects to the broker and sends the formatted data as a json and stores it as a log variable.
    def start(self, log, get_interval):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        self.running = True
        self.state = "RUNNING"
        
        start_message = json.dumps({
            "event": "START",
            "timestamp": time.time()
        })
        
        self.client.publish(TOPIC, start_message)
        
        log("Publisher START event sent")

        while self.running:
            self.interval = get_interval()
            
            data = self.format_data(self.generator.get_value())
            self.client.publish(TOPIC, data)
            log(f"Sent: {data} (interval: {self.interval}s)")
            
            elapsed = 0
            while self.running and elapsed < self.interval:
                time.sleep(0.2)
                elapsed += 0.2
                
                new_interval = get_interval()
                if new_interval != self.interval:
                    self.interval = new_interval
                    break

    def stop(self):
        self.running = False
        self.state = "STOPPED"
        
        stop_message = json.dumps({
            "event": "STOP",
            "timestamp": time.time()
        })
    
        try:
            self.client.publish(TOPIC, stop_message)
        except:
            pass
    
        self.client.loop_stop()
        self.client.disconnect()    

# PublisherGUI class that creates and displays the GUI.
class PublisherGUI:
    def __init__(self, root):
        self.root = root
        self.publisher = Publisher()
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # GUI setup.
    def gui_setup(self):
        self.interval_var = tk.StringVar(value="10 sec")
        
        intervals = {
            "1 sec": 1,
            "5 sec": 5,
            "10 sec": 10,
            "Hourly": 3600,
            "Daily": 86400,
            "Weekly": 604800,
            "Monthly": 2592000
        }
        
        self.interval_map = intervals
        
        self.root.title("Publisher")
        self.root.geometry("800x500")
        self.root.minsize(500, 300)
        self.root.grid_columnconfigure(1, minsize=200)

        # Configure grid (2 columns: left = log, right = controls)
        self.root.columnconfigure(0, weight=3)  # main area
        self.root.columnconfigure(1, weight=1)  # side panel
        self.root.rowconfigure(0, weight=1)
    
        # LEFT FRAME (log area)
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # RIGHT FRAME (controls)
        right_frame = tk.Frame(self.root, bd=2, relief="groove")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(99, weight=1)
    
        # TEXT + SCROLLBAR
        self.text = tk.Text(left_frame, wrap="none")
        self.text.grid(row=0, column=0, sticky="nsew")
    
        scroll_y = tk.Scrollbar(left_frame, orient="vertical", command=self.text.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
    
        scroll_x = tk.Scrollbar(left_frame, orient="horizontal", command=self.text.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
    
        self.text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    
        # BUTTONS (bottom of left panel)
        button_frame = tk.Frame(left_frame)
        button_frame.grid(row=2, column=0, pady=5)
    
        tk.Button(button_frame, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(right_frame, text="Reset", command=self.reset).grid(row=3, column=0, pady=20, sticky="ew")
    
        # RIGHT PANEL CONTENT (controls)
        tk.Label(
            right_frame, 
            text="Settings", 
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, pady=10, sticky="n")
        
        tk.Label(
            right_frame, 
            text="Send Interval"
        ).grid(row=1, column=0, pady=5, sticky="w", padx=10)
        
        dropdown = tk.OptionMenu(right_frame, self.interval_var, *intervals.keys())
        dropdown.grid(row=2, column=0, padx=10, sticky="ew")

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

    # Start class that starts publishing the data to the log on a thread.
    def start(self):
        if self.publisher.running:
            self.log("Already running!")
            return
        
        def get_interval():
            return self.interval_map[self.interval_var.get()]
        
        self.log("Publisher has been started")
        threading.Thread(
            target=self.publisher.start, 
            args=(self.log, get_interval),
            daemon=True
        ).start()

    # Stop class that stops publishing data.
    def stop(self):
        self.publisher.stop()
        self.log("Publisher has been stopped.")
        
    # Resets the publisher
    def reset(self):
        # resets interval
        self.interval_var.set("10 sec")
        
        # clear log window
        self.text.delete("1.0", tk.END)
        
        # send reset message to subscriber
        reset_message = json.dumps({
            "event": "RESET",
            "timestamp": time.time()
        })
        
        try:
            self.publisher.client.publish(TOPIC, reset_message)
            self.log("System reset: interval set to 10 sec and log cleared.")
            self.stop()
            self.start()
        except:
            self.log("Reset failed: MQTT not connected.")

# Main class to run Publisher.
if __name__ == "__main__":
    root = tk.Tk()
    app = PublisherGUI(root)
    root.mainloop()