import cv2
import numpy as np

cap1 = cv2.VideoCapture('videos/bus01.mp4')
cap2 = cv2.VideoCapture('videos/bus02.mp4')
cap3 = cv2.VideoCapture('videos/bus03.mp4')

if not (cap1.isOpened() and cap2.isOpened() and cap3.isOpened()):
    print("Error: Ada video yang tidak bisa dibuka. Cek kembali path/nama filenya.")
    exit()
    
TARGET_WIDTH = 640
TARGET_HEIGHT = 360

print("Memulai streaming 3 CCTV... Tekan 'q' untuk keluar.")

    

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()
    ret3, frame3 = cap3.read()
    
    if not ret1:
        cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret1, frame1 = cap1.read()
    if not ret2:
        cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret2, frame2 = cap2.read()
    if not ret3:
        cap3.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret3, frame3 = cap3.read()
        
    frame1_resized = cv2.resize(frame1, (TARGET_WIDTH, TARGET_HEIGHT))
    frame2_resized = cv2.resize(frame2, (TARGET_WIDTH, TARGET_HEIGHT))
    frame3_resized = cv2.resize(frame3, (TARGET_WIDTH, TARGET_HEIGHT))
    
    cv2.putText(frame1_resized, "CCTV 01 - Pintu Depan", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame2_resized, "CCTV 02 - Pintu Tengah", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame3_resized, "CCTV 03 - Pintu Belakang", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    combined_frame = np.hstack((frame1_resized, frame2_resized, frame3_resized))
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
cap1.release()
cap2.release()
cap3.release()
cv2.destroyALLWindows()
print("Streaming dihentkan")