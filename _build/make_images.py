#!/usr/bin/env python3
"""프로필 사진 한 장에서 쓰임새별 이미지를 만든다.

  python3 _build/make_images.py <원본사진> <출력 images 디렉토리>

만드는 것:
  profile.jpg         640x800   소개 페이지 (손 흔드는 모습까지 담는다)
  profile-square.jpg  256x256   글쓴이 상자 썸네일 (얼굴 중심)
  og-image.jpg       1200x630   링크 공유 미리보기 (흰 바탕 + 로마자 이름)
"""
import os
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# 원본(1145x1374) 기준 잘라낼 자리
PORTRAIT_BOX = (210, 150, 1110, 1275)   # 4:5, 흔드는 손까지
FACE_BOX = (145, 140, 805, 800)         # 정사각, 얼굴 중심 (머리 위 여백 확보)

# 톤 보정 — 사이트가 흰 바탕이라 원본 그대로 쓰면 사진만 무겁게 가라앉는다.
# 중간톤을 올리고(GAMMA), 검정을 들어올리고(LIFT), 빨강을 조금 더해 따뜻하게 한다.
# 배경 현수막의 원색이 튀므로 채도는 낮춘다.
TONE = dict(gamma=0.78, r_gain=1.050, b_gain=0.950,
            saturation=0.87, contrast=0.95, lift=0.12)


def _lut(gamma, gain, lift):
    out = []
    for v in range(256):
        x = (v / 255.0) ** gamma
        x = lift + (1 - lift) * x
        out.append(max(0, min(255, round(x * 255 * gain))))
    return out


def warm(im, gamma, r_gain, b_gain, saturation, contrast, lift):
    """따뜻하고 밝게. 얼굴 윤곽이 뭉개지지 않을 만큼만 대비를 눕힌다."""
    r, g, b = im.split()
    im = Image.merge("RGB", (r.point(_lut(gamma, r_gain, lift)),
                             g.point(_lut(gamma, 1.0, lift)),
                             b.point(_lut(gamma, b_gain, lift))))
    im = ImageEnhance.Color(im).enhance(saturation)
    return ImageEnhance.Contrast(im).enhance(contrast)


INK = (17, 17, 17)
MUTED = (118, 118, 118)
ACCENT = (138, 47, 47)
RULE = (207, 207, 207)


def spaced(draw, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def main(src_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(src_path).convert("RGB")
    print("원본:", im.size)
    im = warm(im, **TONE)

    # 1) 소개 페이지용 세로 사진
    portrait = im.crop(PORTRAIT_BOX).resize((640, 800), Image.LANCZOS)
    portrait.save(os.path.join(out_dir, "profile.jpg"), quality=88, optimize=True,
                  progressive=True)

    # 2) 글쓴이 상자 썸네일
    face = im.crop(FACE_BOX).resize((256, 256), Image.LANCZOS)
    face.save(os.path.join(out_dir, "profile-square.jpg"), quality=88, optimize=True)

    # 3) 공유 미리보기 — 흰 바탕에 사진과 로마자 이름
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), (255, 255, 255))
    ph = im.crop(FACE_BOX).resize((430, 430), Image.LANCZOS)
    og.paste(ph, (95, 100))
    d = ImageDraw.Draw(og)

    f_name = ImageFont.truetype(SERIF, 62)
    f_role = ImageFont.truetype(SANS, 27)
    f_meta = ImageFont.truetype(SANS, 24)
    f_kick = ImageFont.truetype(SERIF, 20)

    x0, y = 610, 148
    spaced(d, (x0, y), "HIJO KANG", f_name, INK, 3)
    y += 92
    d.line([(x0, y), (x0 + 300, y)], fill=INK, width=2)
    y += 34
    spaced(d, (x0, y), "PHONETICS · PHONOLOGY · MORPHOLOGY", f_kick, ACCENT, 1.6)
    y += 52
    d.text((x0, y), "Associate Professor of English", font=f_role, fill=(51, 51, 51))
    y += 38
    d.text((x0, y), "Language and Literature", font=f_role, fill=(51, 51, 51))
    y += 50
    d.text((x0, y), "Chonnam National University", font=f_meta, fill=MUTED)

    d.line([(95, H - 58), (W - 95, H - 58)], fill=RULE, width=1)
    d.text((95, H - 44), "hijokang.duckdns.org", font=f_meta, fill=MUTED)

    og.save(os.path.join(out_dir, "og-image.jpg"), quality=90, optimize=True,
            progressive=True)

    for n in ("profile.jpg", "profile-square.jpg", "og-image.jpg"):
        p = os.path.join(out_dir, n)
        print(f"  {n:20s} {Image.open(p).size} {os.path.getsize(p):,}바이트")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
