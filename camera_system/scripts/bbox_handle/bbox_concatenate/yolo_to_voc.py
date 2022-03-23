import os
from xml.dom import minidom
import xml.etree.cElementTree as ET
from PIL import Image

ANNOTATIONS_DIR_PREFIX = "/home/fyp2selfdriving/Documents/traffic_light/New_dataset/inference_out"

DESTINATION_DIR = "/home/fyp2selfdriving/Documents/traffic_light/New_dataset/inference_voc"

CLASS_MAPPING = {
    '0': 'Green',
    '1': 'Green-up',
    '2': 'Green-left',
    '3': 'Green-right',
    '4': 'Red',
    '5': 'Yellow',
    '6': 'Red-Yellow',
    '7': 'Count-down',
    '8': 'Empty',
    '9': 'Empty-count-down'
}

def formatter(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def create_root(file_prefix, width, height):
    root = ET.Element("annotation")
    ET.SubElement(root, "filename").text = "{}.jpg".format(file_prefix)
    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(width)
    ET.SubElement(size, "height").text = str(height)
    ET.SubElement(size, "depth").text = "3"
    return root


def create_object_annotation(root, voc_labels):
    for voc_label in voc_labels:
        obj = ET.SubElement(root, "object")
        ET.SubElement(obj, "name").text = voc_label[0]
        bbox = ET.SubElement(obj, "bndbox")
        ET.SubElement(bbox, "xmin").text = str(voc_label[1])
        ET.SubElement(bbox, "ymin").text = str(voc_label[2])
        ET.SubElement(bbox, "xmax").text = str(voc_label[3])
        ET.SubElement(bbox, "ymax").text = str(voc_label[4])
    return root


def create_file(file_prefix, width, height, voc_labels):
    root = create_root(file_prefix, width, height)
    root = create_object_annotation(root, voc_labels)
    with open("{}/{}.xml".format(DESTINATION_DIR, file_prefix), "w") as f:

            f.write(formatter(root))
            f.close()

def read_file(file_path):
    file_prefix = file_path.split(".txt")[0]
    image_file_name = "{}.jpg".format(file_prefix)
    # img = Image.open("{}/{}".format("sites", image_file_name))
    w, h = (1920,1080)
    with open(ANNOTATIONS_DIR_PREFIX+'/'+file_path, 'r') as file:
        lines = file.readlines()
        voc_labels = []
        for line in lines:
            voc = []
            line = line.strip()
            data = line.split()
            voc.append(CLASS_MAPPING.get(data[0]))
            bbox_width = float(data[3]) * w
            bbox_height = float(data[4]) * h
            center_x = float(data[1]) * w
            center_y = float(data[2]) * h
            voc.append(round(center_x - (bbox_width / 2)))
            voc.append(round(center_y - (bbox_height / 2)))
            voc.append(round(center_x + (bbox_width / 2)))
            voc.append(round(center_y + (bbox_height / 2)))
            voc_labels.append(voc)
        create_file(file_prefix, w, h, voc_labels)


def start():
    if not os.path.exists(DESTINATION_DIR):
        os.makedirs(DESTINATION_DIR)
    for filename in os.listdir(ANNOTATIONS_DIR_PREFIX):
        if filename.endswith('txt'):
            read_file(filename)
        else:
            print("Skipping file: {}".format(filename))


if __name__ == "__main__":
    start()
