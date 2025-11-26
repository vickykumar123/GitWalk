/**
 * DependencyGraph - D3.js Force-Directed Graph Visualization
 *
 * Displays file dependencies as an interactive graph.
 * - Nodes: Files in the repository
 * - Edges: Import relationships between files
 */

import {useEffect, useRef, useState} from "react";
import * as d3 from "d3";
import type {GraphNode, GraphEdge} from "@/hooks/query/repository";

// Language colors (matching file tree)
const LANGUAGE_COLORS: Record<string, string> = {
  python: "#3572A5",
  javascript: "#f1e05a",
  typescript: "#3178c6",
  rust: "#dea584",
  go: "#00ADD8",
  java: "#b07219",
  c: "#555555",
  cpp: "#f34b7d",
  php: "#4F5D95",
  ruby: "#701516",
  default: "#8b5cf6",
};

interface DependencyGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  selectedNodeId?: string | null;
}

// Extended node type for D3 simulation
interface SimulationNode extends GraphNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

// Extended edge type for D3 simulation
interface SimulationEdge {
  source: SimulationNode | string;
  target: SimulationNode | string;
  type: string;
}

export default function DependencyGraph({
  nodes,
  edges,
  onNodeClick,
  selectedNodeId,
}: DependencyGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({width: 800, height: 600});
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const {width, height} = containerRef.current.getBoundingClientRect();
        setDimensions({width, height});
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // D3 visualization
  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const {width, height} = dimensions;

    // Create container group for zoom/pan
    const g = svg.append("g");

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create arrow marker for edges
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "-0 -5 10 10")
      .attr("refX", 28)
      .attr("refY", 0)
      .attr("orient", "auto")
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .append("path")
      .attr("d", "M 0,-5 L 10,0 L 0,5")
      .attr("fill", "#6b7280");

    // Prepare data for simulation
    const simulationNodes: SimulationNode[] = nodes.map((d) => ({...d}));
    const simulationEdges: SimulationEdge[] = edges.map((d) => ({...d}));

    // Create force simulation
    const simulation = d3.forceSimulation(simulationNodes)
      .force("link", d3.forceLink<SimulationNode, SimulationEdge>(simulationEdges)
        .id((d) => d.id)
        .distance(180)
        .strength(1.2)
      )
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(35));

    // Draw edges
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(simulationEdges)
      .join("line")
      .attr("stroke", "#4b5563")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrowhead)");

    // Draw nodes
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll<SVGGElement, SimulationNode>("g")
      .data(simulationNodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(d3.drag<SVGGElement, SimulationNode>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Node circles
    node.append("circle")
      .attr("r", (d) => d.has_external_dependencies ? 18 : 14)
      .attr("fill", (d) => LANGUAGE_COLORS[d.language?.toLowerCase()] || LANGUAGE_COLORS.default)
      .attr("stroke", (d) => d.id === selectedNodeId ? "#fff" : "transparent")
      .attr("stroke-width", 2)
      .attr("opacity", 0.9);

    // Node labels
    node.append("text")
      .text((d) => d.filename)
      .attr("x", 22)
      .attr("y", 5)
      .attr("font-size", "12px")
      .attr("fill", "#d1d5db")
      .attr("pointer-events", "none");

    // Node interactions
    node
      .on("click", (event, d) => {
        event.stopPropagation();
        onNodeClick?.(d);
      })
      .on("mouseenter", (event, d) => {
        setHoveredNode(d.id);
        // Highlight connected edges
        link.attr("stroke-opacity", (l) => {
          const source = typeof l.source === "object" ? l.source.id : l.source;
          const target = typeof l.target === "object" ? l.target.id : l.target;
          return source === d.id || target === d.id ? 1 : 0.2;
        });
        link.attr("stroke", (l) => {
          const source = typeof l.source === "object" ? l.source.id : l.source;
          const target = typeof l.target === "object" ? l.target.id : l.target;
          return source === d.id || target === d.id ? "#8b5cf6" : "#4b5563";
        });
      })
      .on("mouseleave", () => {
        setHoveredNode(null);
        link.attr("stroke-opacity", 0.6);
        link.attr("stroke", "#4b5563");
      });

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimulationNode).x!)
        .attr("y1", (d) => (d.source as SimulationNode).y!)
        .attr("x2", (d) => (d.target as SimulationNode).x!)
        .attr("y2", (d) => (d.target as SimulationNode).y!);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    // Initial zoom to fit
    const initialScale = Math.min(
      width / 1000,
      height / 800,
      1
    );
    svg.call(zoom.transform, d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(initialScale)
      .translate(-width / 2, -height / 2)
    );

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, dimensions, selectedNodeId, onNodeClick]);

  // Find hovered node data for tooltip
  const hoveredNodeData = hoveredNode ? nodes.find((n) => n.id === hoveredNode) : null;

  return (
    <div ref={containerRef} className="relative w-full h-full bg-[var(--bg-primary)]">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
      />

      {/* Tooltip */}
      {hoveredNodeData && (
        <div className="absolute top-4 left-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-3 shadow-lg max-w-xs">
          <p className="font-mono text-sm font-medium truncate">{hoveredNodeData.path}</p>
          <div className="flex items-center gap-2 mt-2 text-xs text-[var(--text-muted)]">
            <span className="px-1.5 py-0.5 rounded bg-[var(--bg-primary)] capitalize">
              {hoveredNodeData.language}
            </span>
            {hoveredNodeData.functions.length > 0 && (
              <span>{hoveredNodeData.functions.length} functions</span>
            )}
            {hoveredNodeData.classes.length > 0 && (
              <span>{hoveredNodeData.classes.length} classes</span>
            )}
          </div>
          {hoveredNodeData.has_external_dependencies && (
            <p className="text-xs text-yellow-500 mt-1">Has external dependencies</p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-3">
        <p className="text-xs font-medium mb-2 text-[var(--text-muted)]">Languages</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {Object.entries(LANGUAGE_COLORS).slice(0, 6).map(([lang, color]) => (
            <div key={lang} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{backgroundColor: color}}
              />
              <span className="text-xs capitalize">{lang}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Controls hint */}
      <div className="absolute bottom-4 left-4 text-xs text-[var(--text-muted)]">
        Scroll to zoom • Drag to pan • Click node to view file
      </div>
    </div>
  );
}
