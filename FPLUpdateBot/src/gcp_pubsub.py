from google.cloud import pubsub_v1


class GcpPubSubClient(object):

    def __init__(self, project_id, topic_id):
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
        print(future.result())
        print("Published message to {0}".format(self.topic_path))
