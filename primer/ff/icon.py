from PIL import Image
# Простая обработка иконки под стандарт (напр. steam 32x32)
def process_icon(input_path, output_path):
    try:
        img = Image.open(input_path)
        img = img.resize((32, 32))
        img.save(output_path)
        return True
    except:
        return False
