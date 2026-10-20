import cv2
from ultralytics import YOLO

from counter import CrossingCounter


class VideoWorker:
    def __init__(
        self,
        video_path,
        model_path="yolo11n.pt",
        line_ratio=0.80,
        directions=None,
        camera_name="CCTV",
    ):
        self.video_path = video_path
        self.model_path = model_path
        self.line_ratio = line_ratio
        self.directions = directions or {
            "above_to_below": "masuk",
            "below_to_above": "keluar",
        }
        self.camera_name = camera_name

    def run(self):
        # Membuka video.
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(
                f"[ERROR] Tidak dapat membuka video: "
                f"{self.video_path}"
            )
            return

        model = YOLO(self.model_path)
        counter = None

        window_name = f"BUS TAYO AI - {self.camera_name}"

        print(f"[INFO] Memproses {self.video_path}")

        try:
            while True:
                ret, frame = cap.read()

                if not ret:
                    print("[INFO] Video selesai.")
                    break

                height, width = frame.shape[:2]
                line_y = int(height * self.line_ratio)

                if counter is None:
                    counter = CrossingCounter(
                        line_y=line_y,
                        directions=self.directions,
                    )

                # Deteksi manusia dan tracking ByteTrack.
                results = model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=[0],
                    conf=0.35,
                    verbose=False,
                )

                result = results[0]
                boxes = result.boxes

                # Gambar garis virtual.
                cv2.line(
                    frame,
                    (0, line_y),
                    (width, line_y),
                    (0, 255, 255),
                    2,
                )

                if boxes is not None and len(boxes) > 0:
                    coordinates = boxes.xyxy.cpu().tolist()

                    if boxes.id is not None:
                        track_ids = boxes.id.int().cpu().tolist()
                    else:
                        track_ids = [None] * len(coordinates)

                    print(
                        f"[DETEKSI] "
                        f"Jumlah orang: {len(coordinates)}"
                    )

                    for box, track_id in zip(
                        coordinates, track_ids
                    ):
                        x1, y1, x2, y2 = map(int, box)

                        center_x = (x1 + x2) // 2

                        # Titik tengah kotak deteksi.
                        center_y = y2 - 5

                        # Perbarui penghitung.
                        hasil = counter.update(
                            track_id,
                            center_y,
                        )

                        print(
                            f"ID={track_id}, "
                            f"Y={center_y}, "
                            f"garis={line_y}, "
                            f"hasil={hasil}, "
                            f"MASUK={counter.masuk}, "
                            f"KELUAR={counter.keluar}"
                        )

                        # Gambar kotak deteksi.
                        warna = (0, 255, 0)

                        cv2.rectangle(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            warna,
                            2,
                        )

                        label = (
                            f"ID {track_id}"
                            if track_id is not None
                            else "Person"
                        )

                        cv2.putText(
                            frame,
                            label,
                            (x1, max(20, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            warna,
                            2,
                        )

                        cv2.circle(
                            frame,
                            (center_x, center_y),
                            4,
                            (255, 0, 0),
                            -1,
                        )

                        if hasil is not None:
                            print(
                                f"[{self.camera_name}] "
                                f"ID {track_id}: "
                                f"{hasil.upper()}"
                            )

                else:
                    print("[INFO] Tidak ada orang terdeteksi.")

                # Tampilkan jumlah meskipun tidak ada orang
                # terdeteksi pada frame saat ini.
                counts = counter.get_counts()

                cv2.putText(
                    frame,
                    f"MASUK: {counts['masuk']}",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    f"KELUAR: {counts['keluar']}",
                    (15, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

                # Tampilkan setiap frame.
                cv2.imshow(window_name, frame)

                # Tekan Q untuk menghentikan video.
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("[INFO] Dihentikan oleh pengguna.")
                    break

        finally:
            # Membersihkan sumber daya setelah loop berakhir.
            cap.release()
            cv2.destroyAllWindows()

        if counter is not None:
            print("[HASIL AKHIR]", counter.get_counts())