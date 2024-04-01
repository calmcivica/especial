from PIL import Image
import os

image_directory = 'static/dbt'
optimized_directory = 'static_new/dbt'

if not os.path.exists(optimized_directory):
    os.makedirs(optimized_directory)

for filename in os.listdir(image_directory):
    if filename.endswith('.png'):
        file_path = os.path.join(image_directory, filename)
        image = Image.open(file_path)

        # Save the image with optimal settings
        optimized_path = os.path.join(optimized_directory, filename)
        image.save(optimized_path, format='PNG', optimize=True)