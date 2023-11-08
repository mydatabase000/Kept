import requests

# Define maximum message lengths for each notification type
MAX_LENGTHS = {
    "telegram": 4096,
    "discord": 2000,
    "pushover": 1024,
}

class Notifier:
    def __init__(self, args):
        # Store only relevant arguments for the notification types
        self.args = {
            key: value
            for key, value in vars(args).items()
            if key in MAX_LENGTHS.keys() and value is not None
        }

    def send(self, message: str):
        # Send the message to each notification type
        for type in self.args:
            if len(message) > MAX_LENGTHS[type]:
                # If message exceeds max length, split and send in parts
                for i in range(0, len(message), MAX_LENGTHS[type]):
                    self.send(message[i : i + MAX_LENGTHS[type]])
                return
            else:
                # Call the specific method for the notification type
                getattr(self, type)(message)

    def telegram(self, message):
        # Send message via Telegram
        token, chat_id = self.args["telegram"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)

    def discord(self, message):
        # Send message via Discord
        url = self.args["discord"]
        data = {"username": "Microsoft Rewards Farmer", "content": message}
        requests.post(url, data=data)

    def pushover(self, message):
        # Send message via Pushover
        token, user_key = self.args["pushover"]
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": token,
            "user": user_key,
            "message": message
        }
        requests.post(url, data=data)
