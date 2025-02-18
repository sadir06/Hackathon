import React, { useRef } from 'react';
import {
  Box,
  Button,
  Center,
  Input,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';
import axios from 'axios';

const FileUpload = ({ onFileProcessed, setIsLoading, toast }) => {
  const fileInputRef = useRef();
  const bgColor = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      toast({
        title: 'Invalid file type',
        description: 'Please upload a PDF file',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsLoading(true);
      const response = await axios.post('/api/process-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      onFileProcessed(response.data);
      toast({
        title: 'Success',
        description: 'Your PDF has been processed successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to process PDF',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Center>
      <Box
        p={8}
        bg={bgColor}
        borderRadius="lg"
        borderWidth={2}
        borderStyle="dashed"
        borderColor={borderColor}
        w="full"
        maxW="600px"
      >
        <VStack spacing={4}>
          <Text fontSize="lg" fontWeight="medium">
            Upload your lecture notes (PDF)
          </Text>
          <Input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            ref={fileInputRef}
            display="none"
          />
          <Button
            colorScheme="teal"
            onClick={() => fileInputRef.current.click()}
            size="lg"
          >
            Choose File
          </Button>
          <Text fontSize="sm" color="gray.500">
            Maximum file size: 10MB
          </Text>
        </VStack>
      </Box>
    </Center>
  );
};

export default FileUpload; 