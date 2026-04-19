# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk
import paho.mqtt.client as mqtt
import json

# Broker connection and Topic with amount of open windows.
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "TEMPERATURE"
open_windows = 0

# Subscriber class that receives data from the broker.
class Subscriber:
    def __init__(self, log):

        # Instance variables.
        self.running = False
        self.log = log
        self.minimum_temperature = 38
        self.maximum_temperature = 62

    def decode_data(self, client, userdata, message):
        if not self.running: #Stopping new callbacks from running after the subscriber has hit stop.
            return
        try:
            data = json.loads(message.payload.decode())
    
            # Handle RESET event
            if "event" in data:
                if data["event"] == "RESET":
                    self.log("Publisher RESET received.")
                elif data["event"] == "STOP":
                    self.log("Publisher STOP received.")
                return
    
            # Handle normal data
            if "value" in data:
                value = data["value"]
                
                # Detect wild/out-of-range values.
                if value < self.minimum_temperature or value > self.maximum_temperature:
                    self.log(f"ERROR: Wild value detected: {value}")
                else:
                    self.log(f"Received: {value}")
    
        except Exception as error:
            self.log(f"ERROR. There was an error processing the message: {error}.")
        
    def on_connect(self, client, userdata, flags, rc):
        self.log("Connected to broker.")
        client.subscribe(TOPIC)    
    
    # Start class that connects to the broker and receives the formatted data.
    def start(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.decode_data
        self.running = True
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    # Stop class that disconnects from the broker.
    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

# SubscriberGUI class that creates and displays the GUI.
class SubscriberGUI:
    def __init__(self, root, app_root):

        # Instance variables.
        self.root = root
        self.app_root = app_root
        global open_windows
        open_windows += 1
        self.bar_min = 35
        self.bar_max = 65
        self.subscriber = Subscriber(self.log)
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    # Close class to handle closing a window and handle closing the program when there are no windows left.
    def close(self):
        global open_windows
        try:
            self.subscriber.stop()
        except:
            pass

        open_windows -= 1
        self.root.destroy()
        if open_windows == 0:
            self.app_root.quit()
    
    # GUI setup.
    def gui_setup(self):
        self.root.title(f"Subscriber - {TOPIC}")
        self.root.geometry("800x500")
        self.root.minsize(500, 425)

        # Grid layout. (1 column, 3 rows.)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=4)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        # Row 1. Temperature.
        right_frame = tk.Frame(self.root, bd=2, relief="groove")
        right_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Row 2. Log.
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=1, column=0, sticky="nsew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        self.text = tk.Text(left_frame, wrap="none")
        self.text.grid(row=0, column=0, sticky="nsew")

        scroll_y = tk.Scrollbar(left_frame, orient="vertical", command=self.text.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = tk.Scrollbar(left_frame, orient="horizontal", command=self.text.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")

        # Row 3. Buttons.
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=2, column=0, pady=5)

        tk.Button(button_frame, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="New Subscriber", command=self.open_new_window, width=15).pack(side=tk.LEFT, padx=5)

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.root.after(0, self._log_safe, message)
    
    def _log_safe(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
    
    # Open new window class that allows more than one Subscriber window open at a time.
    def open_new_window(self):
        new_window = tk.Toplevel(self.app_root)
        SubscriberGUI(new_window, self.app_root)
    
    # Start class that starts receiving the published data to the log.
    def start(self):
        self.log("Subscriber has been started.")
        self.subscriber.start()
    
    # Stop class that stops receiving the publishing data.
    def stop(self):
        self.subscriber.stop()
        self.log("Subscriber has been stopped.")

# Main class to run Subscriber.
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    first_window = tk.Toplevel(root)
    SubscriberGUI(first_window, root)
    root.mainloop()