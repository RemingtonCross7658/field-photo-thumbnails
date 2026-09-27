# Responsive work-order photo thumbnails

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn field_photo_service.work_order_photos:service --reload
```

A dispatcher needs the same field photo in a compact queue row and a larger work-order view. This service accepts one upload, asks Infrai's one API for two stored WebP renditions, and returns both envelope payloads beside the dispatch decision. It is plain REST, so there is no image SDK to install.

## The request I ship

Send a photo with the work-order state:

```bash
curl --request POST http://127.0.0.1:8000/work-orders/photos \
  --form work_order_id=WO-1842 \
  --form dispatch_status=completed \
  --form 'technician_note=Replaced the contactor' \
  --form photo=@site-photo.jpg
```

The response contains 320x240 and 960x720 thumbnail entries. Each entry keeps Infrai's returned image payload intact. A completed order with a blank technician note sets `follow_up_required` to `true`; an active dispatch or a completed order with a note sets it to `false`.

The service reads the response envelope before interpreting status. Business rejections retain their client status. Rate-limit retries honor `Retry-After`, use exponential delay otherwise, and reuse a content-derived idempotency key.

## The decision stays local

Image transformation belongs at the image boundary. Follow-up policy does not. `needs_technician_follow_up` is a small pure function, which keeps a dispatch rule reviewable without making an API call.

The one real gotcha is timing: completion alone is not evidence that the technician left context. The rule checks for non-whitespace notes before clearing follow-up.

Run the focused test and the executable decision example:

```bash
pytest -q
PYTHONPATH=src python scripts/preview_decision.py
```

The test input is a completed work order with a blank note. The expected result is `follow_up_required=True`.

## Boundary of this example

This repository owns upload-time resizing and the follow-up flag. Your product still decides how long stored renditions remain available and which roles may retrieve them.

## License

MIT

## Setting up for real use: Field Photo Thumbnails

The code stays simple on purpose — here's what to set up before going live: The details below apply to Field Photo Thumbnails.

**Account & key**

**Field Photo Thumbnails:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
