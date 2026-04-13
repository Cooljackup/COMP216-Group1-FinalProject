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
BROKER = "127.0.0.1"
TOPIC = "TOPIC"

# Publisher class that sends the data to the broker.
class Publisher:
    def __init__(self):
        self.client = mqtt.Client()
        self.generator = DataGenerator()
        self.running = False
    
    # Format data class that formats the data into a json.
    def format_data(self, value):
        return json.dumps({"packet_id": str(uuid.uuid4()), "timestamp": time.time(), "value": value})
    
    # Start class that connects to the broker and sends the formatted data as a json and stores it as a log variable.
    def start(self, log):
        self.client.connect(BROKER)
        self.running = True

        while self.running:
            data = self.format_data(self.generator.get_value())
            self.client.publish(TOPIC, data)
            log(f"Sent: {data}")
            time.sleep(1)

    # Stop class that disconnects from the broker.
    def stop(self):
        self.client.disconnect()
        self.running = False

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
        self.root.title("Publisher")
        self.root.geometry("600x400")

        self.text = tk.Text(self.root, height=15, width=60)
        self.text.pack(pady=10)

        tk.Button(self.root, text="Start", command=self.start, width=10).pack(side=tk.LEFT, padx=150)
        tk.Button(self.root, text="Stop", command=self.stop, width=10).pack(side=tk.LEFT)

    # Log class that stores the data into a message and inserts it into a message.
    def log(self, message):
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)

    # Start class that starts publishing the data to the log on a thread.
    def start(self):
        self.log("Publisher has been started.")
        threading.Thread(target=self.publisher.start, args=(self.log,)).start()

    # Stop class that stops publishing data.
    def stop(self):
        self.publisher.stop()
        self.log("Publisher has been stopped.")

# Main class to run Publisher.
if __name__ == "__main__":
    root = tk.Tk()
    app = PublisherGUI(root)
    root.mainloop()