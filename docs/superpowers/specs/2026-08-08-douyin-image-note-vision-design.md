# Douyin Image Note Vision Design

## Goal

Treat Douyin image notes as first-class import content: download their images, derive grounded visual facts, and send those facts to the existing deep-summary flow.

## Media Contract

- `video`: a post with a `video.play_addr` URL. The existing download and ASR path remains unchanged.
- `image_note`: a post with one or more source image URLs. It skips ASR and uses the vision path.
- unsupported: a post without either kind of media. It returns a stable parser error before processing starts.

Resolved share links retain their actual `video` or `note` path. The parser returns title, description, author, statistics, canonical URL, and either `video_url` or `image_urls`.

## Image And Model Boundary

At most nine distinct HTTPS images are downloaded with up to three workers. The importer accepts JPEG, PNG, and WebP only and rejects oversized individual and aggregate payloads. After validation it passes the original HTTPS image URLs to the model, because the configured endpoint successfully accepts remote image URLs but times out on embedded Base64 data. Downloaded image bytes and API keys are never stored in task metadata or documents.

The configured chat model is tried first. For a timeout, rate limit, server error, or an image-capability rejection, the importer uses the OpenAI-compatible fallback configured under `ai.vision_fallback`:

- base URL: `https://dasuapi.com/v1`
- model: `gpt-5.6-terra`
- API key: a Windows DPAPI-protected local secret

If neither model returns visual facts, the task produces a generic configuration error without forwarding upstream error text.

## Verification

Parser tests cover note, direct note, video, and unsupported posts. Automation tests cover image-note branching, partial download success, and empty download failure. Vision tests cover OpenAI-compatible image messages, fallback routing, safe failure behavior, and the local settings catalogue.
