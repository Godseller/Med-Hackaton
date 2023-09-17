import cv2
import mediapipe as mp
import numpy as np
import os

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

def detect_hand(image):
    # Инициализация Hands модели
    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        # Преобразование изображения в RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Обнаружение рук на изображении
        results = hands.process(image_rgb)
        
        # Рисуем бокс и получаем координаты точек, если руки обнаружены
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Получаем размеры изображения
                image_height, image_width, _ = image.shape
                
                # Рисуем бокс вокруг руки
                box = get_hand_box(hand_landmarks, image_width, image_height)
                cv2.rectangle(image, box[0], box[1], (0, 255, 0), 2)
                
                # Сжимаем изображение внутри бокса до размеров 50x50
                compressed_image = compress_image(image[box[0][1]:box[1][1], box[0][0]:box[1][0]], 200, 200)
                
                return compressed_image

    # Если рука не обнаружена или не удалось сжать изображение, возвращаем None
    return None


def get_hand_box(hand_landmarks, image_width, image_height):
    # Получаем координаты верхнего левого и нижнего правого углов бокса
    x_min = image_width
    x_max = 0
    y_min = image_height
    y_max = 0

    for landmark in hand_landmarks.landmark:
        x = int(landmark.x * image_width)
        y = int(landmark.y * image_height)

        if x < x_min:
            x_min = x
        if x > x_max:
            x_max = x
        if y < y_min:
            y_min = y
        if y > y_max:
            y_max = y
    x_min = max(0, x_min - 20)
    y_min = max(0, y_min - 20)
    x_max = min(image_width - 1, x_max + 20)
    y_max = min(image_height - 1, y_max + 20)
    # Создаем оригинальный бокс
    original_box = ((x_min, y_min), (x_max, y_max))

    return original_box


def compress_image(image, new_width, new_height):
    # Получаем размеры исходного изображения
    image_height, image_width, _ = image.shape
    
    # Проверяем, что размеры нового изображения не больше размеров исходного изображения
    if new_width > image_width or new_height > image_height:
        # Вычисляем разницу в размерах
        width_diff = new_width - image_width
        height_diff = new_height - image_height
        
        # Вычисляем значения границы для заполнения
        top = max(height_diff // 2, 0)
        bottom = max(height_diff - top, 0)
        left = max(width_diff // 2, 0)
        right = max(width_diff - left, 0)
        
        # Создаем новое изображение с заполнением нулями
        resized_image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    else:
        # Изменяем размер изображения
        resized_image = cv2.resize(image, (new_width, new_height))
    
    return resized_image

output_dir = 'output_frames'
os.makedirs(output_dir, exist_ok=True)
# Загрузка видео
cap = cv2.VideoCapture('hand/video.mp4')

frame_number = 0
while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret:
        break
    
    # Обнаружение руки на кадре и сжатие изображения внутри бокса
    compressed_image = detect_hand(frame)
    if compressed_image is not None:
        # Генерируем уникальное имя файла для сохранения
        filename = os.path.join(output_dir, f'frame_{frame_number}.jpg')
        frame_number += 1
        
        # Сохраняем сжатое изображение в файл
        cv2.imwrite(filename, compressed_image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()