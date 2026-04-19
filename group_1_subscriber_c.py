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
    def __init__(self, log, update_graph):

        # Instance variables.
        self.running = False
        self.log = log
        self.update_graph = update_graph
        self.minimum_temperature = 35
        self.maximum_temperature = 65

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
                    publisher_id = data.get("publisher_id", "default")
                    self.log(f"{publisher_id} stopped sending data.")
                    self.update_graph(publisher_id, None)
                return
    
            # Handle normal data
            if "value" in data:
                publisher_id = data.get("publisher_id", "default")
                value = data["value"]
                
                # Detect wild/out-of-range values.
                if value < self.minimum_temperature or value > self.maximum_temperature:
                    self.log(f"ERROR: Wild value detected: {value} from {publisher_id}.")
                else:
                    self.log(f"Received: {value} from {publisher_id}.")
    
                # Updates the graph.
                self.update_graph(publisher_id, value)
                
        except Exception as error:
            self.log(f"ERROR. There was an error processing the message: {error}.")
        
    # On connect class to handle connecting to the broker with the selected topic.
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
        self.subscriber = Subscriber(self.log, self.update_graph)
        self.history = []
        self.max_points = 60
        self.graph_dimensions_left = 50
        self.graph_dimensions_right = 740
        self.graph_dimensions_top = 50
        self.graph_dimensions_bottom = 325
        self.graph_width = self.graph_dimensions_right - self.graph_dimensions_left
        self.graph_height = self.graph_dimensions_bottom - self.graph_dimensions_top
        self.graph_grid_steps_x = 10
        self.graph_grid_steps_y = 10
        self.data_history = {}
        self.next_color_index = 0
        self.colors = ["red", "green", "blue", "orange", "purple", "cyan"]
        self.color_map = {}
        self.gui_setup()

        # To properly close the window.
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
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Grid layout. (1 column, 3 rows.)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=5)
        self.root.rowconfigure(1, weight=2)
        self.root.rowconfigure(2, weight=0)

        # Row 1. Temperature.
        right_frame = tk.Frame(self.root, bd=2, relief="groove")
        right_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.graph = tk.Canvas(right_frame, bg="black", height=250)
        self.graph.pack(fill="both", expand=True, padx=10, pady=10)

        # Title, grid lines, & graph box.
        self.graph.create_text((self.graph_dimensions_left + self.graph_dimensions_right) / 2, self.graph_dimensions_top - 25, text="Temperature", fill="white", font=("Arial", 12, "bold"))
        for i in range(self.graph_grid_steps_x + 1):
            x = self.graph_dimensions_left + i * ((self.graph_dimensions_right - self.graph_dimensions_left) / self.graph_grid_steps_x)
            self.graph.create_line(x, self.graph_dimensions_top, x, self.graph_dimensions_bottom, fill="#333333")
        for i in range(self.graph_grid_steps_y + 1):
            y = self.graph_dimensions_top + i * ((self.graph_dimensions_bottom - self.graph_dimensions_top) / self.graph_grid_steps_y)
            self.graph.create_line(self.graph_dimensions_left, y, self.graph_dimensions_right, y, fill="#333333")
        self.graph.create_rectangle(self.graph_dimensions_left, self.graph_dimensions_top, self.graph_dimensions_right, self.graph_dimensions_bottom, outline="white")

        # Degrees & degrees title.
        steps = 15
        graph_height = self.graph_dimensions_bottom - self.graph_dimensions_top
        for i in range(steps + 1):
            val = self.bar_min + i * (self.bar_max - self.bar_min) / steps
            ratio = i / steps
            y = self.graph_dimensions_bottom - (ratio * graph_height)
            self.graph.create_text(self.graph_dimensions_left - 15, y, text=f"{val:.0f}", fill="white", font=("Arial", 10))
        self.graph.create_text(self.graph_dimensions_left - 40, (self.graph_dimensions_top + self.graph_dimensions_bottom) / 2, text="Degrees (°C)", fill="white", font=("Arial", 10), angle=90)

        # Samples title.
        self.graph.create_text((self.graph_dimensions_left + self.graph_dimensions_right) / 2, self.graph_dimensions_bottom + 20, text="Samples", fill="white", font=("Arial", 10))

        # Row 2. Log.
        left_frame = tk.Frame(self.root, height=120)
        left_frame.grid(row=1, column=0, sticky="nsew")
        left_frame.grid_propagate(False)
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

    # Update graph class to update the graph when a value is received.
    def update_graph(self, publisher_id, value):
        self.root.after(0, self._update_graph_safe, publisher_id, value)
    
    # Update graph safe class handles both updating and deleting lines and retaining their colour if resubscribed.
    def _update_graph_safe(self, publisher_id, value):
        if value is None:
            self.data_history.pop(publisher_id, None)
            self.draw_graph()
            return

        if publisher_id not in self.data_history:
            self.data_history[publisher_id] = []

            if publisher_id not in self.color_map:
                self.color_map[publisher_id] = self.colors[self.next_color_index % len(self.colors)]
                self.next_color_index += 1

        self.data_history[publisher_id].append(value)
        if len(self.data_history[publisher_id]) > self.max_points:
            self.data_history[publisher_id].pop(0)

        self.draw_graph()
    
    # Draw graph class to handle updating the graph with lines. Handles setting colours and where to draw to.
    def draw_graph(self):
        self.graph.delete("line")
        for publisher_id, values in self.data_history.items():
            if len(values) < 2:
                continue

            color = self.color_map[publisher_id]
            points = []
            for i, v in enumerate(values):
                x = self.graph_dimensions_left + i * ((self.graph_dimensions_right - self.graph_dimensions_left) / self.max_points)
                v = max(self.bar_min, min(self.bar_max, v))
                ratio = (v - self.bar_min) / (self.bar_max - self.bar_min)
                y = self.graph_dimensions_bottom - (ratio * (self.graph_dimensions_bottom - self.graph_dimensions_top))
                points.append((x, y))

            for i in range(len(points) - 1):
                self.graph.create_line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], fill=color, width=2, tags="line")
    
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