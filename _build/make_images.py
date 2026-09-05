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
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# 원본(1145x1374) 기준 잘라낼 자리
# 세로 사진은 4:5. 잘라내는 범위를 넓힐수록 인물이 작게 담긴다 —
# 1059x1324 는 이전(900x1125)보다 17.6% 넓어, 인물이 85% 크기로 들어간다.
PORTRAIT_BOX = (86, 50, 1145, 1374)     # 4:5, 흔드는 손과 여백까지
FACE_BOX = (145, 140, 805, 800)         # 정사각, 얼굴 중심 (머리 위 여백 확보)

# 톤 보정 — 사이트가 흰 바탕이라 원본 그대로 쓰면 사진만 무겁게 가라앉는다.
# 중간톤을 올리고(GAMMA), 검정을 들어올리고(LIFT), 빨강을 조금 더해 따뜻하게 한다.
# 배경 현수막의 원색이 튀므로 채도는 낮춘다.
TONE = dict(gamma=0.78, r_gain=1.050, b_gain=0.950,
            saturation=0.87, contrast=0.95, lift=0.12)


# 배경 손질. 오른쪽 흰 난간이 y≈120 에서 꺾여 위로 비스듬히 빠지는데,
# 크롭을 넓히면서 그 꺾인 부분이 화면에 들어와 세로선이 틀어져 보였다.
# 곧게 뻗은 아래 구간을 위로 이어 붙여 난간이 곧게 지나가게 한다.
RAIL = dict(src=(986, 146, 1104, 286), paste_at=(6, -134), x=986)


def straighten_rail(im, src, paste_at, x):
    strip = im.crop(src)
    for top in paste_at:
        im.paste(strip, (x, top))
    return im


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


# 피부 결 정리. 얼굴에만 적용하고, 눈·안경·머리카락 같은 윤곽은 지킨다.
# strength 를 0.8 넘게 올리면 밀랍처럼 보이므로 이 선을 넘기지 않는다.
#
# protect 는 **안경이 지나가는 띠**다. 금테가 얇고 살색과 밝기가 비슷해
# edge_keep 문턱에 걸리지 않고 뭉개졌다. 그 구간만 통째로 빼면 테는 원본대로
# 남으면서 이마·볼 보정은 그대로 간다. feather 로 가장자리를 풀어 이음매를 없앤다.
SKIN = dict(strength=0.62, radius=3.0, edge_keep=20,
            protect=(295, 415, 775, 645), feather=26)


def smooth_skin(im, strength, radius, edge_keep, protect, feather):
    """살색인 곳만 부드럽게. 윤곽과 안경 띠는 건드리지 않는다."""
    import numpy as np

    a = np.asarray(im, dtype=np.float32)
    blur = np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)

    hsv = np.asarray(im.convert("HSV"), dtype=np.float32)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    skin = (((hue <= 30) | (hue >= 235)) & (sat > 28) & (sat < 190)
            & (val > 70)).astype(np.uint8) * 255
    skin = np.asarray(Image.fromarray(skin).filter(ImageFilter.GaussianBlur(6)),
                      dtype=np.float32) / 255.0

    zone = Image.new("L", im.size, 255)
    ImageDraw.Draw(zone).rectangle(protect, fill=0)
    zone = np.asarray(zone.filter(ImageFilter.GaussianBlur(feather)),
                      dtype=np.float32) / 255.0

    edge = np.abs(a - blur).mean(axis=2)
    keep = np.clip(1.0 - edge / edge_keep, 0, 1)

    w = (skin * keep * zone * strength)[..., None]
    return Image.fromarray(np.clip(a * (1 - w) + blur * w, 0, 255).astype(np.uint8))


# 배경 회색 처리. 사진 뒤의 현수막이 원색이라 흰 바탕 사이트에서 튄다.
# 배경을 **잘라내지 않고 채도만 뺀다** — 마스크가 조금 어긋나도 잘린 자국이 안 생긴다.
BG = dict(erode=5, blur=1.8, lighten=1.06,
          # 사람에게 있는 색만 남긴다 (PIL 색상값 0~255)
          skin_hi=34, skin_lo=239,     # 살색: 붉은 쪽 양끝
          blue_lo=134, blue_hi=168,    # 셔츠 파랑
          # 현수막에도 같은 파랑이 있어서, 파랑은 셔츠가 있는 아래쪽에서만 살린다
          blue_from=600, blue_to=760)


def gray_background(im, erode, blur, lighten, skin_hi, skin_lo,
                    blue_lo, blue_hi, blue_from, blue_to):
    from rembg import new_session, remove

    w, h = im.size
    person = remove(im, session=new_session("u2net")).split()[-1]
    if erode:
        person = person.filter(ImageFilter.MinFilter(erode))

    hue = im.convert("HSV").split()[0]
    skin = hue.point(lambda x: 255 if (x <= skin_hi or x >= skin_lo) else 0)
    blue = hue.point(lambda x: 255 if blue_lo <= x <= blue_hi else 0)

    col = Image.new("L", (1, h))
    col.putdata([0 if y < blue_from else
                 (255 if y > blue_to else
                  int((y - blue_from) / (blue_to - blue_from) * 255))
                 for y in range(h)])
    blue = ImageChops.multiply(blue, col.resize((w, h)))

    keep = ImageChops.lighter(skin, blue).filter(ImageFilter.MedianFilter(5))
    mask = ImageChops.multiply(person, keep).filter(ImageFilter.GaussianBlur(blur))

    flat = ImageEnhance.Color(im).enhance(0.0)
    flat = ImageEnhance.Brightness(flat).enhance(lighten)
    return Image.composite(im, flat, mask)


INK = (17, 17, 17)
MUTED = (118, 118, 118)
ACCENT = (21, 86, 132)          # style.css 의 --accent 와 같은 값 (#155684)
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
    im = straighten_rail(im, **RAIL)
    im = warm(im, **TONE)
    im = smooth_skin(im, **SKIN)
    im = gray_background(im, **BG)
    print("배경 회색 처리 완료")

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
