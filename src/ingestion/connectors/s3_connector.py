class S3Connector:
    def __init__(self, access_key, secret_key, bucket_name):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.session = None

    def connect(self):
        import boto3

        self.session = boto3.Session(
            aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key
        )
        return self.session.resource("s3")

    def upload_file(self, file_name, object_name=None):
        s3 = self.connect()
        if object_name is None:
            object_name = file_name
        s3.Bucket(self.bucket_name).upload_file(file_name, object_name)

    def download_file(self, object_name, file_name):
        s3 = self.connect()
        s3.Bucket(self.bucket_name).download_file(object_name, file_name)
