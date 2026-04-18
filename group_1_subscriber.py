# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk
import paho.mqtt.client as mqtt
import json

# Broker connection and Topic.
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "TEMPERATURE"

# Subscriber class that receives data from the broker.
class Subscriber:
    def __init__(self, log, update_ui):

        # Instance variables.
        self.running = False
        self.client = mqtt.Client()
        self.log = log
        self.minimum_temperature = 38
        self.maximum_temperature = 62
        self.update_ui = update_ui

    def decode_data(self, client, userdata, message):
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

                # Update GUI.
                self.update_ui(value)
    
        except Exception as error:
            self.log(f"ERROR. There was an error processing the message: {error}.")
        
    def on_connect(self, client, userdata, flags, rc):
        self.log("Connected to broker.")
        client.subscribe(TOPIC)    
    
    # Start class that connects to the broker and receives the formatted data.
    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.decode_data
        self.client.connect(BROKER, PORT, 60)
        self.client.subscribe(TOPIC)
        self.client.loop_start()
        self.running = True

    # Stop class that disconnects from the broker.
    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.running = False

# SubscriberGUI class that creates and displays the GUI.
class SubscriberGUI:
    def __init__(self, root):

        # Instance variables.
        self.root = root
        self.subscriber = Subscriber(self.log, self.update_bar)
        self.bar_min = 35
        self.bar_max = 65
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # GUI setup.
    def gui_setup(self):
        self.root.title(f"Subscriber - {TOPIC}")
        self.root.geometry("800x500")
        self.root.minsize(500, 425)
        self.root.grid_columnconfigure(1, minsize=200)

        # Grid layout configuration. (2 columns: Left = Log, Right = Temperature bar.)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
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

        # Right column & content. (Temperature bar.)
        right_frame = tk.Frame(self.root, bd=2, relief="groove")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.canvas = tk.Canvas(right_frame, width=120, height=380)
        self.canvas.pack(pady=10)
        self.canvas.create_rectangle(10, 10, 110, 340, fill="black", outline="silver", width=2)

        label_val = self.bar_min
        steps = 30
        for i in range(steps + 1):
            y = 335 - i * (320 / steps)
            self.canvas.create_text(30, y, text=f"{label_val:.0f}", fill="white", font=("Arial", 7))
            label_val += (self.bar_max - self.bar_min) / steps

        self.bar = self.canvas.create_rectangle(50, 340, 90, 340, fill="red")

        self.value_label = tk.Label(right_frame, text="Current: --")
        self.value_label.pack()

        # Bottom row & content. (Underneath left column.)
        button_frame = tk.Frame(left_frame)
        button_frame.grid(row=2, column=0, pady=5)

        tk.Button(button_frame, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT, padx=5)

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.root.after(0, self._log_safe, message)
    
    def _log_safe(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

    # Update bar.
    def update_bar(self, value):
        self.root.after(0, self._update_bar_safe, value)

    def _update_bar_safe(self, value):
        is_wild = (value < self.subscriber.minimum_temperature or value > self.subscriber.maximum_temperature)

        # If the value transmitted is wild, it turns the bar yellow and doesn't update bar.
        if is_wild:
            color = "yellow"
            self.canvas.itemconfig(self.bar, fill=color)
            return

        # Updates bar if normal.
        display_value = max(self.bar_min, min(self.bar_max, value))
        ratio = (display_value - self.bar_min) / (self.bar_max - self.bar_min)
        top_y = 340 - ratio * 320
        self.canvas.coords(self.bar, 50, top_y, 90, 340)
        self.canvas.itemconfig(self.bar, fill="green")
        self.value_label.config(text=f"Current: {value:.2f}")

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
    app = SubscriberGUI(root)
    root.mainloop()