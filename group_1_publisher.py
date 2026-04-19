# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk
import paho.mqtt.client as mqtt
import json
import uuid
import time
import random
import threading

# Import DataGenerator.
from group_1_data_generator import DataGenerator

# Import EmailAlert.
from group_1_emailAlert import EmailAlert

# Broker connection and Topic with amount of open windows.
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "TEMPERATURE"
open_windows = 0

# Publisher class that sends the data to the broker.
class Publisher:
    def __init__(self):

        # Instance variables.
        self.client = mqtt.Client()
        self.generator = DataGenerator()
        self.running = False
        self.publisher_id = str(uuid.uuid4())
        self.interval = 10  # default
        self.skip_block = False
        self.skip_count = 0
        self.block_chance = 0.10
        self.wild_chance = 0.10
        self.loss_chance = 0.10
        self.state = "STOPPED"
        
        self.email_alert = EmailAlert()
        self.emailAddresses = [] # ADD EMAILS HERE!
        
    # Format data class that formats the data into a json.
    def format_data(self, value):
        return json.dumps({"publisher_id": self.publisher_id, "packet_id": str(uuid.uuid4()), "timestamp": time.time(), "value": value})
    
    # Start class that connects to the broker and sends the formatted data as a json and stores it as a log variable.
    def start(self, log, get_interval, get_settings):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        self.running = True
        self.state = "RUNNING"
        
        # Sends the start event.
        start_message = json.dumps({"event": "START", "timestamp": time.time()})
        self.client.publish(TOPIC, start_message)
        log("Publisher START event sent.")

        # Runs while status is set to running.
        while self.running:
            self.interval = get_interval()
            self.interval, self.block_chance, self.wild_chance, self.loss_chance = get_settings()

            # Random block skip between 3 and 5 that happens about roughly 10% of the time. (Customizable.)
            if not self.skip_block and random.random() < self.block_chance:
                self.skip_block = True
                self.skip_count = random.randint(3, 5)
                log(f"ERROR. Block skip started with a total of {self.skip_count} blocked transmissions.")

            if self.skip_block:
                log("ERROR. Transmission blocked.")
                self.skip_count -= 1

                if self.skip_count <= 0:
                    self.skip_block = False
                    log("Block skip has ended.")
            
            # If the block skip doesn't happen, generates a normal value.
            else:
                value = self.generator.get_value()

                # Wild data value with a range of -150 and 150 that happens about roughly 10% of the time. (Customizable.)
                if random.random() < self.wild_chance:
                    value = random.uniform(-150, 150)
                    log(f"ERROR. Wild data value of {value} was transmitted!")
                    
                    # sends email alert to all subscribed emails in the array.
                    for email in self.emailAddresses:
                        self.email_alert.send_alert(email, "Bad Data Alert", f"A wild data value of {value} was sent!")

                data = self.format_data(value)
                
                # Missed transmission that happens about roughly 10% of the time. (Customizable.)
                if random.random() < self.loss_chance:
                    log("ERROR. Packet lost. Transmission skipped.")
                else:
                    self.client.publish(TOPIC, data)
                    log(f"Sent: {data} (interval: {self.interval}s).")

            # Handles the interval.
            elapsed = 0
            while self.running and elapsed < self.interval:
                time.sleep(0.2)
                elapsed += 0.2
                new_interval = get_interval()
                if new_interval != self.interval:
                    self.interval = new_interval
                    break

    # Stop class that disconnects from the broker.
    def stop(self):
        self.running = False
        self.state = "STOPPED"
        
        # Formats the stop message and sends the message to notify the subscribers that the publisher is shutting down.
        stop_message = json.dumps({"event": "STOP", "publisher_id": self.publisher_id, "timestamp": time.time()})
        try:
            self.client.publish(TOPIC, stop_message)
        except:
            pass
    
        self.client.loop_stop()
        self.client.disconnect()    

# PublisherGUI class that creates and displays the GUI.
class PublisherGUI:
    def __init__(self, root, app_root):

        # Instance variables.
        self.root = root
        self.app_root = app_root
        self.publisher = Publisher()
        global open_windows
        open_windows += 1
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # Close class to handle closing a window and handle closing the program when there are no windows left.
    def close(self):
        global open_windows

        try:
            self.publisher.stop()
        except:
            pass

        open_windows -= 1
        self.root.destroy()
        
        if open_windows == 0:
            self.app_root.quit()

    # GUI setup.
    def gui_setup(self):

        # Instance variables.
        self.interval_var = tk.StringVar(value="10 seconds")
        self.block_var = tk.StringVar(value="10%")
        self.wild_var = tk.StringVar(value="10%")
        self.loss_var = tk.StringVar(value="10%")
        intervals = {"1 second": 1, "5 seconds": 5, "10 seconds": 10, "Hourly": 3600, "Daily": 86400, "Weekly": 604800, "Monthly": 2592000}
        self.interval_map = intervals
        percentages = {"0%": 0, "10%": 10, "20%": 20, "30%": 30, "40%": 40, "50%": 50, "60%": 60, "70%": 70, "80%": 80, "90%": 90, "100%": 100}
        self.percentage_map = percentages
        
        # Main window properties.
        self.root.title(f"Publisher - {TOPIC}")
        self.root.geometry("800x500")
        self.root.minsize(500, 425)
        self.root.grid_columnconfigure(1, minsize=200)

        # Grid layout configuration. (2 columns: Left = Log, Right = Controls.)
        self.root.columnconfigure(0, weight=3)  # main area
        self.root.columnconfigure(1, weight=1)  # side panel
        self.root.rowconfigure(0, weight=1)
    
        # Left column & content. (Text log & scrollbars.)
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        self.text = tk.Text(left_frame, wrap="none")
        self.text.grid(row=0, column=0, sticky="nsew")
    
        scroll_y = tk.Scrollbar(left_frame, orient="vertical", command=self.text.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = tk.Scrollbar(left_frame, orient="horizontal", command=self.text.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        # Right column & content. (Settings & controls.)
        right_frame = tk.Frame(self.root, bd=2, relief="groove")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(99, weight=1)

        tk.Label(right_frame, text="Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=10, sticky="n")

        # Send Interval.
        tk.Label(right_frame, text="Send Interval:").grid(row=1, column=0, pady=5, sticky="w", padx=10)
        dropdown = tk.OptionMenu(right_frame, self.interval_var, *intervals.keys())
        dropdown.grid(row=2, column=0, padx=10, sticky="ew")

        # Packet loss.
        tk.Label(right_frame, text="Packet Loss %:").grid(row=5, column=0, pady=5, sticky="w", padx=10)
        dropdown = tk.OptionMenu(right_frame, self.loss_var, *percentages.keys())
        dropdown.grid(row=6, column=0, padx=10, sticky="ew")

        # Wild Value.
        tk.Label(right_frame, text="Wild Value %:").grid(row=7, column=0, pady=5, sticky="w", padx=10)
        dropdown = tk.OptionMenu(right_frame, self.wild_var, *percentages.keys())
        dropdown.grid(row=8, column=0, padx=10, sticky="ew")

        # Block Skip.
        tk.Label(right_frame, text="Block Skip %:").grid(row=9, column=0, pady=5, sticky="w", padx=10)
        dropdown = tk.OptionMenu(right_frame, self.block_var, *percentages.keys())
        dropdown.grid(row=10, column=0, padx=10, sticky="ew")
        
        # Reset.
        tk.Button(right_frame, text="Reset", command=self.reset).grid(row=11, column=0, pady=75, sticky="ew")

        # Bottom row & content. (Underneath left column.)
        button_frame = tk.Frame(left_frame)
        button_frame.grid(row=2, column=0, pady=5)
    
        tk.Button(button_frame, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="New Publisher", command=self.open_new_window, width=15).pack(side=tk.LEFT, padx=5)

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

    # Open new window class that allows more than one Publisher window open at a time.
    def open_new_window(self):
        new_win = tk.Toplevel(self.app_root)
        PublisherGUI(new_win, self.app_root)
    
    # Start class that starts publishing the data to the log on a thread.
    def start(self):
        if self.publisher.running:
            self.log("ERROR. Already running!")
            return
        
        # Gets the selected interval from the dropdown and converts it into seconds.
        def get_interval():
            return self.interval_map[self.interval_var.get()]
        
        # Gets all random chance settings from the dropdowns and converts them into percentages.
        def get_settings():
            return (self.interval_map[self.interval_var.get()], self.percentage_map[self.block_var.get()] / 100, self.percentage_map[self.wild_var.get()] / 100, self.percentage_map[self.loss_var.get()] / 100)
        
        self.log("Publisher has been started.")
        threading.Thread(target=self.publisher.start, args=(self.log, get_interval, get_settings), daemon=True).start()

    # Stop class that stops publishing data.
    def stop(self):
        self.publisher.stop()
        self.log("Publisher has been stopped.")
        
    # Reset class that resets the publisher.
    def reset(self):
        # Resets interval and percentage variables.
        self.interval_var.set("10 seconds")
        self.block_var.set("10%")
        self.wild_var.set("10%")
        self.loss_var.set("10%")
        
        # Clears the log window.
        self.text.delete("1.0", tk.END)
        
        # Sends the reset message to Subscriber and resets the Subscriber's window.
        reset_message = json.dumps({"event": "RESET", "timestamp": time.time()})
        try:
            self.publisher.client.publish(TOPIC, reset_message)
            self.log("System reset: Interval reset to 10 seconds and log was cleared.")
            self.stop()
            self.start()
        except:
            self.log("ERROR. Reset failed: MQTT not connected.")

# Main class to run Publisher.
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    first_window = tk.Toplevel(root)
    PublisherGUI(first_window, root)
    root.mainloop()