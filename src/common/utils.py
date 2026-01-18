def log_message(message):
    print(f"[LOG] {message}")


def load_config(config_file):
    import json

    with open(config_file, "r") as file:
        return json.load(file)
