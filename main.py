import os
import meshtastic
import meshtastic.tcp_interface
import requests
from pubsub import pub
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
radio_hostname = "meshtastic.local"  # Change to IP if needed
iface = meshtastic.tcp_interface.TCPInterface(radio_hostname)

import requests

def sendPushoverMessage(message, title):
    """Send a message to Pushover."""
    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message,
        "title": title,
    }
    response = requests.post(PUSHOVER_API_URL, data=payload)
    
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

# Callback function to log received messages
def onReceive(packet, interface):
    """When Message Received"""
    if "decoded" in packet and "text" in packet["decoded"]:
        sender_id = packet["fromId"]
        message = packet["decoded"]["text"]

        # Check if message came from MQTT (no rxSnr)
        is_mqtt = "rxSnr" not in packet
        source_type = "📡" if not is_mqtt else "🌐"

        # Lookup sender's node information
        sender_name = sender_id  # Default to sender ID
        for node in interface.nodes.values():
            if node["num"] == packet["from"]:
                sender_name = node["user"]["longName"]
                break  # Stop searching once we find the node

        print(f"{source_type} 📩 Message from {sender_name}: {message}")
        sendPushoverMessage(f"{source_type}: {message}", f"📩 Message from {sender_name}")

def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print("Connection established")
    sendPushoverMessage("Meshtastic Connected", f"Meshtastic Connected")

def onDisconnection(interface, topic=pub.AUTO_TOPIC):  
    print("⚠️ Connection lost! Trying to reconnect...")
    sendPushoverMessage("Meshtastic Disconnected", "⚠️ Connection lost!")

    while True:  # Keep trying to reconnect
        try:
            iface = meshtastic.tcp_interface.TCPInterface(radio_hostname)
            break  # Exit the loop when reconnected
        except Exception as e:
            print(f"Retrying connection in 10 seconds... ({e})")
            time.sleep(10)  # Wait and retry

# Subscribe to incoming messages
pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")
pub.subscribe(onDisconnection, "meshtastic.connection.lost")

try:
    print("✅ Listening for messages... Press Ctrl+C to stop.")
    while True:
        pass  # Keep script running
except KeyboardInterrupt:
    print("\n⏹ Stopping listener.")
    iface.close()
