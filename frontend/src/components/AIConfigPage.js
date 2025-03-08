import React, { useState, useEffect } from 'react';
import { useApiService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { createLogger } from '../utils/logging';

// Create a logger for the AIConfigPage component
const logger = createLogger('AIConfigPage');

const AIConfigPage = () => {
  const api = useApiService();
  const navigate = useNavigate();
  
  // State for AI configurations
  const [selectedUseCase, setSelectedUseCase] = useState('project_summary');
  const [configurations, setConfigurations] = useState([]);
  const [activeConfig, setActiveConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for available parameters
  const [availableParameters, setAvailableParameters] = useState([]);
  
  // State for response format
  const [responseFormat, setResponseFormat] = useState('');
  
  // State for form
  const [formData, setFormData] = useState({
    use_case: 'project_summary',
    model: 'gpt-3.5-turbo',
    system_prompt: '',
    user_prompt_template: '',
    max_tokens: 500,
    temperature: 0.7,
    description: ''
  });
  
  // State for UI
  const [isEditing, setIsEditing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [viewingConfigVersion, setViewingConfigVersion] = useState(null);
  
  // Add state to track if we're cloning a configuration
  const [cloningConfig, setCloningConfig] = useState(null);
  
  // Use case options
  const useCaseOptions = [
    { value: 'project_summary', label: 'Project Summary' },
    { value: 'relevance_extraction', label: 'Relevance Extraction' }
  ];
  
  // Model options
  const modelOptions = [
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' }
  ];
  
  // Load configurations for the selected use case
  const loadConfigurations = async () => {
    logger.log(`Loading configurations for use case: ${selectedUseCase}`);
    setLoading(true);
    setError(null);
    
    // Track which operations succeeded
    const operationStatus = {
      getAllConfigurations: false,
      getActiveConfiguration: false,
      getParameters: false,
      getResponseFormat: false
    };
    
    try {
      // Get all configurations
      try {
        logger.log(`Fetching all configurations for use case: ${selectedUseCase}`);
        const response = await api.getAllAIConfigurations(selectedUseCase);
        setConfigurations(response.data.data);
        logger.log(`Successfully loaded ${response.data.data.length} configurations for use case: ${selectedUseCase}`);
        operationStatus.getAllConfigurations = true;
      } catch (err) {
        logger.logError(`Error loading all configurations for use case: ${selectedUseCase}`, err);
        setError('Failed to load configurations. Please try again.');
      }
      
      // Get active configuration
      try {
        logger.log(`Fetching active configuration for use case: ${selectedUseCase}`);
        const activeResponse = await api.getActiveAIConfiguration(selectedUseCase);
        setActiveConfig(activeResponse.data.data);
        logger.log(`Successfully loaded active configuration for use case: ${selectedUseCase}`);
        operationStatus.getActiveConfiguration = true;
      } catch (err) {
        logger.logError(`Error loading active configuration for use case: ${selectedUseCase}`, err);
        if (!operationStatus.getAllConfigurations) {
          setError('Failed to load configurations. Please try again.');
        }
      }
      
      // Get available parameters
      try {
        logger.log(`Fetching parameters for use case: ${selectedUseCase}`);
        const parametersResponse = await api.getAIConfigurationParameters(selectedUseCase);
        setAvailableParameters(parametersResponse.data.data);
        logger.log(`Successfully loaded ${parametersResponse.data.data.length} parameters for use case: ${selectedUseCase}`);
        operationStatus.getParameters = true;
      } catch (err) {
        logger.logError(`Error loading parameters for use case: ${selectedUseCase}`, err);
        if (!operationStatus.getAllConfigurations && !operationStatus.getActiveConfiguration) {
          setError('Failed to load configurations. Please try again.');
        }
      }
      
      // Get response format
      try {
        logger.log(`Fetching response format for use case: ${selectedUseCase}`);
        const responseFormatResponse = await api.getAIConfigurationResponseFormat(selectedUseCase);
        setResponseFormat(responseFormatResponse.data.data);
        logger.log(`Successfully loaded response format for use case: ${selectedUseCase}`);
        operationStatus.getResponseFormat = true;
      } catch (err) {
        logger.logError(`Error loading response format for use case: ${selectedUseCase}`, err);
        if (!operationStatus.getAllConfigurations && !operationStatus.getActiveConfiguration && !operationStatus.getParameters) {
          setError('Failed to load configurations. Please try again.');
        }
      }
      
      // Set overall error message if all operations failed
      if (!operationStatus.getAllConfigurations && !operationStatus.getActiveConfiguration && !operationStatus.getParameters && !operationStatus.getResponseFormat) {
        logger.logError(`All operations failed for use case: ${selectedUseCase}`, null);
        setError('Failed to load any configuration data. Please try again or contact support.');
      }
    } catch (err) {
      logger.logError(`Unexpected error loading configurations for use case: ${selectedUseCase}`, err);
      setError('An unexpected error occurred. Please try again or contact support.');
    } finally {
      setLoading(false);
      logger.log(`Finished loading configurations for use case: ${selectedUseCase}`);
    }
  };
  
  // Load configurations when the selected use case changes
  useEffect(() => {
    // Clear and close the form when use case changes
    setShowForm(false);
    setCloningConfig(null);
    setFormData({
      use_case: selectedUseCase,
      model: 'gpt-3.5-turbo',
      system_prompt: '',
      user_prompt_template: '',
      max_tokens: 500,
      temperature: 0.7,
      description: ''
    });
    setViewingConfigVersion(null);
    
    // Load configurations for the new use case
    loadConfigurations();
  }, [selectedUseCase]);
  
  // Set form data when cloning a configuration
  useEffect(() => {
    if (cloningConfig) {
      const configToClone = configurations.find(c => c.version === cloningConfig);
      if (configToClone) {
        setFormData({
          use_case: configToClone.use_case,
          model: configToClone.model,
          system_prompt: configToClone.system_prompt,
          user_prompt_template: configToClone.user_prompt_template,
          max_tokens: configToClone.max_tokens,
          temperature: configToClone.temperature,
          description: `Clone of version ${configToClone.version}: ${configToClone.description || ''}`
        });
        setShowForm(true);
      }
    }
  }, [cloningConfig, configurations]);
  
  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // If changing the use case, fetch the available parameters for the new use case
    if (name === 'use_case' && value !== formData.use_case) {
      logger.log(`Changing use case from ${formData.use_case} to ${value}`);
      api.getAIConfigurationParameters(value)
        .then(response => {
          setAvailableParameters(response.data.data);
          logger.log(`Loaded ${response.data.data.length} parameters for use case: ${value}`);
        })
        .catch(err => {
          logger.logError('Error loading parameters', err);
        });
        
      // Also fetch the response format for the new use case
      api.getAIConfigurationResponseFormat(value)
        .then(response => {
          setResponseFormat(response.data.data);
          logger.log(`Loaded response format for use case: ${value}`);
        })
        .catch(err => {
          logger.logError('Error loading response format', err);
        });
    }
    
    setFormData({
      ...formData,
      [name]: name === 'max_tokens' || name === 'temperature' 
        ? parseFloat(value) 
        : value
    });
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    logger.log(`Submitting form for use case: ${formData.use_case}`);
    
    // Validate description field
    if (!formData.description.trim()) {
      logger.log(`Form validation failed: Description is required`);
      setError('Description is required. Please provide a meaningful description for this configuration.');
      return;
    }
    
    // Validate user prompt template
    if (!formData.user_prompt_template.trim()) {
      logger.log(`Form validation failed: User prompt template is required`);
      setError('User prompt template is required.');
      return;
    }
    
    // Validate system prompt
    if (!formData.system_prompt.trim()) {
      logger.log(`Form validation failed: System prompt is required`);
      setError('System prompt is required.');
      return;
    }
    
    logger.log(`Form validation passed, creating configuration for use case: ${formData.use_case}`, {
      use_case: formData.use_case,
      model: formData.model,
      max_tokens: formData.max_tokens,
      temperature: formData.temperature,
      description: formData.description,
      system_prompt_length: formData.system_prompt.length,
      user_prompt_template_length: formData.user_prompt_template.length
    });
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.createAIConfiguration(formData);
      logger.log(`Successfully created configuration for use case: ${formData.use_case}, version: ${response.data.data.version}`);
      
      setShowForm(false);
      setCloningConfig(null);
      setFormData({
        use_case: selectedUseCase,
        model: 'gpt-3.5-turbo',
        system_prompt: '',
        user_prompt_template: '',
        max_tokens: 500,
        temperature: 0.7,
        description: ''
      });
      
      logger.log(`Reloading configurations after successful creation`);
      loadConfigurations();
    } catch (err) {
      logger.logError(`Error creating configuration for use case: ${formData.use_case}`, err);
      
      // Extract error message from response if available
      let errorMessage = 'Failed to create configuration. Please try again.';
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
        logger.logError(`Server error details: ${errorMessage}`, err);
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
      logger.log(`Form submission completed for use case: ${formData.use_case}`);
    }
  };
  
  // Set a configuration as active
  const handleSetActive = async (version) => {
    logger.log(`Setting configuration as active for use case: ${selectedUseCase}, version: ${version}`);
    setLoading(true);
    setError(null);
    
    try {
      await api.setActiveAIConfiguration(selectedUseCase, version);
      logger.log(`Successfully set configuration as active for use case: ${selectedUseCase}, version: ${version}`);
      loadConfigurations();
    } catch (err) {
      logger.logError('Error setting active configuration', err);
      setError('Failed to set active configuration. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Delete a configuration
  const handleDelete = async (version) => {
    if (!window.confirm('Are you sure you want to delete this configuration?')) {
      return;
    }
    
    logger.log(`Deleting configuration for use case: ${selectedUseCase}, version: ${version}`);
    setLoading(true);
    setError(null);
    
    try {
      await api.deleteAIConfiguration(selectedUseCase, version);
      logger.log(`Successfully deleted configuration for use case: ${selectedUseCase}, version: ${version}`);
      loadConfigurations();
    } catch (err) {
      logger.logError('Error deleting configuration', err);
      setError('Failed to delete configuration. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      <div className="w-64 bg-white border-r border-gray-200 h-full">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold">Hobbes App</h1>
          <p className="text-sm text-gray-500">AI Configuration</p>
        </div>
        <div className="p-4">
          <button
            onClick={() => navigate('/')}
            className="w-full text-left px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-50 rounded"
          >
            Back to App
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-8">
        <h1 className="text-3xl font-bold mb-6">AI Configuration Management</h1>
        
        {/* Use Case Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Use Case
          </label>
          <select
            className="w-full md:w-1/3 p-2 border border-gray-300 rounded-md"
            value={selectedUseCase}
            onChange={(e) => {
              const newUseCase = e.target.value;
              // If form is open, confirm before changing
              if (showForm && newUseCase !== selectedUseCase) {
                if (window.confirm('Changing the use case will clear the current form. Continue?')) {
                  setSelectedUseCase(newUseCase);
                }
              } else {
                setSelectedUseCase(newUseCase);
              }
            }}
          >
            {useCaseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {/* Actions */}
        <div className="flex mb-6 gap-4">
          <button
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            onClick={() => {
              setCloningConfig(null);
              setShowForm(true);
              setFormData({
                use_case: selectedUseCase,
                model: 'gpt-3.5-turbo',
                system_prompt: '',
                user_prompt_template: '',
                max_tokens: 500,
                temperature: 0.7,
                description: ''
              });
            }}
          >
            Create New Configuration
          </button>
        </div>
        
        {/* Configuration Form */}
        {showForm && (
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h2 className="text-xl font-semibold mb-4">
              {cloningConfig ? `Clone Configuration (Version ${cloningConfig})` : 'Create New Configuration'}
            </h2>
            
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="model"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={formData.model}
                    onChange={handleInputChange}
                    required
                  >
                    {modelOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="description"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={formData.description}
                    onChange={handleInputChange}
                    placeholder="Configuration description"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Tokens <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="max_tokens"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={formData.max_tokens}
                    onChange={handleInputChange}
                    min="1"
                    max="4000"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="temperature"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={formData.temperature}
                    onChange={handleInputChange}
                    min="0"
                    max="2"
                    step="0.1"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  System Prompt <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="system_prompt"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={formData.system_prompt}
                  onChange={handleInputChange}
                  rows="4"
                  placeholder="System prompt that defines the AI assistant's role and behavior"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User Prompt Template <span className="text-red-500">*</span>
                </label>
                <div className="mb-2 text-sm text-gray-600 p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <p className="font-medium text-yellow-800">Template Instructions:</p>
                  
                  <div className="mt-2">
                    <p className="font-medium text-yellow-800">Available Parameters:</p>
                    <ul className="list-disc list-inside ml-2 text-yellow-800">
                      {availableParameters.map((param) => (
                        <li key={param.name}><code>{`{${param.name}}`}</code> - {param.description}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="mt-2">
                    <p className="font-medium text-yellow-800">Usage:</p>
                    <p className="text-yellow-800">Insert parameters using single curly braces, e.g., <code>{'{project_name}'}</code></p>
                  </div>
                  
                  <div className="mt-3">
                    <p className="font-medium text-yellow-800">Response Format:</p>
                    <p className="text-yellow-800">Do not include output format instructions in your template. The system will automatically append the following response format:</p>
                    <pre className="mt-2 p-2 bg-yellow-100 rounded text-xs overflow-auto whitespace-pre-wrap text-yellow-800">
                      {responseFormat || 'Loading response format...'}
                    </pre>
                  </div>
                </div>
                <textarea
                  name="user_prompt_template"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={formData.user_prompt_template}
                  onChange={handleInputChange}
                  rows="6"
                  placeholder="Template for the user prompt with variables to be filled"
                  required
                />
              </div>
              
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  className="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                  onClick={() => {
                    setShowForm(false);
                    setCloningConfig(null);
                    setFormData({
                      use_case: selectedUseCase,
                      model: 'gpt-3.5-turbo',
                      system_prompt: '',
                      user_prompt_template: '',
                      max_tokens: 500,
                      temperature: 0.7,
                      description: ''
                    });
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </form>
          </div>
        )}
        
        {/* Configurations List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <h2 className="text-xl font-semibold p-4 bg-gray-50 border-b">
            {selectedUseCase === 'project_summary' ? 'Project Summary' : 'Relevance Extraction'} Configurations
          </h2>
          
          {loading && !configurations.length ? (
            <div className="p-6 text-center text-gray-500">Loading configurations...</div>
          ) : configurations.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No configurations found for this use case.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Version
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created At
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {configurations.map((config) => (
                    <tr key={config.version} className={config.is_active ? 'bg-blue-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {config.version}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {config.model}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {config.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(config.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {config.is_active ? (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            className="text-blue-600 hover:text-blue-900"
                            onClick={() => {
                              setViewingConfigVersion(config.version);
                            }}
                          >
                            View
                          </button>
                          
                          <button
                            className="text-purple-600 hover:text-purple-900"
                            onClick={() => {
                              setCloningConfig(config.version);
                            }}
                          >
                            Clone
                          </button>
                          
                          {!config.is_active && (
                            <>
                              <button
                                className="text-green-600 hover:text-green-900"
                                onClick={() => handleSetActive(config.version)}
                              >
                                Set Active
                              </button>
                              
                              <button
                                className="text-red-600 hover:text-red-900"
                                onClick={() => handleDelete(config.version)}
                              >
                                Delete
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* Configuration Details (Hidden by default) */}
              {viewingConfigVersion && (
                <div
                  className="p-4 bg-gray-50 border-t"
                >
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium">Configuration Details</h3>
                    <button
                      className="text-gray-500 hover:text-gray-700"
                      onClick={() => setViewingConfigVersion(null)}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Model</h4>
                      <p className="text-sm text-gray-900">{configurations.find(c => c.version === viewingConfigVersion)?.model}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Max Tokens</h4>
                      <p className="text-sm text-gray-900">{configurations.find(c => c.version === viewingConfigVersion)?.max_tokens}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Temperature</h4>
                      <p className="text-sm text-gray-900">{configurations.find(c => c.version === viewingConfigVersion)?.temperature}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Created At</h4>
                      <p className="text-sm text-gray-900">{new Date(configurations.find(c => c.version === viewingConfigVersion)?.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700">System Prompt</h4>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-sm overflow-auto whitespace-pre-wrap">
                      {configurations.find(c => c.version === viewingConfigVersion)?.system_prompt}
                    </pre>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">User Prompt Template</h4>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-sm overflow-auto whitespace-pre-wrap">
                      {configurations.find(c => c.version === viewingConfigVersion)?.user_prompt_template}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIConfigPage; 