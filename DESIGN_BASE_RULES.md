# Design Base Rules

Base design rules for CostBench / Scloda product surfaces.

## Objective

This document defines the default design language for dashboard pages, product modules, and new feature views.

The goal is consistency:
- premium but dense
- intelligent but not academic
- product-first, not template-first
- dark financial interface with clear hierarchy

## Core Principle

New screens should feel like part of the same operating system.

They should not look like:
- isolated landing pages
- startup templates
- oversized marketing heroes inside the dashboard
- generic AI product clones

They should feel like:
- a research terminal
- an investor workflow surface
- a decision-support product

## Product Tone

The visual tone should communicate:
- seriousness
- clarity
- analytical depth
- modern infrastructure
- controlled intelligence

Avoid:
- playful SaaS energy
- empty space used only for drama
- bright random gradients
- giant text blocks with no operational value

## Layout Rules

### 1. Dashboard-first structure

Inside authenticated product views, prefer:
- compact page headers
- modular panels
- card-based composition
- clear vertical rhythm
- actionable sections

Do not default to:
- full-screen hero sections
- oversized billboard headlines
- long marketing copy above the fold

### 2. Width and density

Use a controlled content width:
- preferred max width: `1200px`
- use grid layouts for sections
- avoid stretched content that feels empty

Pages should feel information-rich, not crowded.

### 3. Section hierarchy

Each page should usually have:
1. compact header or intro
2. main functional panels
3. secondary panels or supporting modules
4. CTA only where it helps workflow

## Visual Language

### 1. Surface system

Default surfaces:
- dark translucent panels
- subtle borders
- soft blur when useful
- restrained gradients
- depth through layering, not noise

Recommended traits:
- border radius: `12px` to `18px`
- border color: subtle slate / graphite
- background: deep navy / charcoal / black-blue
- shadows: soft, low-opacity, structural

### 2. Cards

Cards are the main primitive.

Every card should have:
- a clear purpose
- compact internal spacing
- strong title hierarchy
- readable supporting text
- one main action or no action

Cards should not feel decorative.

### 3. Color usage

Base palette direction:
- deep charcoal / navy background
- cool grays for structure
- green for value / positive movement / activation
- blue for data / navigation / system signals
- gold only for premium / operator / high-tier emphasis
- violet only where frontier-tech or lab positioning needs it

Rules:
- use accent colors sparingly
- one section should usually have one dominant accent
- avoid rainbow interfaces

## Typography

### 1. Headlines

Inside product pages:
- keep headlines compact
- prioritize utility over drama
- large type must still feel operational

Recommended:
- page title: medium-large
- panel title: compact and sharp
- supporting copy: short and specific

Avoid:
- giant 5-line marketing headings in dashboard views
- vague statements with no functional meaning

### 2. Body copy

Copy should be:
- short
- direct
- structured around use
- product-aware

Good copy explains:
- what this module does
- why it matters
- what the user can do next

## Interaction Rules

### 1. CTAs

Every CTA should correspond to a real next step.

Good CTA examples:
- `Explore the lab`
- `Upgrade to Investor`
- `Analyze with Scloda`
- `Open thesis board`

Avoid:
- decorative buttons
- duplicate actions
- vague labels like `Learn more` when the flow is product-internal

### 2. Hover and motion

Motion should be subtle and useful.

Use:
- light lift on cards
- soft opacity or border emphasis
- simple entrance transitions

Avoid:
- constant animation
- exaggerated hover effects
- movement that fights data readability

## Page-Specific Rules

### Subscription / pricing views

Subscription pages inside the dashboard should:
- feel like membership configuration
- explain value through capabilities
- connect pricing to usage and workflow depth

They should not feel like:
- a consumer checkout landing page
- a random SaaS pricing template

Good structure:
- compact membership intro
- plan cards
- capability explanation
- feature unlock logic
- clear product philosophy

### Labs / experimental views

Experimental views like Quantum Lab should feel like:
- a research workspace
- an emerging product surface
- a system for exploration and signal-building

They should include:
- a clear framing of purpose
- operational modules
- community or agent loops
- visible experimentation logic

They should not be just:
- a feed wrapper
- a static content page

### News views

News is not just a feed.

It should behave as:
- a curated signal layer
- a summary surface
- an input into AI workflows

So each news view should make room for:
- source context
- update state
- analysis actions
- categorization or segmentation

## Scloda Design Rules

### 1. Scloda is not a toy chatbot

Scloda should be positioned visually and behaviorally as:
- an analyst
- a copilot for decisions
- a controlled intelligence layer

Not as:
- a freeform chat toy
- a generic assistant bubble

### 2. Personalization model

Product rule:
- we control the analyst core
- the user controls the lens

That means users may tune:
- risk profile
- regions of interest
- explanation depth
- research themes
- notification priorities

That does not mean users should rewrite:
- system behavior
- reasoning rules
- safety framing
- financial communication standards

### 3. Date and data clarity

For market and financial data:
- always prefer explicit dates
- avoid ambiguous “currently” if the data is from another effective date
- make freshness understandable

Trust improves when time context is visible.

## Content Rules

Every module should answer at least one of these:
- What happened?
- Why does it matter?
- What can the user do now?
- What is the signal?
- What should be explored next?

If a section answers none of those, it is probably decoration.

## Build Rule

Before shipping a new view, check:

1. Does it feel native to the dashboard?
2. Is the hierarchy compact and readable?
3. Is there too much empty hero space?
4. Are accent colors controlled?
5. Does the module have operational value?
6. Would this still look credible to an investor or operator?

If the answer to `6` is no, redesign it.

## Short Version

If in doubt, build for this feeling:

`premium research product > AI toy`

`decision surface > marketing page`

`dense clarity > dramatic emptiness`
