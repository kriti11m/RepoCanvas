// Debug script to test graph data
fetch('http://localhost:8000/graph')
  .then(response => response.json())
  .then(data => {
    console.log('Graph Data Structure:');
    console.log('Total nodes:', data.nodes?.length || 0);
    console.log('Total edges:', data.edges?.length || 0);
    
    if (data.nodes?.length > 0) {
      console.log('First few nodes:');
      data.nodes.slice(0, 5).forEach((node, i) => {
        console.log(`${i + 1}.`, {
          id: node.id,
          name: node.name,
          type: node.type,
          file: node.file
        });
      });
    }
    
    if (data.edges?.length > 0) {
      console.log('First few edges:');
      data.edges.slice(0, 5).forEach((edge, i) => {
        console.log(`${i + 1}.`, {
          source: edge.source,
          target: edge.target,
          type: edge.type
        });
      });
    }
  })
  .catch(error => {
    console.error('Error fetching graph data:', error);
  });