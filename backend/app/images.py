
from dotenv import load_dotenv
from imagekitio import ImageKit
import os

load_dotenv()

imagekit = ImageKit(
    os.getenv("IMAGEKIT_PRIVATE_KEY"),
    os.getenv("IMAGEKIT_PUBLIC_KEY"),
    os.getenv("IMAGEKIT_URL_ENDPOINT")
)
