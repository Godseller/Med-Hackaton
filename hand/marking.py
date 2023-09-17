import os
import cv2
import mediapipe as mp
import shutil

# Инициализация MediaPipe Hands
mp_hands = mp.solutions.hands.Hands(static_image_mode=False,
                                    max_num_hands=2,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.5)

# Путь к папке с исходными изображениями
input_folder_path = 'hand/Data'

# Создание новой папки для сохранения размеченных изображений
output_folder_path = 'hand/AnnotatedData'
os.makedirs(output_folder_path, exist_ok=True)

# Рекурсивное создание подпапок в новой папке
for root, dirs, files in os.walk(input_folder_path):
    for dir in dirs:
        dir_path = os.path.join(output_folder_path, os.path.relpath(os.path.join(root, dir), input_folder_path))
        os.makedirs(dir_path, exist_ok=True)

# Получение списка папок в основной папке
subfolders = [f.path for f in os.scandir(input_folder_path) if f.is_dir()]

for subfolder in subfolders:
    # Получение списка файлов в папке
    files = os.listdir(subfolder)

    for file in files:
        # Полный путь к файлу
        file_path = os.path.join(subfolder, file)

        # Чтение изображения
        image = cv2.imread(file_path)

        # Преобразование изображения в формат RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Обнаружение рук на изображении
        results = mp_hands.process(image_rgb)

        # Рисование разметки рук на изображении
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Рисование точек разметки
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * image.shape[1])
                    y = int(landmark.y * image.shape[0])
                    cv2.circle(image, (x, y), 1, (0, 255, 0), -1)

                # Рисование связей между точками разметки
                connections = [[0, 1], [1, 2], [2, 3], [3, 4], [5, 6], [6, 7], [7, 8], [9, 10], [10, 11], [11, 12], [13, 14], [14, 15], [15, 16], [17, 18], [18, 19], [19, 20], [0, 5], [5, 9], [9, 13], [13, 17], [0, 17]]
                for connection in connections:
                    x0 = int(hand_landmarks.landmark[connection[0]].x * image.shape[1])
                    y0 = int(hand_landmarks.landmark[connection[0]].y * image.shape[0])
                    x1 = int(hand_landmarks.landmark[connection[1]].x * image.shape[1])
                    y1 = int(hand_landmarks.landmark[connection[1]].y * image.shape[0])
                    cv2.line(image, (x0, y0), (x1, y1), (0, 255, 0), 1)

        # Сохранение размеченного изображения
        output_file_path = os.path.join(output_folder_path, os.path.relpath(file_path, input_folder_path))
        cv2.imwrite(output_file_path, image)