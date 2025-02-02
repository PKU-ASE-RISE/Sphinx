import base64
import cv2
import pyshine as ps
from LLMs import gpt3, gpt4, gpt4o, gpt4omini, llama3, llama3_70b, llama32_11b_vision, mistral7b, qwen7b, qwen14b, qwenmoe, claude3haiku, claude3sonnet, deepseekchat, gpt4_vlm, gpt4o_vlm, gpt4omini_vlm, qwen_vl_max, qwen_vl_plus

from colorama import Fore, Style


def get_llm(llm_name: str, *args, **kwargs):
    if llm_name == "gpt3":
        return gpt3(*args, **kwargs)
    elif llm_name == "gpt4":
        return gpt4(*args, **kwargs)
    elif llm_name == "gpt4o":
        return gpt4o(*args, **kwargs)
    elif llm_name == "gpt4omini":
        return gpt4omini(*args, **kwargs)
    elif llm_name == "llama3":
        return llama3(*args, **kwargs)
    elif llm_name == 'llama3_70b':
        return llama3_70b(*args, **kwargs)
    elif llm_name == "llama32_11b":
        return llama32_11b_vision(*args, **kwargs)
    elif llm_name == "mistral7b":
        return mistral7b(*args, **kwargs)
    elif llm_name == "qwen7b":
        return qwen7b(*args, **kwargs)
    elif llm_name == "qwen14b":
        return qwen14b(*args, **kwargs)
    elif llm_name == "qwenmoe":
        return qwenmoe(*args, **kwargs)
    elif llm_name == "claude3-haiku":
        return claude3haiku(*args, **kwargs)
    elif llm_name == "claude3-sonnet":
        return claude3sonnet(*args, **kwargs)
    elif llm_name == "deepseek":
        return deepseekchat(*args, **kwargs)
    elif llm_name == "gpt4_vlm":
        return gpt4_vlm(*args, **kwargs)
    elif llm_name == "gpt4o_vlm":
        return gpt4o_vlm(*args, **kwargs)
    elif llm_name == "gpt4omini_vlm":
        return gpt4omini_vlm(*args, **kwargs)
    elif llm_name == "qwen_vl_max":
        return qwen_vl_max(*args, **kwargs)
    elif llm_name == "qwen_vl_plus":
        return qwen_vl_plus(*args, **kwargs)
    else:
        raise ValueError(f"llm_name {llm_name} not recognized")


def print_with_color(text: str, color=""):
    if color == "red":
        print(Fore.RED + text)
    elif color == "green":
        print(Fore.GREEN + text)
    elif color == "yellow":
        print(Fore.YELLOW + text)
    elif color == "blue":
        print(Fore.BLUE + text)
    elif color == "magenta":
        print(Fore.MAGENTA + text)
    elif color == "cyan":
        print(Fore.CYAN + text)
    elif color == "white":
        print(Fore.WHITE + text)
    elif color == "black":
        print(Fore.BLACK + text)
    else:
        print(text)
    print(Style.RESET_ALL)


def draw_bbox_multi(img_path, output_path, elem_list, record_mode=False, dark_mode=False):
    imgcv = cv2.imread(img_path)
    count = 1
    for elem in elem_list:
        try:
            top_left = elem.bbox[0]
            bottom_right = elem.bbox[1]
            left, top = top_left[0], top_left[1]
            right, bottom = bottom_right[0], bottom_right[1]
            label = str(count)
            if record_mode:
                if elem.attrib == "clickable":
                    color = (250, 0, 0)
                elif elem.attrib == "focusable":
                    color = (0, 0, 250)
                else:
                    color = (0, 250, 0)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=color,
                                    text_RGB=(255, 250, 250), alpha=0.5)
            else:
                text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
                bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=bg_color,
                                    text_RGB=text_color, alpha=0.5)
        except Exception as e:
            print_with_color(
                f"ERROR: An exception occurs while labeling the image\n{e}", "red")
        count += 1
    cv2.imwrite(output_path, imgcv)
    return imgcv


def draw_grid(img_path, output_path):
    def get_unit_len(n):
        for i in range(1, n + 1):
            if n % i == 0 and 120 <= i <= 180:
                return i
        return -1

    image = cv2.imread(img_path)
    height, width, _ = image.shape
    color = (255, 116, 113)
    unit_height = get_unit_len(height)
    if unit_height < 0:
        unit_height = 120
    unit_width = get_unit_len(width)
    if unit_width < 0:
        unit_width = 120
    thick = int(unit_width // 50)
    rows = height // unit_height
    cols = width // unit_width
    for i in range(rows):
        for j in range(cols):
            label = i * cols + j + 1
            left = int(j * unit_width)
            top = int(i * unit_height)
            right = int((j + 1) * unit_width)
            bottom = int((i + 1) * unit_height)
            cv2.rectangle(image, (left, top),
                          (right, bottom), color, thick // 2)
            cv2.putText(image, str(label), (left + int(unit_width * 0.05) + 3, top + int(unit_height * 0.3) + 3), 0,
                        int(0.01 * unit_width), (0, 0, 0), thick)
            cv2.putText(image, str(label), (left + int(unit_width * 0.05), top + int(unit_height * 0.3)), 0,
                        int(0.01 * unit_width), color, thick)
    cv2.imwrite(output_path, image)
    return rows, cols


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
