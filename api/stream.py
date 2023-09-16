from aiortc import MediaStreamTrack
from av import VideoFrame
import cv2
from .connectionmanager import manager


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()

    
        img = frame.to_ndarray(format="bgr24")
        

        # Наш frame в переменной img ВСЕ ПРЕОБРАЗОВАНИЯ ДЕЛАЕМ ТУТ __________________---------------------___________________----------
        rows, cols, _ = img.shape




        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
        img = cv2.warpAffine(img, M, (cols, rows))


        # Распознаггый текст передать в браузер
    
        message = "Я точно знаю этот жест!"
        await manager.broadcast(message)


        #___________________________----------------------_____________________---------------------__________________------------------________

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
  


