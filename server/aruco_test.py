import cv2
import threading
from aruco_vz import aruco_tool

rtsp_url = "rtsp://192.168.109.90:8557/left_main_1_0"
read_frame_state = False
read_frame = None
thread_state = False
# 事件对象，用于控制线程的暂停和恢复
pause_event = threading.Event()


def read_rtsp_stream():
    print("begin open RTSP stream")
    global read_frame_state, read_frame, thread_state, pause_event
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("Error: Failed to open RTSP stream")
        return

    pause_event.set()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from RTSP stream")
            break

        if not read_frame_state:
            read_frame = frame.copy()
            read_frame_state = True

        if not thread_state:
            break

    read_frame = None
    cap.release()


def play_test():
    global read_frame_state, read_frame, thread_state, pause_event
    aruco_tool.set_aruco_dictionary(5, 250)
    aruco_tool.set_charuco_board((12, 9))
    thread_state = True
    read_frame_state = False

    rtsp_thread = threading.Thread(target=read_rtsp_stream)
    rtsp_thread.start()

    pause_event.wait()
    pause_event.clear()

    cv2.namedWindow("RTSP Stream", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("RTSP Stream", 900, 600)

    max_wait_count = 30
    wait_count = 0
    board_size = 50

    while True:
        if not read_frame_state:
            wait_count += 1
            if wait_count >= max_wait_count:
                break
            cv2.waitKey(10)
            continue

        wait_count = 0
        img = read_frame.copy()
        img = cv2.resize(img, (900, 600))
        objPoints, imgPoints = aruco_tool.charuco_detect(img, True)
        objPoints = objPoints / 0.25 * board_size
        cv2.imshow("RTSP Stream", img)
        read_frame_state = False

        if cv2.waitKey(1) == ord('q'):
            break

    thread_state = False
    rtsp_thread.join()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    play_test()
