"""
Các thuật toán thay thế trang (Page Replacement Algorithms).

Mỗi thuật toán nhận vào:
    - pages:        danh sách các trang cần truy cập (list[int])
    - frames_count: số lượng frame trong RAM (int)

Mỗi thuật toán trả về:
    - steps:  danh sách trạng thái từng bước, mỗi bước là tuple:
              (page, frames, ref_bits, status, victim)
              - page:     trang đang truy cập
              - frames:   trạng thái các frame sau bước này
              - ref_bits: danh sách reference bit (chỉ dùng cho Second Chance)
              - status:   "Hit" hoặc "Fault"
              - victim:   trang bị thay thế (None nếu không thay)
    - faults: tổng số page fault
"""


# =============================================================================
# FIFO - First In First Out
# Trang nào vào RAM trước thì bị thay trước.
# Dùng một con trỏ xoay vòng (queue_index) để biết frame nào cần thay tiếp.
# =============================================================================

def fifo(pages, frames_count):
    frames = []         # Các frame hiện tại trong RAM
    queue_index = 0     # Con trỏ chỉ đến frame cần thay tiếp theo
    steps = []
    faults = 0

    for page in pages:
        # Page đã có trong RAM → Hit
        if page in frames:
            status = "Hit"
            victim = None
        # Page chưa có → Fault
        else:
            faults += 1
            status = "Fault"

            # Còn frame trống → thêm vào, không cần thay
            if len(frames) < frames_count:
                victim = None
                frames.append(page)
            # Hết frame trống → thay frame cũ nhất (theo queue_index)
            else:
                victim = frames[queue_index]
                frames[queue_index] = page
                queue_index = (queue_index + 1) % frames_count

        # Lưu trạng thái bước này (ref_bits rỗng vì FIFO không dùng)
        steps.append((page, frames.copy(), [], status, victim))

    return steps, faults


# =============================================================================
# Optimal - Thay trang sẽ được dùng xa nhất trong tương lai.
# Cần nhìn trước chuỗi trang → chỉ dùng để so sánh, không thực tế.
# =============================================================================

def optimal(pages, frames_count):
    frames = []
    steps = []
    faults = 0

    for i, page in enumerate(pages):
        # Page đã có trong RAM → Hit
        if page in frames:
            status = "Hit"
            victim = None
        # Page chưa có → Fault
        else:
            faults += 1
            status = "Fault"

            # Còn frame trống → thêm vào
            if len(frames) < frames_count:
                victim = None
                frames.append(page)
            # Hết frame → tìm trang nào được dùng xa nhất trong tương lai
            else:
                future = pages[i + 1:]  # Chuỗi trang từ vị trí tiếp theo

                farthest = -1       # Khoảng cách xa nhất tìm được
                replace_index = 0   # Vị trí frame sẽ bị thay

                for j, frame_page in enumerate(frames):
                    # Trang không xuất hiện trong tương lai → thay ngay
                    if frame_page not in future:
                        replace_index = j
                        break
                    # Trang còn xuất hiện → ghi nhớ nếu xa nhất
                    distance = future.index(frame_page)
                    if distance > farthest:
                        farthest = distance
                        replace_index = j

                victim = frames[replace_index]
                frames[replace_index] = page

        # Lưu trạng thái (ref_bits rỗng vì Optimal không dùng)
        steps.append((page, frames.copy(), [], status, victim))

    return steps, faults


# =============================================================================
# LRU - Least Recently Used
# Thay trang lâu nhất chưa được sử dụng.
# Dùng danh sách recent: phần tử đầu = lâu nhất, phần tử cuối = mới nhất.
# =============================================================================

def lru(pages, frames_count):
    frames = []     # Các frame hiện tại
    recent = []     # Thứ tự sử dụng: đầu = lâu nhất, cuối = mới nhất
    steps = []
    faults = 0

    for page in pages:
        # Page đã có trong RAM → Hit, cập nhật thứ tự sử dụng
        if page in frames:
            status = "Hit"
            victim = None
            # Đưa page lên cuối danh sách (mới dùng nhất)
            recent.remove(page)
            recent.append(page)
        # Page chưa có → Fault
        else:
            faults += 1
            status = "Fault"

            # Còn frame trống → thêm vào
            if len(frames) < frames_count:
                victim = None
                frames.append(page)
                recent.append(page)
            # Hết frame → thay trang lâu nhất (đầu danh sách recent)
            else:
                lru_page = recent.pop(0)    # Lấy trang lâu nhất ra
                victim = lru_page
                index = frames.index(lru_page)
                frames[index] = page        # Thay trong frames
                recent.append(page)         # Thêm trang mới vào cuối

        # Lưu trạng thái (ref_bits rỗng vì LRU không dùng)
        steps.append((page, frames.copy(), [], status, victim))

    return steps, faults


# =============================================================================
# Second Chance - Cải tiến FIFO bằng reference bit.
# Mỗi page có 1 bit tham chiếu (ref_bit).
# Khi cần thay: duyệt vòng từ pointer:
#   - bit = 1 → cho cơ hội thứ hai: reset bit về 0, bỏ qua
#   - bit = 0 → thay thế page này
# =============================================================================

def second_chance(pages, frames_count):
    frames = []         # Các frame hiện tại
    ref_bits = []       # Reference bit tương ứng từng frame
    pointer = 0         # Con trỏ xoay vòng (kiểu đồng hồ)
    steps = []
    faults = 0

    for page in pages:
        # Page đã có trong RAM → Hit, bật reference bit
        if page in frames:
            status = "Hit"
            victim = None
            index = frames.index(page)
            ref_bits[index] = 1
        # Page chưa có → Fault
        else:
            faults += 1
            status = "Fault"

            # Còn frame trống → thêm vào
            if len(frames) < frames_count:
                victim = None
                frames.append(page)
                ref_bits.append(0)      # Page mới vào luôn có bit = 1
            # Hết frame → duyệt vòng tìm page có bit = 0 để thay
            else:
                # Quét: nếu bit = 1 → reset về 0, chuyển sang frame tiếp
                while ref_bits[pointer] == 1:
                    ref_bits[pointer] = 0
                    pointer = (pointer + 1) % frames_count

                # Tìm được frame có bit = 0 → thay thế
                victim = frames[pointer]
                frames[pointer] = page
                ref_bits[pointer] = 0   # Page mới có bit = 1
                pointer = (pointer + 1) % frames_count

        # Lưu trạng thái (bao gồm ref_bits cho Second Chance)
        steps.append((page, frames.copy(), ref_bits.copy(), status, victim))

    return steps, faults


# =============================================================================
# Bảng tra thuật toán theo tên
# =============================================================================

ALGORITHMS = {
    "FIFO": fifo,
    "Optimal": optimal,
    "LRU": lru,
    "Second Chance": second_chance,
}
