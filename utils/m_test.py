import cv2
import time

if __name__ == "__main__":
    open_ret = 0
    open_count = 0
    cap = None
    while not open_ret:
        cap = cv2.VideoCapture("rtsp://192.168.12.235:8557/left_main_1_0")
        open_ret = cap.isOpened()
        open_count += 1
        if open_count == 20:
            break

    m_time = time.time()
    while cap.isOpened():
        print(f"all {time.time() - m_time}")
        m_time = time.time()
        ret, frame = cap.read()
        cv2.imshow("left", frame)
        cv2.waitKey(1)
        time.sleep(0.01)


