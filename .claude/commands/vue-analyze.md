# Vue Component Analyzer

Analyze all Vue components in `client/src/views/` and `client/src/composables/` for performance issues and code reuse opportunities. Optionally accepts a single component path as argument (e.g., `/vue-analyze Orders.vue`).

## Analysis Steps

### 1. Component Structure Audit

For each `.vue` file, read the full contents and check:

- **Options API vs Composition API**: Flag any inconsistency (project standard: Composition API with `setup()`)
- **Template complexity**: Count v-for nesting depth, inline expressions, and computed-vs-inline balance
- **Script size**: Flag components over 300 lines as candidates for extraction
- **Prop/emit surface**: Identify missing prop validation or unused props

### 2. Performance Analysis

Check each component for:

- **Expensive computed properties**: Computed properties that iterate large arrays or do O(n²) work — suggest caching or pagination
- **Missing keys in v-for**: Any v-for using `index` as key instead of a stable identifier
- **Reactive overhead**: Large objects stored in `ref()` / `reactive()` that could use `shallowRef()`
- **Watcher anti-patterns**: `watch` with `{ immediate: true, deep: true }` on large objects — suggest targeted watchers
- **Unnecessary re-renders**: Inline object/array literals in templates (e.g., `:style="{ color: 'red' }"`) that create new references each render
- **API call patterns**: Multiple sequential awaits that could be parallelized with `Promise.all()`
- **Large template expressions**: Complex ternaries or chained method calls in templates that should be computed properties

### 3. Code Reuse Opportunities

Identify duplication across components:

- **Repeated data-fetching patterns**: Loading/error/data tri-state setup duplicated across views — suggest extracting a `useFetch` or `useAsyncData` composable
- **Shared UI patterns**: Identical table markup, stat cards, badge rendering, or filter handling appearing in multiple components — suggest extracting shared components
- **Duplicated utility logic**: Date formatting, currency formatting, status mapping functions repeated across files — suggest a shared utils module
- **Composable opportunities**: Related refs + computed + watchers that appear together in multiple components — suggest extracting as a composable
- **CSS duplication**: Identical or near-identical style blocks across component `<style>` sections — suggest moving to shared styles in App.vue or a CSS module

### 4. i18n Consistency

- Check for hardcoded strings in templates that should use `t()` calls
- Verify all `t()` keys used in templates exist in `client/src/locales/en.js`

## Output Format

Present findings as a structured report:

```
## Vue Component Analysis Report

### Summary
- Components analyzed: X
- Performance issues: X (Y critical, Z minor)
- Code reuse opportunities: X
- i18n gaps: X

### Critical Issues
[Items that should be fixed — real performance problems or bugs]

### Performance Recommendations
[Sorted by estimated impact, with specific file:line references]

### Code Reuse Opportunities
[Grouped by type — composables, shared components, utilities]

### i18n Gaps
[Hardcoded strings with their locations]
```

For each finding, include:

- **File and line number** (e.g., `Orders.vue:45`)
- **What**: One-sentence description of the issue
- **Why it matters**: Performance impact or maintenance cost
- **Suggested fix**: Concrete code change or extraction, not a vague recommendation

Do NOT modify any files. This is a read-only analysis. If the user wants to apply fixes, they should ask separately.
