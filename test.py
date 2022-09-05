import os
import uuid

a = os.path.join(os.path.expanduser("~"), "Downloads", str(uuid.uuid4()))
print(a)