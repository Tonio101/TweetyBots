import argparse
import json
import os

from threading import Lock
from models.fpl_updates import FPLUpdates
from models.gcp_pubsub import GcpPubSubClient


def parse_config_file(fname: str) -> dict:
    """
    Parse Config File.

    Args:
        fname (string): fpl_updates config file.

    Returns:
        dict: A dict with all the config data.
    """
    with open(os.path.abspath(fname), 'r') as fp:
        data = json.load(fp)
        return data


def main():
    usage = ("{FILE} --config <config_file> --debug").format(FILE=__file__)
    description = 'FPL Updates'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Configuration file",
                        required=True)
    parser.add_argument("--debug", help="Enable verbose logging",
                        action='store_true', required=False)
    parser.set_defaults(debug=False)

    args = parser.parse_args()

    config = parse_config_file(args.config)
    twitterConfig = config['twitterbot']
    gcpPubSubConfig = config['gcpPubSub']

    pubsub_client = \
        GcpPubSubClient(
            project_id=gcpPubSubConfig['projectId'],
            topic_id=gcpPubSubConfig['publishId']
        )

    lock = Lock()
    fpl_updates = \
        FPLUpdates(
            lock=lock,
            twitter_bearer_token=twitterConfig['apiBearerToken'],
            pubsub_client=pubsub_client,
            twitter_id="Fpl_Updates"
        )

    fpl_alerts = \
        FPLUpdates(
            lock=lock,
            twitter_bearer_token=twitterConfig['apiBearerToken'],
            pubsub_client=pubsub_client,
            twitter_id="FPL_Alerts"
        )

    fpl_updates.start()
    fpl_alerts.start()
    fpl_updates.join()
    fpl_alerts.join()


if __name__ == "__main__":
    main()
