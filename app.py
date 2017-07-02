import os
from simple_fedq.app import app

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.realpath(__file__))
    local_config_file = os.path.join(base_dir, 'settings_local.py')
    if os.path.isfile(local_config_file):
        app.config.from_pyfile(local_config_file)
    app.run(host="0.0.0.0", port=8080, debug=True)
