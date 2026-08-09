# Content Parser Markdown Rendering Design

## Goal

Make documents opened from `/content-parser` render Markdown through the same shared reading surface used by the home page and knowledge base.

## Scope

Replace the content parser modal's raw `<pre>` output with `MarkdownRenderer`. Preserve the existing modal shell, document title, asynchronous document fetch, close control, and ASR failure notice.

## Architecture

`ContentParser.vue` imports the existing `MarkdownRenderer.vue` component and supplies `document.content` as its `content` prop when a document is open. The shared component already owns marked GFM parsing, external-link handling, wiki-link events, reading themes, font-size preferences, and typography.

No parser API, document schema, queue behavior, or Markdown parsing rules change. The modal remains the content parser's ownership boundary; only its body renderer changes.

## Error Handling

The existing `documentFailure` alert remains above the reader. A fallback or failed ASR document still exposes its status code and reason while its available content is rendered through the shared reader.

## Verification

Add a content parser view test with headings, emphasis, a list, inline code, and a GFM table. It must assert that the modal mounts `MarkdownRenderer` output and no raw `<pre>` remains. Retain the existing ASR error test, then run the focused test file and the frontend production build.

## Delivery

Accepted on 2026-08-10. The implementation reuses `MarkdownRenderer` in `ContentParser.vue`; the regression test verifies headings, emphasis, lists, inline code, and GFM tables render through `.markdown-content` instead of a raw `<pre>`. The frontend unit suite passed 181 tests in 76 files, and the Vite production build completed successfully.
