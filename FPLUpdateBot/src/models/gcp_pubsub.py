import os

from google.cloud import pubsub_v1
from models.logger import Logger
log = Logger.getInstance().getLogger()


class GcpPubSubClient(object):

    def __init__(self, gcp_app_cred_file, project_id, topic_id):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_app_cred_file
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = \
            pubsub_v1.PublisherClient()

        # The `topic_path` method creates a fully qualified
        # identifier in the form
        # `projects/{project_id}/topics/{topic_id}`
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

    def publish_message(self, data):
        future = self.publisher.publish(self.topic_path, data)
        # TODO - Handle return code.
        log.info(future.result())
        log.info("Published message to {0}".format(self.topic_path))
