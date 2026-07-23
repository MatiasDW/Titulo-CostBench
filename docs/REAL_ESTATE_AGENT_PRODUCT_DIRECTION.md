# Scloda Real Estate Agent: Product Direction

Status as of July 22, 2026.

This document incorporates the attached deep-research report on a Chile-focused real-estate AI agent and maps it against the current CostBench product.

## What exists today

- `Scloda Trade`: macro, commodities, crypto, and paper-trading explanation.
- `Scloda Real Estate`: seeded commune-level dashboard, affordability simulation, and basic advisory.
- `News`: international/chile-facing market headlines with Scloda explanation.
- `Scloda Chat`: guarded OpenRouter chat with tools, retrieval cache, traces, review queue, and selective judge pass.

## What is still missing relative to the target product

The report makes it clear that the final product is not "a chatbot with some property widgets". It is a data system with a conversational layer on top.

Current major gaps:

- No unified Chile real-estate data graph yet.
- No SII/MINVU/INE/CBR-grade ingestion pipeline yet.
- No PostGIS spatial model yet.
- No formal bronze/silver/gold pipeline for marketplace snapshots.
- No AVM stack yet.
- No commune/barrio/microzone comparable engine yet.
- No affordability engine tied to live employment/income layers.
- No registral/document due-diligence workflow.
- No institutional-grade maps for zoning, permits, or territorial overlays.

## Product target

Scloda should evolve into a Chile real-estate intelligence system with five product surfaces:

1. Conversational advisor
   Explain the market, compare communes, interpret risks, and answer traceably.

2. Property intelligence sheet
   One asset, one page: pricing, comparables, fiscal anchor, financing stress, and confidence.

3. Research dashboard
   Commune and micro-market analytics: supply, absorption, DOM, yields, affordability, and permits.

4. Due-diligence workspace
   Documents, registral checks, missing fields, and human review checkpoints.

5. Quantum Lab
   Experimental space where Scloda's capability tree, neural memory, research tracks, and future agent modules are visible and iterated.

## Recommended sequence

### Phase 1: Make the current agent safer and more inspectable

- Guardrails
- Retrieval memory
- Persistent traces
- Review queue
- Classifier/routing
- Knowledge index

This phase is now largely in place.

### Phase 2: Turn real estate into a true data product

- Add official-source ingestion layers:
  - Banco Central / BDE
  - INE / SIMEL
  - MINVU / IDE MINVU
  - SII-compatible property anchoring
- Move spatial data toward PostgreSQL + PostGIS
- Build normalized entity keys for property, comuna, region, and listing identity
- Add marketplace snapshot storage and deduplication

### Phase 3: Build institutional intelligence

- Comparable engine
- Yield and affordability stack
- Permit and supply pipeline
- Confidence scoring by data completeness
- Report generation with citations and clear evidence paths

### Phase 4: Premium Scloda

- Subscription-gated capabilities
- Research workspaces
- Scenario analysis
- Portfolio-level intelligence
- Human analyst escalation

## What the report changes in product thinking

The report shifts the final goal from "real estate tab" to "Chile property intelligence platform". That means:

- Scloda should become the main monetized layer.
- The dashboard is supporting infrastructure, not the product itself.
- The data model must be designed for Chile-specific keys and traceability first.
- Every answer should be explainable in terms of source, date, and confidence.

## Concrete next backlog

- Introduce `PostGIS` in the stack and start spatial schema separation.
- Add official real-estate source stubs and data contracts before adding more UI.
- Expand retrieval docs with source methodology and commune-level notes.
- Add comparable-analysis endpoints and commune research panels.
- Evolve Quantum Lab into the visible roadmap for Scloda's future capabilities.
