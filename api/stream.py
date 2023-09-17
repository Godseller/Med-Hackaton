from aiortc import MediaStreamTrack
from av import VideoFrame
import cv2
import numpy as np
import onnxruntime as ort
from constants import classes
from .connectionmanager import manager
from datetime import datetime


ort.set_default_logger_severity(4)
session = ort.InferenceSession('./mvit32-2.onnx')

input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape
window_size = input_shape[3]
output_names = [output.name for output in session.get_outputs()]

threshold = 0.5
frame_interval = 2
frame_waiting = window_size // 2
mean = [123.675, 116.28, 103.53]
std = [58.395, 57.12, 57.375]


def resize(im, new_shape=(224, 224)):
    """
    Resize and pad image while preserving aspect ratio.

    Parameters
    ----------
    im : np.ndarray
        Image to be resized.
    new_shape : Tuple[int]
        Size of the new image.

    Returns
    -------
    np.ndarray
        Resized image.
    """
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right,
                            cv2.BORDER_CONSTANT, value=(114, 114, 114))  # add border
    return im


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"



    def __init__(self, track):
        super().__init__()
        self.track = track
        self.tensors_list_1 = []
        self.tensors_list_2 = []
        self.model_1_outputs = None
        self.model_2_outputs = None
        self.second_model_run = False
        self.start_predict = False
        self.frame_counter = 0

    async def recv(self):
        frame = await self.track.recv()

    
        img = frame.to_ndarray(format="bgr24")
        

        # Наш frame в переменной img ВСЕ ПРЕОБРАЗОВАНИЯ ДЕЛАЕМ ТУТ __________________---------------------___________________----------
        self.frame_counter += 1
        if self.frame_counter % frame_interval == 0:
            image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            image = resize(image, (224, 224))
            image = (image - mean) / std
            image = np.transpose(image, [2, 0, 1])

            self.tensors_list_1.append(image)

            if self.second_model_run:
                self.tensors_list_2.append(image)
            
            if len(self.tensors_list_1) == window_size:
                print('Run first predict', datetime.now())
                input_tensor = np.stack(self.tensors_list_1[: window_size], axis=1)[None][None]
                self.model_1_outputs = session.run(output_names, {input_name: input_tensor.astype(np.float32)})[0]
                self.tensors_list_1.clear()
                self.start_predict = True
                print('Ready first predict', datetime.now())
            
            if len(self.tensors_list_2) == window_size:
                print('Run second predict', datetime.now())
                input_tensor = np.stack(self.tensors_list_2[: window_size], axis=1)[None][None]
                self.model_2_outputs = session.run(output_names, {input_name: input_tensor.astype(np.float32)})[0]
                self.tensors_list_2.clear()
                self.start_predict = True
                print('Ready second predict', datetime.now())

            if self.start_predict:
                self.start_predict = False
                print('Run total predict', datetime.now())
                if self.model_2_outputs and self.model_2_outputs.max() > self.model_1_outputs.max():
                    outputs = self.model_2_outputs
                else:
                    outputs = self.model_1_outputs
                
                gloss = str(classes[outputs.argmax()])
                if outputs.max() > threshold:
                    await manager.broadcast(gloss)
                    print(f'detected word: {gloss}')
                    print('Ready total predict', datetime.now())
                else:
                    await manager.broadcast('---')
                    print('no word')
                    print('Ready total predict', datetime.now())
            
            if self.frame_counter > frame_interval * frame_waiting:
                self.second_model_run = True


        #___________________________----------------------_____________________---------------------__________________------------------________

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
  


