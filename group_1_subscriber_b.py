import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import paho.mqtt.client as mqtt
import json


class Subscriber_B(tk.Tk):
    BROKER = "test.mosquitto.org"
    PORT = 1883
    TOPIC = "TEMPERATURE"
    MAX_POINTS = 50

    def __init__(self):
        super().__init__()

        self.title("Temperature Monitor")
        self.geometry("650x750")
        self.minsize(500, 400)

        # Data
        self.values = []

        # creates MQTT client instance
        self.client = mqtt.Client()
        self.client.on_message = self.on_message # assigns callback function

        # calls function that creates all UI elements
        self.build_ui()

        # calls on_close() to quit the app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
    
        # allows scrolling content
        canvas = tk.Canvas(container)
        scrollbar_y = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    
        scroll_frame = tk.Frame(canvas)
        scroll_frame.config(width=900)
    
        # updates the scrollable area size every time layout changes
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
        # links scrollbars to canvas
        self.canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
    
        # places ui elements in window
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
    
        # creates graph container
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], linewidth=2) # creates line for live updating graph
    
        self.setup_plot()
    
        center_frame = tk.Frame(scroll_frame)
        center_frame.pack(expand=True)
        
        # places matplotlib into tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=center_frame)
        self.canvas.get_tk_widget().pack(pady=20)        
    
        # Status log with last 5 events
        self.status_text = tk.Text(scroll_frame, height=5, width=80, state="disabled")
        self.status_text.pack(pady=5)
    
        # shows the current value
        self.info_label = tk.Label(scroll_frame, text="Current: --.- °C")
        self.info_label.pack(pady=5)
    
        # Buttons
        btn_frame = tk.Frame(scroll_frame)
        btn_frame.pack(pady=10)
    
        tk.Button(btn_frame, text="Start", command=self.start_mqtt, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=self.stop_mqtt, width=10).pack(side=tk.LEFT, padx=5)

    def setup_plot(self):
        self.ax.set_title("Indoor Temperature")
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("°C")
        self.ax.grid(True)

    def start_mqtt(self):
        try:
            self.client.connect(self.BROKER, self.PORT, 60)     # connects to broker
            self.client.subscribe(self.TOPIC)                   # listens to the TOPIC
            self.client.loop_start()                            # runs MQTT in the background
            self.set_status("Connected")
        except Exception:
            self.set_status("Connection Failed")

    def stop_mqtt(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.set_status("Disconnected")

    def on_message(self, client, userdata, message):            # runs when MQTT message arrives
        try:
            data = json.loads(message.payload.decode())         # converts JSON string into dictionary

            event = data.get("event")

            if event == "RESET":
                self.values.clear()
                self.set_status("Reset received")

            elif event == "STOP":
                self.set_status("Publisher stopped")

            elif event == "START":
                self.set_status("Publisher started")

            elif "value" in data:
                self.add_value(data["value"])
                self.set_status("Receiving data...")

            self.after(0, self.update_display)                  # updates GUI from MQTT thread

        except Exception as e:
            print("Error:", e)

    # adds new value - temperature
    def add_value(self, value):
        if len(self.values) >= self.MAX_POINTS:
            self.values.pop(0)
        self.values.append(value)

    def set_status(self, text):
        self.log_status(f"{text}")

    def update_display(self):
        if not self.values:
            return

        # updates plotted line
        self.line.set_data(range(len(self.values)), self.values)

        # adjusts the Y axis
        self.ax.set_ylim(min(self.values) - 1, max(self.values) + 1)
        self.ax.relim()
        self.ax.autoscale_view()

        self.info_label.config(text=f"Current: {self.values[-1]:.1f} °C")

        # redraws the graph
        self.canvas.draw_idle()
    
    def log_status(self, message):
        self.status_text.config(state="normal")
    
        # Add new message
        self.status_text.insert("end", message + "\n")
    
        # Keep only last 5 lines
        lines = self.status_text.get("1.0", "end").split("\n")
        if len(lines) > 6:  # 5 lines + trailing empty
            self.status_text.delete("1.0", f"{len(lines)-6}.0")
    
        self.status_text.config(state="disabled")
        self.status_text.see("end")    

    # runs when window closes
    def on_close(self):
        self.stop_mqtt()    # stops MQTT
        self.destroy()      # closes the app


if __name__ == "__main__":
    app = Subscriber_B()
    app.mainloop()