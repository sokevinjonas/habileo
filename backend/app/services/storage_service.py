import cloudinary.uploader

def upload_image(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]