# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import tkinter as tk
import paho.mqtt.client as mqtt
import json

# Broker connection and Topic.
### TEMPORARY. Just for testing locally.
BROKER = "127.0.0.1"
TOPIC = "TOPIC"

# Subscriber class that receives data from the broker.
class Subscriber:
    def __init__(self, log):
        self.running = False
        self.client = mqtt.Client()
        self.log = log

    # Decode data class that decodes the incoming data from the broker and sends it to the log.
    def decode_data(self, client, userdata, message):
        data = json.loads(message.payload.decode())
        value = data["value"]
        self.log(f"Received: {value}")
    
    # Start class that connects to the broker and receives the formatted data.
    def start(self):
        self.client.on_message = self.decode_data
        self.client.connect(BROKER)
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
        self.root = root
        self.subscriber = Subscriber(self.log)
        self.gui_setup()

        # To properly close the program.
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # GUI setup.
    def gui_setup(self):
        self.root.title("Subscriber")
        self.root.geometry("400x400")

        self.text = tk.Text(self.root, height=15, width=40)
        self.text.pack(pady=10)

        tk.Button(self.root, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=75)
        tk.Button(self.root, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT)

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

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