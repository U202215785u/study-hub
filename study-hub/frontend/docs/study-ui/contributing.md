# Contributing To Study UI

## Required Rules

- Applications import only from `@study-ui`.
- Primitives do not access API clients or Pinia business stores.
- Widgets emit identifiers and do not mutate caller-owned objects.
- New public components require tests, stories, accessibility notes and tokens.
- Raw colors are prohibited outside `tokens.css` and documented content assets.
- Breaking prop or slot changes require a deprecation note before removal.

### Homepage Button Standard

- Use `UiButton`, `UiPillButton` or `UiIconButton` for homepage actions. Raw `button` elements are reserved for content rows whose geometry is part of the widget design, such as calendar days and task rows.
- Keep one component, size and shape for controls with the same role. The shared typography scale is `md: 14px/700`, `sm: 12px/700` and `xs: 10px/700`, all from `--ui-font-sans`.
- Set visual differences through public `variant`, `size`, `shape` and `block` props. Do not override a public button's `font`, `font-size`, `font-weight`, `padding`, `min-height` or `border-radius` from a widget stylesheet.
- Navigation links that sit beside button actions must use the same semantic tokens for typography, spacing, surface, border and pill radius.

## Adding A Component

1. Choose the functional category before naming the component. Do not add a new category for a single component.
2. Write its public behavior test first, including native semantics, event payloads and state precedence.
3. Implement visual decisions with existing semantic variables. Add a token only when the value represents a reusable design decision.
4. Add Storybook stories for default and every applicable edge state. Include a narrow or mobile example when width can change behavior.
5. Export the component from `src/design-system/index.js` and add its row to `component-status.md` in the same change.
6. Record an exact Figma component or frame node when one exists. Never create a plausible-looking node id.
7. Run `npm run verify:study-ui`. For homepage or layout changes also run `node tests/home-responsive.mjs`.

## API Design

- Prefer native HTML behavior and familiar event names.
- Use controlled values (`modelValue`) for form components.
- Use content tones only for classification and status names only for operational state.
- Loading, error, empty and content states must not render simultaneously.
- Icon-only controls require a visible tooltip and an accessible name.
- Widget events carry an id or another small serializable key; pages resolve the full object and perform side effects.

## Review Checklist

- The component has one clear responsibility and belongs to an existing category.
- Public props have defaults or required declarations and constrained values use validators.
- Keyboard focus is visible and focus order follows reading order.
- Color is not the only way status is communicated.
- Long text cannot resize fixed controls, overlap adjacent content or cause horizontal overflow.
- Storybook builds without accessibility configuration errors.
- Documentation and Figma mapping match the public export.
