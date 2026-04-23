import React, { useState, useRef } from 'react';
import axios from 'axios';
import { 
  FileText, UploadCloud, X, Loader2, CheckCircle, Download, FilePenLine
} from 'lucide-react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [instructions, setInstructions] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.docx')) {
      setFile(droppedFile);
      resetState();
    } else {
      setError('Please upload a valid .docx file.');
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.docx')) {
      setFile(selectedFile);
      resetState();
    } else if (selectedFile) {
      setError('Please upload a valid .docx file.');
    }
  };

  const resetState = () => {
    setIsSuccess(false);
    setError('');
    setDownloadUrl('');
  };

  const removeFile = () => {
    setFile(null);
    setInstructions('');
    resetState();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatDocument = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('instructions', instructions);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/format', formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      setDownloadUrl(url);
      setIsSuccess(true);
    } catch (err) {
      console.error(err);
      setError('An error occurred during processing. Ensure the backend is running and you have set GEMINI_API_KEY in the backend .env file.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-panel">
        <div className="header">
          <FilePenLine size={48} className="logo-icon" />
          <h1 className="title">Smart DocFormatter</h1>
          <p className="subtitle">AI-powered professional document standardization</p>
        </div>

        {!file && !isProcessing && !isSuccess && (
          <div 
            className={`upload-area ${isDragging ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud size={48} className="upload-icon" />
            <p className="upload-text">Click or drag your .docx file here</p>
            <p className="upload-hint">Maximum file size: 10MB</p>
            <input 
              type="file" 
              className="file-input" 
              ref={fileInputRef} 
              accept=".docx" 
              onChange={handleFileChange}
            />
          </div>
        )}

        {error && (
          <div style={{ color: '#ef4444', textAlign: 'center', marginBottom: '1rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        {file && !isProcessing && !isSuccess && (
          <>
            <div className="selected-file">
              <div className="file-info">
                <FileText size={24} color="var(--primary)" />
                <div>
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
                </div>
              </div>
              <button className="remove-btn" onClick={removeFile} aria-label="Remove file">
                <X size={20} />
              </button>
            </div>
            
            <div className="instruction-input">
              <label htmlFor="rules">Chatbot formatting rules (Optional)</label>
              <textarea 
                id="rules" 
                placeholder="e.g. set font size to 14 and heading 16, make subheadings bold..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={3}
              ></textarea>
            </div>

            <button className="action-btn" onClick={formatDocument}>
              Format Document
            </button>
          </>
        )}

        {isProcessing && (
          <div className="processing-state">
            <Loader2 size={48} className="spinner" />
            <p className="processing-text">AI is analyzing and formatting...</p>
            <p className="subtitle" style={{fontSize: '0.85rem', textAlign: 'center'}}>
              Parsing layout and applying your rules.
            </p>
          </div>
        )}

        {isSuccess && (
          <div className="success-state">
            <CheckCircle size={56} className="success-icon" />
            <h2 className="success-text">Document Formatted!</h2>
            <p className="success-hint">Your document has been professionally standardized.</p>
            
            <div style={{display: 'flex', gap: '1rem', marginTop: '1.5rem'}}>
              <a 
                href={downloadUrl} 
                download={`formatted_${file.name}`}
                className="action-btn" 
                style={{textDecoration: 'none', flex: 1}}
              >
                <Download size={20} />
                Download
              </a>
              <button 
                className="action-btn" 
                onClick={removeFile}
                style={{background: 'rgba(255,255,255,0.1)', boxShadow: 'none', flex: 1}}
              >
                Process Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
