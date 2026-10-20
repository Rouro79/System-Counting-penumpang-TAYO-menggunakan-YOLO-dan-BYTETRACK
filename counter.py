class CrossingCounter:
    def __init__(self, line_y, directions=None):
        self.line_y = line_y

        self.directions = directions or {
            "above_to_below": "masuk",
            "below_to_above": "keluar",
        }

        self.previous_y = {}
        self.counted_ids = set()

        self.masuk = 0
        self.keluar = 0

    def update(self, track_id, center_y):
        if track_id is None:
            return None

        previous_y = self.previous_y.get(track_id)

        # Simpan posisi pertama orang ditemukan.
        self.previous_y[track_id] = center_y

        if previous_y is None:
            return None

        # ID yang sudah dihitung tidak dihitung kembali.
        if track_id in self.counted_ids:
            return None

        direction = None

        # Bergerak dari atas ke bawah.
        if previous_y < self.line_y <= center_y:
            direction = "above_to_below"

        # Bergerak dari bawah ke atas.
        elif previous_y > self.line_y >= center_y:
            direction = "below_to_above"

        if direction is None:
            return None

        hasil = self.directions.get(direction)

        if hasil not in ("masuk", "keluar"):
            return None

        self.counted_ids.add(track_id)

        if hasil == "masuk":
            self.masuk += 1
        else:
            self.keluar += 1

        print(
            f"[TERHITUNG] ID={track_id} "
            f"arah={direction} hasil={hasil.upper()}"
        )

        return hasil

    def get_counts(self):
        return {
            "masuk": self.masuk,
            "keluar": self.keluar,
            "total_terhitung": self.masuk + self.keluar,
        }

    def reset(self):
        self.previous_y.clear()
        self.counted_ids.clear()
        self.masuk = 0
        self.keluar = 0