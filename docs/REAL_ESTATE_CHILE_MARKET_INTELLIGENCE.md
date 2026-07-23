# Real Estate Chile Market Intelligence

Condensed notes from the July 2026 market research reports attached to this workspace.

## Core principle

The product should behave as a Chile real-estate intelligence layer first and a chatbot second. Useful answers depend on combining macro, affordability, territorial risk, registral/cadastral context, and micro-market supply signals.

## Sources that matter most

- Banco Central de Chile and CMF for UF, rates, debt, mortgage and macro-financial context.
- INE and SIMEL for labor market, income, census structure, and permits.
- MINVU and IDE MINVU for deficit, urban policy, zoning and geospatial layers.
- SII for fiscal valuation, cadastral anchors and property identity.
- Conservadores / CBR and municipal sources for titles, restrictions and local permits.
- Portals such as Portalinmobiliario, TOCTOC, Yapo and similar only as market-live complements, not as the sole truth source.

## Product implications

- Distinguish price asked, appraised value, fiscal value, and transacted price.
- Treat affordability as a first-class signal, not just price per square meter.
- Combine real-estate metrics with mortgage cost, income pressure, unemployment and permits.
- Add territorial risk: flood, tsunami, wildfire, evacuation, regulatory constraints and accessibility.
- Build a master-property record rather than isolated chatbot answers.

## Priority metrics

- UF/m2 and price in real CLP.
- Days on market, months of inventory and absorption.
- Gross/net rental yield and affordability ratio.
- Mortgage rate, LTV, DTI and financial burden.
- Housing deficit, permits, receptions and pipeline pressure.
- Spatial risk and zoning constraints by commune and microzone.

## Recommended architecture direction

- PostgreSQL + PostGIS as canonical system of record.
- pgvector/native vector search for retrieval over structured knowledge.
- DuckDB for analytical marts and exploration.
- Real-estate specific feature store combining macro, cadastral, geospatial and listing data.
- RAG only on top of validated sources and reproducible metrics.

## Scloda implications

- The agent should answer with source hierarchy and confidence, not generic prose.
- It should know whether a value is live, cached, estimated or historical.
- It should support underwriting, valuation, market comparison, and territorial risk analysis as distinct tasks.
