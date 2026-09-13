"""Check and re-encode uploaded thumbnail images.

An upload is only accepted after Pillow could decode it completely. What
gets stored is not the upload itself but its pixels written as a fresh
JPEG: appended payloads, polyglot tricks and metadata such as EXIF/GPS do
not survive that step.
"""

from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Pillow format names; also limits which decoders may touch an upload.
ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP")
# 5000 x 5000 is plenty for a thumbnail and keeps decompression bombs small.
MAX_PIXELS = 25_000_000


def validate_thumbnail_image(file):
    """Model validator: accept only a fully decodable JPEG, PNG or WebP."""
    try:
        file.seek(0)
        with Image.open(file, formats=ALLOWED_FORMATS) as image:
            image.verify()                  # structure and checksums
        file.seek(0)
        with Image.open(file, formats=ALLOWED_FORMATS) as image:
            width, height = image.size      # read from the header only
            if width * height > MAX_PIXELS:
                raise ValidationError(
                    "The image may have at most 25 megapixels.",
                    code="image_too_large",
                )
            image.load()                    # decode every pixel
        file.seek(0)
    except ValidationError:
        raise
    except Exception as exc:
        # Like Django's ImageField: broken or hostile files make Pillow
        # raise many different exception types.
        raise ValidationError(
            "Upload a valid JPEG, PNG or WebP image.",
            code="invalid_image",
        ) from exc


def reencode_as_jpeg(file) -> ContentFile:
    """Return the pixels of a validated upload as a freshly encoded JPEG."""
    file.seek(0)
    with Image.open(file, formats=ALLOWED_FORMATS) as image:
        # Apply the EXIF rotation now; the EXIF block itself is dropped.
        image = ImageOps.exif_transpose(image).convert("RGBA")
    # JPEG has no alpha channel: put transparent areas on white.
    background = Image.new("RGBA", image.size, "white")
    flat = Image.alpha_composite(background, image).convert("RGB")

    buffer = BytesIO()
    flat.save(buffer, format="JPEG", quality=90)
    return ContentFile(buffer.getvalue(), name="thumbnail.jpg")
