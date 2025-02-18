import React, { useState } from 'react';
import { ChakraProvider, Box, VStack, Heading, Text, useToast } from '@chakra-ui/react';
import ReactFlow, { Background, Controls } from 'react-flow-renderer';
import FileUpload from './components/FileUpload';
import FlowChart from './components/FlowChart';

function App() {
  const [flowData, setFlowData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleFileProcessed = (data) => {
    setFlowData(data);
  };

  return (
    <ChakraProvider>
      <Box minH="100vh" bg="gray.50" p={8}>
        <VStack spacing={8} align="stretch">
          <Box textAlign="center" py={10}>
            <Heading as="h1" size="2xl" color="teal.600">
              LectureFlowViz
            </Heading>
            <Text mt={4} fontSize="xl" color="gray.600">
              Transform your lecture notes into interactive flowcharts
            </Text>
          </Box>

          <FileUpload 
            onFileProcessed={handleFileProcessed}
            setIsLoading={setIsLoading}
            toast={toast}
          />

          {flowData && (
            <Box
              bg="white"
              p={6}
              borderRadius="lg"
              boxShadow="xl"
              h="600px"
              position="relative"
            >
              <FlowChart data={flowData} />
            </Box>
          )}
        </VStack>
      </Box>
    </ChakraProvider>
  );
}

export default App; 