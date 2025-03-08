import React, { useState, useEffect } from 'react';
import { useApiService } from '../services/api';
import { createLogger } from '../utils/logging';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AINavigation from './AINavigation';

// Create a logger for the AIFilesPage component
const logger = createLogger('AIFilesPage');

const AIFilesPage = () => {
  const api = useApiService();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // State for AI files
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for file upload
  const [csvFile, setCsvFile] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  
  // Use case options (hardcoded like in AIConfigPage)
  const useCaseOptions = [
    { value: 'project_summary', label: 'Project Summary' },
    { value: 'relevance_extraction', label: 'Relevance Extraction' }
  ];
  
  // State for AI configurations
  const [selectedUseCase, setSelectedUseCase] = useState(useCaseOptions[0].value);
  const [configurations, setConfigurations] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState(null);
  
  // Load files and configurations on component mount
  useEffect(() => {
    loadFiles();
    loadConfigurations(selectedUseCase);
  }, []);
  
  // Load configurations when use case changes
  useEffect(() => {
    if (selectedUseCase) {
      loadConfigurations(selectedUseCase);
    }
  }, [selectedUseCase]);
  
  // Load files from the API
  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.getAIFiles();
      setFiles(response.data.data.files);
      logger.log(`Loaded ${response.data.data.files.length} files`);
    } catch (err) {
      logger.logError('Error loading files', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Load configurations for a use case
  const loadConfigurations = async (useCase) => {
    try {
      const response = await api.getAllAIConfigurations(useCase);
      setConfigurations(response.data.data);
      
      // Set the active configuration as selected
      const activeConfig = response.data.data.find(config => config.is_active);
      if (activeConfig) {
        setSelectedConfig(activeConfig);
      } else if (response.data.data.length > 0) {
        setSelectedConfig(response.data.data[0]);
      }
    } catch (err) {
      logger.logError(`Error loading configurations for use case ${useCase}`, err);
    }
  };
  
  // Handle file change
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        setUploadError('Please select a CSV file');
        setCsvFile(null);
        return;
      }
      
      setCsvFile(file);
      setUploadError(null);
    }
  };
  
  // Handle file upload
  const handleFileUpload = async (event) => {
    event.preventDefault();
    
    if (!csvFile) {
      setUploadError('Please select a CSV file');
      return;
    }
    
    if (!selectedConfig) {
      setUploadError('Please select a configuration');
      return;
    }
    
    setIsUploading(true);
    setUploadError(null);
    
    try {
      // Create a FormData object to send the file
      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('use_case', selectedUseCase);
      formData.append('version', selectedConfig.version);
      
      // Upload the file
      const response = await api.uploadAIFile(formData);
      
      // Show success message
      setUploadSuccess(true);
      setCsvFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('csv-file-input');
      if (fileInput) {
        fileInput.value = '';
      }
      
      // Reload files
      loadFiles();
      
      logger.log(`Uploaded file with ID ${response.data.data.file_id}`);
    } catch (err) {
      logger.logError('Error uploading file', err);
      setUploadError('Failed to upload file. Please check your input and try again.');
      setUploadSuccess(false);
    } finally {
      setIsUploading(false);
    }
  };
  
  // Handle file download
  const handleDownload = async (fileId, isOutput = false) => {
    try {
      // Get file details with download URLs
      const response = await api.getAIFile(fileId);
      
      // Get the appropriate download URL
      const downloadUrl = isOutput 
        ? response.data.data.output_download_url
        : response.data.data.input_download_url;
      
      if (!downloadUrl) {
        setError(`No ${isOutput ? 'output' : 'input'} file available for download`);
        return;
      }
      
      // Open the download URL in a new tab
      window.open(downloadUrl, '_blank');
    } catch (err) {
      logger.logError(`Error downloading ${isOutput ? 'output' : 'input'} file`, err);
      setError(`Failed to download ${isOutput ? 'output' : 'input'} file. Please try again.`);
    }
  };
  
  // Handle file processing interruption
  const handleInterrupt = async (fileId) => {
    if (!window.confirm('Are you sure you want to interrupt processing of this file?')) {
      return;
    }
    
    try {
      await api.interruptAIFile(fileId);
      
      // Reload files
      loadFiles();
      
      logger.log(`Interrupted processing of file with ID ${fileId}`);
    } catch (err) {
      logger.logError('Error interrupting file processing', err);
      setError('Failed to interrupt file processing. Please try again.');
    }
  };
  
  // Handle back button click
  const handleBack = () => {
    navigate('/');
  };
  
  // Render the file state badge
  const renderStateBadge = (state) => {
    switch (state) {
      case 'accepted':
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
            Accepted
          </span>
        );
      case 'processing':
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
            Processing
          </span>
        );
      case 'completed':
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
            Completed
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
            Failed
          </span>
        );
      case 'interrupted':
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
            Interrupted
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
            {state}
          </span>
        );
    }
  };
  
  // Render progress information
  const renderProgress = (file) => {
    if (!file.total_records) {
      return null;
    }
    
    const processed = file.processed_records || 0;
    const total = file.total_records;
    const percentage = total > 0 ? Math.round((processed / total) * 100) : 0;
    
    return (
      <div className="mt-1">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{processed} / {total} records ({percentage}%)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
          <div 
            className="bg-blue-600 h-2 rounded-full" 
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };
  
  // Check if a file can be interrupted
  const canInterruptFile = (file) => {
    // Allow interruption for files in 'accepted' or 'processing' state
    return file.state === 'accepted' || file.state === 'processing';
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg
              className="w-5 h-5 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </button>
        </div>
        
        <AINavigation />
        <div className="bg-white shadow rounded-lg p-6 mt-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">AI Files</h1>
          
          {/* Upload Form */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-medium text-gray-900">Upload CSV File</h2>
            <p className="mt-2 text-sm text-gray-600">
              Upload a CSV file with "input" and optional "expected_output" columns. 
              The input column should contain JSON data that will be processed by the AI service.
            </p>
            
            {uploadSuccess && (
              <div className="mt-4 p-4 bg-green-100 text-green-800 rounded-md">
                File uploaded successfully! It will be processed in the background.
              </div>
            )}
            
            {uploadError && (
              <div className="mt-4 p-4 bg-red-100 text-red-800 rounded-md">
                {uploadError}
              </div>
            )}
            
            <form onSubmit={handleFileUpload} className="mt-4">
              {/* Use Case Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Use Case
                </label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={selectedUseCase}
                  onChange={(e) => setSelectedUseCase(e.target.value)}
                  required
                >
                  {useCaseOptions.map(useCase => (
                    <option key={useCase.value} value={useCase.value}>
                      {useCase.label}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Configuration Selection */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">
                  Configuration
                </label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={selectedConfig ? selectedConfig.version : ''}
                  onChange={(e) => {
                    const version = parseInt(e.target.value);
                    const config = configurations.find(c => c.version === version);
                    setSelectedConfig(config);
                  }}
                  required
                >
                  <option value="">Select a configuration</option>
                  {configurations.map(config => (
                    <option key={config.version} value={config.version}>
                      Version {config.version} {config.is_active ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* File Input */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">
                  CSV File
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="csv-file-input"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                      >
                        <span>Upload a file</span>
                        <input
                          id="csv-file-input"
                          name="file"
                          type="file"
                          accept=".csv"
                          className="sr-only"
                          onChange={handleFileChange}
                          required
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">CSV up to 10MB</p>
                  </div>
                </div>
                {csvFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    Selected file: {csvFile.name} ({Math.round(csvFile.size / 1024)} KB)
                  </p>
                )}
              </div>
              
              {/* Submit Button */}
              <div className="mt-6">
                <button
                  type="submit"
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  disabled={isUploading}
                >
                  {isUploading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Uploading...
                    </>
                  ) : (
                    'Upload File'
                  )}
                </button>
              </div>
            </form>
          </div>
          
          {/* Files List */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-medium text-gray-900">Your Files</h2>
            
            {error && (
              <div className="mt-4 p-4 bg-red-100 text-red-800 rounded-md">
                {error}
              </div>
            )}
            
            {loading ? (
              <div className="mt-4 text-gray-500">Loading files...</div>
            ) : files.length === 0 ? (
              <div className="mt-4 text-gray-500">No files found.</div>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        File ID
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        State
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Use Case
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Version
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created At
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {files.map(file => (
                      <tr key={file.file_id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {file.file_id.substring(0, 8)}...
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {renderStateBadge(file.state)}
                          {renderProgress(file)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {file.metadata?.use_case || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {file.metadata?.version || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {file.user_id === user?.id ? user?.name || user?.email : file.user_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(file.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button
                            onClick={() => handleDownload(file.file_id, false)}
                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                          >
                            Download Input
                          </button>
                          {(file.state === 'completed' || file.state === 'interrupted') && file.output_s3_key && (
                            <button
                              onClick={() => handleDownload(file.file_id, true)}
                              className="text-green-600 hover:text-green-900 mr-4"
                            >
                              Download Output
                            </button>
                          )}
                          {canInterruptFile(file) && (
                            <button
                              onClick={() => handleInterrupt(file.file_id)}
                              className="text-orange-600 hover:text-orange-900"
                            >
                              Interrupt
                            </button>
                          )}
                          {file.error_message && (
                            <div className="mt-2 text-xs text-red-600 max-w-xs truncate" title={file.error_message}>
                              Error: {file.error_message}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIFilesPage; 