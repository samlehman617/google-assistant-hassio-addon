#!/bin/bash
set -e

CONFIG_PATH=/data/options.json
CLIENT_JSON=/data/client.json
CRED_JSON=/data/cred.json

CLIENT_SECRETS=$(jq --raw-output '.client_secrets' $CONFIG_PATH)
PROJECT_ID=$(jq --raw-output '.project_id' $CONFIG_PATH)
MODEL_ID=$(jq --raw-output '.model_id' $CONFIG_PATH)
SPEAKER_MAC=$(jq --raw-output '.model_id' $CONFIG_PATH)

# Enable Bluetooth
# ./enable_bt.sh $SPEAKER_MAC
# Enable Hotword Detection
# ./src/snowboy.sh

# Check if a new assistant file exists
if [ -f "/share/$CLIENT_SECRETS" ]; then
    echo "[Info] Install/Update service client_secrets file"
    cp -f "/share/$CLIENT_SECRETS" "$CLIENT_JSON"
fi

if [ ! -f "$CRED_JSON" ] && [ -f "$CLIENT_JSON" ]; then
    echo "[Info] Start WebUI for handling oauth2"
    python3 /src/hassio_oauth.py "$CLIENT_JSON" "$CRED_JSON"
elif [ ! -f "$CRED_JSON" ]; then
    echo "[Error] You need initialize Google Assistant with a client secret json!"
    exit 1
fi

# Setup bluetooth
# Connect to device

echo -e "connect $SPEAKER_MAC" | bluetoothctl
echo -e "trust $SPEAKER_MAC" | bluetoothctl

# Change bluetooth device in sound config
search="00:00:00:00:00:00"
sed 's/$search/$SPEAKER_MAC/g' /.asoundrc

# Save a copy to /etc/asound.conf & prevent being overwritten
sudo cp /.asoundrc /etc/asound.conf
sudo cp /.asoundrc ~/.asoundrc
chmod a-w /.asoundrc

echo "[Info] Run Hass.io Google Assisant SDK"
exec python3 /src/assistant.py --credentials $CRED_JSON --device_config $CLIENT_JSON --project_id $PROJECT_ID --device_model_id $MODEL_ID
# exec python3 /src/webserver/hassio_gassistant.py "$CRED_JSON" "$PROJECT_ID" "$MODEL_ID" < /dev/null
