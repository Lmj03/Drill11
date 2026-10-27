"""Regenerate the PRD state diagram as a PNG (requires Pillow)."""

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK = "#20314D"
BLUE = "#275EBA"
GREEN = "#157D68"
ORANGE = "#B46716"
BACKGROUND = "#F3F6FB"


def font(size, bold=False):
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = (
        windows / ("malgunbd.ttf" if bold else "malgun.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    )
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("Install a Korean font: Malgun Gothic or Nanum Gothic")


def generate(output=ROOT / "state_diagram.png"):
    image = Image.new("RGB", (2000, 1670), BACKGROUND)
    draw = ImageDraw.Draw(image)

    def text(center, value, size=26, color=INK, bold=False):
        f = font(size, bold)
        bbox = draw.multiline_textbbox((0, 0), value, font=f, spacing=10, align="center")
        x = center[0] - (bbox[2] - bbox[0]) / 2
        y = center[1] - (bbox[3] - bbox[1]) / 2 - bbox[1]
        draw.multiline_text((x, y), value, font=f, fill=color, spacing=10, align="center")

    def arrow(points, color=BLUE):
        draw.line(points, fill=color, width=5, joint="curve")
        start, end = points[-2:]
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        head = [end]
        for offset in (-0.48, 0.48):
            head.append((end[0] - 20 * math.cos(angle + offset),
                         end[1] - 20 * math.sin(angle + offset)))
        draw.polygon(head, fill=color)

    def label(center, value, size=25, color=BLUE):
        f = font(size)
        bbox = draw.multiline_textbbox((0, 0), value, font=f, spacing=10, align="center")
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = center
        draw.rounded_rectangle((x-w/2-18, y-h/2-12, x+w/2+18, y+h/2+12),
                               radius=12, fill=BACKGROUND)
        text(center, value, size, color)

    def node(box, title, body, color):
        draw.rounded_rectangle(box, radius=24, fill="white", outline=color, width=4)
        x = (box[0] + box[2]) / 2
        text((x, box[1] + 53), title, 38, color, True)
        text((x, box[1] + 130), body, 25)

    text((1000, 65), "소년 상태 다이어그램", 46, bold=True)
    text((1000, 125), "pico2d  /  IDLE · RUN · AUTO_RUN  /  prd.md 구현 기준", 25)

    # Core transitions. Labels and self-transition details appear below.
    draw.ellipse((375, 175, 405, 205), fill=INK)
    arrow([(390, 205), (390, 250)], INK)
    text((495, 203), "게임 시작", 23)
    arrow([(620, 300), (1380, 300)])
    arrow([(1380, 390), (620, 390)])
    arrow([(120, 400), (85, 400), (85, 960), (750, 960)], GREEN)
    arrow([(1880, 400), (1915, 400), (1915, 960), (1250, 960)], GREEN)
    arrow([(750, 810), (680, 810), (680, 470), (540, 470), (540, 430)], ORANGE)
    arrow([(1250, 810), (1320, 810), (1320, 470), (1460, 470), (1460, 430)], BLUE)
    arrow([(1500, 430), (1500, 515), (1800, 515), (1800, 430)], BLUE)
    arrow([(900, 990), (900, 1060), (1100, 1060), (1100, 990)], GREEN)

    node((120, 250, 620, 430), "IDLE", "이동 정지\n기본 크기", BLUE)
    node((1380, 250, 1880, 430), "RUN", "좌우 수동 이동\n기본 속도 · 기본 크기", BLUE)
    node((750, 770, 1250, 990), "AUTO_RUN", "구현 클래스: AutoRun\n자동 이동 · 선형 가속 · 선형 확대", GREEN)

    label((1000, 275), "← / → 누름  ·  방향키 조합에 따라 이동", 25)
    label((1000, 366), "방향키 모두 해제 → 정지  [제안 채택]", 25)
    label((320, 660), "A 누름\n타이머 0초로 시작\n시작 방향 랜덤 선택", 26, GREEN)
    label((1680, 660), "A 누름\n타이머 0초로 시작\n시작 방향 랜덤 선택", 26, GREEN)
    label((690, 615), "5초 만료\n같은 프레임에 좌우 입력 없음\n기본 속도 · 크기로 복원", 24, ORANGE)
    label((1310, 615), "← / → 누름\n5초 만료보다 입력 우선\n기본 속도 · 크기로 복원", 24, BLUE)
    label((1650, 488), "동시 입력 / 한쪽 키 해제", 23)
    label((1000, 1110), "벽 도달 또는 화살표 이외 키 입력\nAUTO_RUN 유지 · 타이머와 증가량 유지", 26, GREEN)

    cards = (
        (90, "01  벽에서 방향 전환", GREEN,
         "왼쪽 끝 → 오른쪽 이동\n오른쪽 끝 → 왼쪽 이동\n확대된 실제 표시 폭으로 경계 판정\n접지 위치 유지 · 벽에서 타이머 유지"),
        (720, "02  방향키 처리", BLUE,
         "한쪽만 누름 → 해당 방향으로 이동\n좌우 동시 → 마지막 방향을 보고 정지\n한쪽 해제 → 남아 있는 방향으로 이동\n방향키 모두 해제 → IDLE [제안 채택]"),
        (1350, "03  AUTO RUN 규칙", ORANGE,
         "datetime 기반 · 최대 5초\n속도 240 → 720 px/s · 크기 1 → 2배\nA 재입력 / 다른 키로 해제·초기화 없음\n재진입 시 랜덤 선택 · 기본값에서 시작"),
    )
    for x, heading, color, body in cards:
        draw.rounded_rectangle((x, 1210, x + 560, 1555), radius=20,
                               fill="white", outline="#DCE4F0", width=2)
        text((x + 280, 1260), heading, 27, color, True)
        text((x + 280, 1410), body, 23)

    text((1000, 1610), "창 닫기: 프로그램 종료  |  ↑ / ↓: 수평 이동 및 상태 전이에 사용하지 않음", 22)
    image.save(output)
    print(output)


if __name__ == "__main__":
    generate()
