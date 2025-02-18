import React, { useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from 'react-flow-renderer';

const FlowChart = ({ data }) => {
  // Transform the data into the format expected by ReactFlow
  const initialNodes = data.nodes.map(node => ({
    id: node.id,
    data: { label: node.text },
    position: { x: 0, y: 0 }, // Initial positions
    style: {
      background: '#fff',
      border: '1px solid #2B6CB0',
      borderRadius: '8px',
      padding: '10px',
      fontSize: '12px',
      width: 'auto',
      minWidth: '150px',
      textAlign: 'center',
    },
  }));

  const initialEdges = data.edges.map(edge => ({
    id: `${edge.from}-${edge.to}`,
    source: edge.from,
    target: edge.to,
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#2B6CB0' },
  }));

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Automatically layout the nodes in a tree structure
  React.useEffect(() => {
    const layoutNodes = nodes.map((node, index) => {
      const level = data.nodes.find(n => n.id === node.id).level;
      return {
        ...node,
        position: {
          x: (level - 1) * 300 + 50,
          y: index * 100 + 50,
        },
      };
    });
    setNodes(layoutNodes);
  }, [data]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      attributionPosition="bottom-right"
    >
      <Background />
      <Controls />
    </ReactFlow>
  );
};

export default FlowChart; 