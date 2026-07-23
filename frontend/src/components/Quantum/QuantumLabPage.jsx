import React, { useEffect, useState } from 'react';
import './QuantumLabPage.css';

const STATUS_COLORS = {
  active: 'status-active',
  in_progress: 'status-progress',
  planned: 'status-planned',
};

export default function QuantumLabPage() {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    fetch('/api/v1/scloda/capabilities', { credentials: 'include' })
      .then((res) => res.json())
      .then((data) => {
        if (!mounted) return;
        setNodes(data.nodes || []);
      })
      .catch(() => {
        if (!mounted) return;
        setError('Quantum Lab is unavailable right now.');
      })
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  const rootNodes = nodes.filter((node) => !node.parent_slug);
  const childrenFor = (slug) => nodes.filter((node) => node.parent_slug === slug);
  const quantumChildren = childrenFor('scloda-quantum-lab');
  const neuralTracks = [
    {
      label: 'Dataset Layer',
      status: 'live now',
      description: 'Trace logs, review queue outcomes, retrieved chunks, and structured schema memory form the early training substrate.',
    },
    {
      label: 'Vector Memory',
      status: 'live now',
      description: 'pgvector retrieval stores embeddings natively in Postgres so Scloda can ground answers before spending extra tokens.',
    },
    {
      label: 'Neural Training Loop',
      status: 'next build',
      description: 'Human-reviewed conversations, labeled intents, and failure clusters will become the first supervised dataset for future tuning.',
    },
    {
      label: 'Research Sandbox',
      status: 'planned',
      description: 'Quantum computing, neural-network experiments, and domain graph expansion all live here before reaching the production agent.',
    },
  ];
  const architectureColumns = [
    {
      title: 'Inputs',
      items: ['User prompt', 'Profile + risk context', 'Active page context'],
    },
    {
      title: 'Agent Core',
      items: ['Guardrails', 'Task router', 'OpenRouter model'],
    },
    {
      title: 'Grounding',
      items: ['pgvector memory', 'Market/real-estate tools', 'Knowledge chunks'],
    },
    {
      title: 'Trust Layer',
      items: ['Confidence scoring', 'Human review queue', 'Capability roadmap'],
    },
  ];

  const renderBranch = (node, depth = 0) => {
    const children = childrenFor(node.slug);
    const isRoot = depth === 0;

    return (
      <div key={node.slug} className={`quantum-branch quantum-depth-${Math.min(depth, 2)}`}>
        <div className={`quantum-node ${isRoot ? 'quantum-node-root' : ''}`}>
          <div className="quantum-node-top">
            <span className={`quantum-status ${STATUS_COLORS[node.status] || 'status-planned'}`}>
              {node.status.replace('_', ' ')}
            </span>
            <span className="quantum-score">{node.maturity_score}%</span>
          </div>
          {isRoot ? <h3>{node.label}</h3> : <h4>{node.label}</h4>}
          <p>{node.description}</p>
          <small>{node.domain}</small>
        </div>

        {children.length > 0 && (
          <div className="quantum-branches">
            {children.map((child) => renderBranch(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="quantum-lab-page">
      <section className="quantum-hero">
        <span className="quantum-kicker">Scloda Research Layer</span>
        <h1>Quantum Lab</h1>
        <p>
          This is where Scloda stops being only a chatbot and becomes a growing intelligence
          system: memory, review loops, market logic, neural branches, and future Chile real-estate modules.
        </p>
      </section>

      <section className="quantum-grid">
        <article className="quantum-card">
          <h2>What this space is for</h2>
          <p>
            Train Scloda gradually, track capability maturity, and expose what is already live versus what still needs
            data, research, or human validation.
          </p>
        </article>
        <article className="quantum-card">
          <h2>Why it matters</h2>
          <p>
            The final product is not a generic assistant. It is a Chile-focused intelligence platform for trade,
            real estate, risk, and research with explainable growth paths.
          </p>
        </article>
      </section>

      <section className="quantum-card quantum-spotlight">
        <div className="quantum-spotlight-copy">
          <span className="quantum-section-label">Neural Network Workspace</span>
          <h2>Where Scloda learns next</h2>
          <p>
            This lab now shows the real upgrade path: captured conversations, vector memory,
            supervised review outcomes, and future neural-network training blocks.
          </p>
        </div>

        <div className="quantum-track-grid">
          {neuralTracks.map((track) => (
            <article key={track.label} className="quantum-track-card">
              <div className="quantum-track-status">{track.status}</div>
              <h3>{track.label}</h3>
              <p>{track.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="quantum-card quantum-diagram-shell">
        <div className="quantum-tree-header">
          <div>
            <span className="quantum-section-label">Current Diagram</span>
            <h2>Scloda System Map</h2>
            <p>The current agent path from user input to grounded output and review.</p>
          </div>
        </div>

        <div className="quantum-architecture-grid">
          {architectureColumns.map((column) => (
            <div key={column.title} className="quantum-architecture-column">
              <h3>{column.title}</h3>
              {column.items.map((item) => (
                <div key={item} className="quantum-architecture-node">{item}</div>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section className="quantum-tree-shell">
        <div className="quantum-tree-header">
          <div>
            <h2>Scloda Capability Tree</h2>
            <p>Live branches, nested modules, and planned research tracks.</p>
          </div>
        </div>

        {loading && <div className="quantum-empty">Loading capability tree...</div>}
        {error && <div className="quantum-empty">{error}</div>}

        {!loading && !error && (
          <div className="quantum-tree">
            {rootNodes.map((root) => renderBranch(root))}
          </div>
        )}
      </section>

      {!loading && !error && quantumChildren.length > 0 && (
        <section className="quantum-card quantum-research-panel">
          <div className="quantum-tree-header">
            <div>
              <span className="quantum-section-label">Research Tracks</span>
              <h2>Quantum Lab Modules</h2>
              <p>Dedicated branches already defined for the lab instead of a generic placeholder.</p>
            </div>
          </div>

          <div className="quantum-track-grid">
            {quantumChildren.map((node) => (
              <article key={node.slug} className="quantum-track-card">
                <div className={`quantum-track-status quantum-track-status-${node.status}`}>
                  {node.status.replace('_', ' ')}
                </div>
                <h3>{node.label}</h3>
                <p>{node.description}</p>
                <small>{node.domain}</small>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
