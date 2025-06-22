import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from threading import Lock
from pathlib import Path
import logging
import os

class MQTTHandler:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MQTTHandler, cls).__new__(cls)
                logging.getLogger(__name__).info("Created new MQTTHandler instance")
            else:
                logging.getLogger(__name__).info("Reusing existing MQTTHandler instance")
        return cls._instance

    def __init__(self, port=1883, client_id="flask_mqtt_client", broker='localhost', username=None, password=None):
        if not hasattr(self, 'initialized'):
            # Load environment variables from mqtt.env in the same directory
            env_path = Path(__file__).parent / "mqtt.env"
            load_dotenv(dotenv_path=env_path)
            # Get username and password from environment if not provided on run
            if username is None:
                username = os.getenv("MQTT_USERNAME")
            if password is None:
                password = os.getenv("MQTT_PASSWORD")
            # Check for a configured broker location, if not assume localhost, unless specified on run
            broker_url = os.getenv("MQTT_BROKER")
            if broker_url:
                self.broker = broker_url
            else:
                self.broker = broker
            # Check for a configured broker port, if not assume 1883, unless specified on run
            broker_port = os.getenv("MQTT_PORT")
            if broker_port:
                self.port = broker_port
            else:
                self.port = port
            # Check for a configured client id, if not assume flask_mqtt_client, unless specified on run
            mqtt_client_id = os.getenv("MQTT_CLIENT_ID")
            if mqtt_client_id:
                self.client_id = mqtt_client_id
            else:
                self.client_id = client_id
            # Setup MQTT Client
            self.client = mqtt.Client(client_id=client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.logger = logging.getLogger(__name__)
            self.subscriptions = {}
            self.initialized = True
            # Enable automatic reconnection with exponential backoff
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            # Set authentication credentials if provided
            if username and password:
                self.client.username_pw_set(username, password)
                self.connect()
            else:
                self.logger.warning("MQTTHandler not connecting: username and/or password not provided.")

    def connect(self):
        try:
            if not self.client.is_connected():
                self.client.connect(self.broker, self.port, keepalive=60)
                self.client.loop_start()
                self.logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            else:
                self.logger.debug("Already connected to MQTT broker")
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            self.logger.info("Will retry connection due to failure")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT client connected successfully")
            # Restore subscriptions on successful connection
            for topic in self.subscriptions:
                self.subscribe(topic)
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            self.logger.error(f"Failed to connect with code {rc}: {error_messages.get(rc, 'Unknown error')}")
            self.logger.info("Will retry connection due to failure")

    def on_disconnect(self, client, userdata, rc):
        self.logger.warning(f"Disconnected from MQTT broker with code {rc}")
        if rc != 0:  # Unexpected disconnection
            self.logger.info("Attempting to reconnect to MQTT broker")
            # Paho's automatic reconnection will handle retrying

    def on_message(self, client, userdata, msg):
        callback = self.subscriptions.get(msg.topic)
        if callback:
            try:
                callback(msg)
            except Exception as e:
                self.logger.error(f"Error processing message on {msg.topic}: {e}")

    def subscribe(self, topic, callback=None):
        self.subscriptions[topic] = callback
        if self.client.is_connected():
            self.client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")

    def publish(self, topic, message, qos=0):
        try:
            self.client.publish(topic, message, qos)
            self.logger.info(f"Published to {topic}: {message}")
        except Exception as e:
            self.logger.error(f"Error publishing to {topic}: {e}")

    def disconnect(self):
        try:
            if self.client.is_connected():
                self.client.loop_stop()
                self.client.disconnect()
                self.logger.info("Disconnected from MQTT broker")
        except Exception as e:
            self.logger.error(f"Error disconnecting from MQTT broker: {e}")

    def is_connected(self):
        """
        Returns True if the MQTT client is currently connected to the broker.
        """
        return self.client.is_connected()

    def get_subscribed_topics(self):
        """
        Returns a list of topics the client is currently subscribed to.
        """
        return list(self.subscriptions.keys())