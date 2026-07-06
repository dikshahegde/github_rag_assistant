import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload,  
  FileText, 
  RefreshCw, 
  Send, 
  Check, 
  Code, 
  AlertCircle, 
  File, 
  MessageSquare, 
  BookOpen,
  Trash2
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ─── File Tree Helpers ───────────────────────────────────────────────────────

function buildTree(paths) {
  const root = {};
  for (const filePath of paths) {
    const parts = filePath.split('/');
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        if (!node.__files__) node.__files__ = [];
        node.__files__.push({ name: part, fullPath: filePath });
      } else {
        if (!node[part]) node[part] = {};
        node = node[part];
      }
    }
  }
  return root;
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const icons = {
    py: '🐍', js: '🟨', ts: '🔷', jsx: '⚛️', tsx: '⚛️',
    md: '📝', java: '☕', json: '📋', yaml: '📋', yml: '📋',
    txt: '📄', csv: '📊', html: '🌐', css: '🎨', gitignore: '🚫',
    env: '⚙️', toml: '⚙️', cfg: '⚙️', ini: '⚙️', pkl: '📦',
    sh: '💻', bat: '💻', ps1: '💻', xml: '📋', sql: '🗄️',
  };
  return icons[ext] || '📄';
}

function FileTreeNode({ name, node, selectedFile, onSelectFile, depth = 0 }) {
  const [isOpen, setIsOpen] = useState(depth < 2);
  const indent = depth * 14;

  const folders = Object.keys(node).filter(k => k !== '__files__').sort();
  const files = (node.__files__ || []).sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div>
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          padding: '4px 6px',
          paddingLeft: `${indent + 6}px`,
          cursor: 'pointer',
          borderRadius: '4px',
          fontSize: '0.82rem',
          color: 'var(--text-muted)',
          userSelect: 'none',
          transition: 'background 0.15s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <span style={{ fontSize: '0.65rem', minWidth: '10px', opacity: 0.7 }}>
          {isOpen ? '▾' : '▸'}
        </span>
        <span>📁</span>
        <span style={{ fontWeight: 600, letterSpacing: '0.01em' }}>{name}</span>
      </div>

      {isOpen && (
        <div>
          {folders.map(folderName => (
            <FileTreeNode
              key={folderName}
              name={folderName}
              node={node[folderName]}
              selectedFile={selectedFile}
              onSelectFile={onSelectFile}
              depth={depth + 1}
            />
          ))}
          {files.map(({ name: fileName, fullPath }) => (
            <div
              key={fullPath}
              onClick={() => onSelectFile(fullPath)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 6px',
                paddingLeft: `${indent + 22}px`,
                cursor: 'pointer',
                borderRadius: '4px',
                fontSize: '0.8rem',
                background: selectedFile === fullPath ? 'var(--accent, #4f8ef7)' : 'transparent',
                color: selectedFile === fullPath ? '#fff' : 'var(--text-secondary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => {
                if (selectedFile !== fullPath)
                  e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
              }}
              onMouseLeave={e => {
                if (selectedFile !== fullPath)
                  e.currentTarget.style.background = 'transparent';
              }}
              title={fullPath}
            >
              <span style={{ flexShrink: 0 }}>{getFileIcon(fileName)}</span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{fileName}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FileTree({ files, selectedFile, onSelectFile }) {
  const tree = buildTree(files);
  const folders = Object.keys(tree).filter(k => k !== '__files__').sort();
  const rootFiles = (tree.__files__ || []).sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div style={{ fontSize: '0.82rem' }}>
      {folders.map(folderName => (
        <FileTreeNode
          key={folderName}
          name={folderName}
          node={tree[folderName]}
          selectedFile={selectedFile}
          onSelectFile={onSelectFile}
          depth={0}
        />
      ))}
      {rootFiles.map(({ name: fileName, fullPath }) => (
        <div
          key={fullPath}
          onClick={() => onSelectFile(fullPath)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 6px',
            paddingLeft: '6px',
            cursor: 'pointer',
            borderRadius: '4px',
            fontSize: '0.8rem',
            background: selectedFile === fullPath ? 'var(--accent, #4f8ef7)' : 'transparent',
            color: selectedFile === fullPath ? '#fff' : 'var(--text-secondary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            transition: 'background 0.15s',
          }}
          onMouseEnter={e => {
            if (selectedFile !== fullPath)
              e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
          }}
          onMouseLeave={e => {
            if (selectedFile !== fullPath)
              e.currentTarget.style.background = 'transparent';
          }}
          title={fullPath}
        >
          <span style={{ flexShrink: 0 }}>{getFileIcon(fileName)}</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{fileName}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────────────────────

function App() {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [repoUrlInput, setRepoUrlInput] = useState('');
  const [forceClone, setForceClone] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);

  const [activeTab, setActiveTab] = useState('summary');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [highlightLines, setHighlightLines] = useState(null);

  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [retrievedChunks, setRetrievedChunks] = useState([]);

  const messagesEndRef = useRef(null);
  const codeLinesRef = useRef([]);

  useEffect(() => {
    fetchHealth();
    fetchRepositories();
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  useEffect(() => {
    if (highlightLines && codeLinesRef.current[highlightLines.start]) {
      setTimeout(() => {
        codeLinesRef.current[highlightLines.start].scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }, 100);
    }
  }, [highlightLines, fileContent]);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`);
      const data = await res.json();
      if (data.status === 'healthy') {
        setIsBackendHealthy(true);
        if (!data.gemini_key_configured) {
          setUploadError('Warning: GEMINI_API_KEY is not configured in the .env file. API queries will fail.');
        }
      }
    } catch (e) {
      setIsBackendHealthy(false);
      setUploadError('Could not connect to FastAPI backend. Please ensure uvicorn is running on port 8000.');
    }
  };

  const fetchRepositories = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/upload`);
      if (res.ok) {
        const data = await res.json();
        setRepositories(data);
        if (data.length > 0 && !selectedRepo) {
          handleSelectRepo(data[0]);
        }
      }
    } catch (e) {
      console.error('Error fetching repositories:', e);
    }
  };

  const handleSelectRepo = async (repo) => {
    setSelectedRepo(repo);
    setSelectedFile(null);
    setFileContent('');
    setHighlightLines(null);
    setActiveTab('summary');

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/${repo.repo_name}/history`);
      if (res.ok) {
        const history = await res.json();
        if (history.length > 0) {
          setChatMessages(history);
        } else {
          setChatMessages([{
            sender: 'assistant',
            text: `I have loaded the repository **${repo.repo_name}**. Ask me anything about this codebase!`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }]);
        }
      }
    } catch (e) {
      setChatMessages([{
        sender: 'assistant',
        text: `I have loaded the repository **${repo.repo_name}**. Ask me anything about this codebase!`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  };

  // ─── Clear chat history for a repo ───────────────────────────────────────
  const handleClearChat = async () => {
    if (!selectedRepo) return;
    const fresh = [{
      sender: 'assistant',
      text: `Chat cleared. Ask me anything about **${selectedRepo.repo_name}**!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }];
    setChatMessages(fresh);
    try {
      await fetch(`${API_BASE_URL}/api/chat/${selectedRepo.repo_name}/history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fresh)
      });
    } catch (e) {
      console.error('Failed to clear chat history:', e);
    }
  };

  // ─── Delete a repo from active repositories ───────────────────────────────
  const handleDeleteRepo = async (repoName, e) => {
    e.stopPropagation(); // don't trigger handleSelectRepo
    if (!window.confirm(`Remove "${repoName}" from active repositories?`)) return;
    try {
      await fetch(`${API_BASE_URL}/api/upload/${repoName}`, { method: 'DELETE' });
    } catch (err) {
      // even if backend delete fails, remove from UI
    }
    setRepositories(prev => prev.filter(r => r.repo_name !== repoName));
    if (selectedRepo?.repo_name === repoName) {
      setSelectedRepo(null);
      setChatMessages([]);
      setSelectedFile(null);
      setFileContent('');
    }
  };

  const handleUploadRepo = async (e) => {
    e.preventDefault();
    if (!repoUrlInput.trim()) return;

    setIsUploading(true);
    setUploadError('');
    setUploadSuccess('');

    try {
      const res = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: repoUrlInput.trim(),
          force_clone: forceClone
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Ingestion failed');
      }

      const data = await res.json();
      setUploadSuccess(`Indexed repository successfully!`);

      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });

      await fetchRepositories();
      handleSelectRepo(data);
      setRepoUrlInput('');
    } catch (err) {
      setUploadError(err.message || 'Failed to process repository.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectFile = async (filePath) => {
    if (!selectedRepo) return;
    setSelectedFile(filePath);
    setIsLoadingFile(true);
    setHighlightLines(null);
    setActiveTab('fileviewer');

    try {
      const encodedPath = encodeURIComponent(filePath);
      const res = await fetch(`${API_BASE_URL}/api/upload/${selectedRepo.repo_name}/files/${encodedPath}`);
      if (res.ok) {
        const data = await res.json();
        setFileContent(data.content);
      } else {
        setFileContent('Error loading file content.');
      }
    } catch (err) {
      setFileContent('Error connecting to backend to fetch file.');
    } finally {
      setIsLoadingFile(false);
    }
  };

  const handleCitationClick = async (filePath, startLine, endLine) => {
    if (!selectedRepo) return;
    setSelectedFile(filePath);
    setIsLoadingFile(true);
    setHighlightLines({ start: startLine, end: endLine });
    setActiveTab('fileviewer');

    try {
      const encodedPath = encodeURIComponent(filePath);
      const res = await fetch(`${API_BASE_URL}/api/upload/${selectedRepo.repo_name}/files/${encodedPath}`);
      if (res.ok) {
        const data = await res.json();
        setFileContent(data.content);
      } else {
        setFileContent('Error loading file content.');
      }
    } catch (err) {
      setFileContent('Error connecting to backend to fetch file.');
    } finally {
      setIsLoadingFile(false);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!currentQuery.trim() || !selectedRepo || isGenerating) return;

    const userMessage = {
      sender: 'user',
      text: currentQuery,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatMessages(prev => [...prev, userMessage]);
    const queryToSend = currentQuery;
    setCurrentQuery('');
    setIsGenerating(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_name: selectedRepo.repo_name,
          query: queryToSend,
          top_k: 5
        })
      });

      if (!res.ok) throw new Error('Failed to query assistant');

      const data = await res.json();

      const assistantMessage = {
        sender: 'assistant',
        text: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: data.citations
      };

      const updatedMessages = [...chatMessages, userMessage, assistantMessage];
      setChatMessages(updatedMessages);
      setRetrievedChunks(data.retrieved_chunks);

      try {
        await fetch(`${API_BASE_URL}/api/chat/${selectedRepo.repo_name}/history`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedMessages)
        });
      } catch (e) {
        console.error('Failed to save chat history:', e);
      }

    } catch (err) {
      setChatMessages(prev => [...prev, {
        sender: 'assistant',
        text: 'Error generating response. Please check your Gemini API key and try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsGenerating(false);
    }
  };

  const parseMarkdownAndCitations = (text, citations = []) => {
    if (!text) return '';

    const blocks = [];
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        blocks.push({ type: 'text', content: text.substring(lastIndex, match.index) });
      }
      blocks.push({ type: 'code', lang: match[1], content: match[2] });
      lastIndex = codeBlockRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      blocks.push({ type: 'text', content: text.substring(lastIndex) });
    }

    return blocks.map((block, idx) => {
      if (block.type === 'code') {
        return (
          <pre key={idx} style={{ position: 'relative' }}>
            <span className="code-lang-label">{block.lang || 'code'}</span>
            <code>{block.content}</code>
          </pre>
        );
      }

      const lines = block.content.split('\n');
      return lines.map((line, lineIdx) => {
        if (line.startsWith('# ')) {
          return <h2 key={`${idx}-${lineIdx}`}>{line.substring(2)}</h2>;
        } else if (line.startsWith('## ')) {
          return <h3 key={`${idx}-${lineIdx}`}>{line.substring(3)}</h3>;
        } else if (line.startsWith('### ')) {
          return <h4 key={`${idx}-${lineIdx}`}>{line.substring(4)}</h4>;
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={`${idx}-${lineIdx}`}>{renderInlineFormatting(line.substring(2))}</li>;
        } else if (line.trim() === '') {
          return <br key={`${idx}-${lineIdx}`} />;
        }
        return <p key={`${idx}-${lineIdx}`}>{renderInlineFormatting(line)}</p>;
      });
    });
  };

  const renderInlineFormatting = (text) => {
    const tokenRegex = /(\*\*.*?\*\*|`.*?`|\[[^:\s]+:\d+-\d+\])/g;
    const parts = text.split(tokenRegex);

    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i}>{part.slice(1, -1)}</code>;
      }
      const citationMatch = part.match(/^\[([^:\s]+):(\d+)-(\d+)\]$/);
      if (citationMatch) {
        const filePath = citationMatch[1];
        const startLine = parseInt(citationMatch[2], 10);
        const endLine = parseInt(citationMatch[3], 10);
        const displayFile = filePath.split('/').pop();
        return (
          <button
            key={i}
            className="citation-badge"
            onClick={() => handleCitationClick(filePath, startLine, endLine)}
            title={`View ${filePath} lines ${startLine}-${endLine}`}
          >
            📄 {displayFile} L{startLine}-{endLine}
          </button>
        );
      }
      return part;
    });
  };

  // ─── Shared clear button style ────────────────────────────────────────────
  const clearBtnStyle = {
    background: 'transparent',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '6px',
    padding: '4px 8px',
    cursor: 'pointer',
    color: 'var(--text-muted)',
    fontSize: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'all 0.15s',
  };

  return (
    <div className="app-container">

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="brand">
          <Code size={24} />
          <span>RAG Code Assistant</span>
        </div>

        {/* Upload Form */}
        <form className="form-group" onSubmit={handleUploadRepo}>
          <label className="section-title">
            <Upload size={14} /> Import Repository
          </label>
          <div className="input-container">
            <Code className="input-icon" />
            <input
              type="text"
              className="text-input"
              placeholder="https://github.com/username/repo"
              value={repoUrlInput}
              onChange={(e) => setRepoUrlInput(e.target.value)}
              disabled={isUploading}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
            <input
              type="checkbox"
              id="forceClone"
              checked={forceClone}
              onChange={(e) => setForceClone(e.target.checked)}
            />
            <label htmlFor="forceClone" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Overwrite existing database index
            </label>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isUploading || !repoUrlInput.trim()}
          >
            {isUploading ? (
              <><RefreshCw size={16} className="spinner" /> Indexing Repository...</>
            ) : (
              'Ingest Codebase'
            )}
          </button>
        </form>

        {/* Alerts */}
        {uploadError && (
          <div className="status-badge error">
            <AlertCircle size={16} />
            <span>{uploadError}</span>
          </div>
        )}
        {uploadSuccess && (
          <div className="status-badge success">
            <Check size={16} />
            <span>{uploadSuccess}</span>
          </div>
        )}

        {/* Active Repositories */}
        <div className="form-group" style={{ marginTop: '10px' }}>
          <label className="section-title">
            <BookOpen size={14} /> Active Repositories
          </label>
          {repositories.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No repositories indexed yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '150px', overflowY: 'auto' }}>
              {repositories.map(repo => (
                <div
                  key={repo.repo_name}
                  className={`repo-card ${selectedRepo?.repo_name === repo.repo_name ? 'active' : ''}`}
                  onClick={() => handleSelectRepo(repo)}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  <div className="repo-title" style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1, minWidth: 0 }}>
                    <Code size={16} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {repo.repo_name}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                    <span className="repo-badge">
                      {(repo.files || repo.parsed_files || []).length} files
                    </span>
                    {/* ── Clear repo button ── */}
                    <button
                      title="Remove repository"
                      onClick={(e) => handleDeleteRepo(repo.repo_name, e)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'rgba(255,100,100,0.6)',
                        padding: '2px 4px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,80,80,1)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,100,100,0.6)'}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Explorer */}
        {selectedRepo && (
          <div className="form-group">
            <label className="section-title">
              <FileText size={14} /> Explorer
              <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 400, opacity: 0.6 }}>
                {(selectedRepo.files || selectedRepo.parsed_files || []).length} files
              </span>
            </label>
            <div
              className="file-tree-scroll"
              style={{ overflowY: 'auto', overflowX: 'hidden', paddingRight: '2px' }}
            >
              <FileTree
                files={selectedRepo.files || selectedRepo.parsed_files || []}
                selectedFile={selectedFile}
                onSelectFile={handleSelectFile}
              />
            </div>
          </div>
        )}
      </aside>

      {/* ── Main Panel ── */}
      <main className="workspace">
        {!selectedRepo ? (
          <div className="home-placeholder">
            <Code className="placeholder-icon" />
            <h1 className="placeholder-title">RAG Code Repository Assistant</h1>
            <p className="placeholder-text">
              Analyze structure, review configurations, and understand full repositories without manual searches.
              Paste a repository URL in the sidebar to begin.
            </p>
          </div>
        ) : (
          <>
            <header className="tab-header">
              <button
                className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
                onClick={() => setActiveTab('summary')}
              >
                <BookOpen size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                Repo Summary
              </button>
              <button
                className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
              >
                <MessageSquare size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                RAG Chat
              </button>
              <button
                className={`tab-btn ${activeTab === 'fileviewer' ? 'active' : ''}`}
                onClick={() => setActiveTab('fileviewer')}
                disabled={!selectedFile}
              >
                <Code size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                File Viewer {selectedFile && `(${selectedFile.split('/').pop()})`}
              </button>
            </header>

            <div className="panel-content">

              {/* Tab 1: Summary */}
              <div className={`tab-panel ${activeTab === 'summary' ? 'active' : ''}`}>
                <div className="summary-container">
                  <div className="summary-card markdown-body">
                    {parseMarkdownAndCitations(selectedRepo.summary)}
                  </div>
                </div>
              </div>

              {/* Tab 2: RAG Chat */}
              <div className={`tab-panel ${activeTab === 'chat' ? 'active' : ''}`}>
                <div className="chat-container">

                  {/* Chat header with clear button */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 16px',
                    borderBottom: '1px solid var(--border-color)',
                    flexShrink: 0,
                  }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      💬 Chat with <strong style={{ color: 'var(--text-main)' }}>{selectedRepo.repo_name}</strong>
                    </span>
                    {/* ── Clear chat button ── */}
                    <button
                      style={clearBtnStyle}
                      onClick={handleClearChat}
                      title="Clear chat history"
                      onMouseEnter={e => {
                        e.currentTarget.style.borderColor = 'rgba(255,100,100,0.5)';
                        e.currentTarget.style.color = 'rgba(255,100,100,0.9)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
                        e.currentTarget.style.color = 'var(--text-muted)';
                      }}
                    >
                      <Trash2 size={12} /> Clear chat
                    </button>
                  </div>

                  <div className="messages-list">
                    {chatMessages.map((msg, index) => (
                      <div key={index} className={`message-wrapper ${msg.sender}`}>
                        <div className="message-bubble markdown-body">
                          {msg.sender === 'assistant'
                            ? parseMarkdownAndCitations(msg.text, msg.citations)
                            : msg.text}
                        </div>
                        <div className="message-meta">
                          {msg.sender === 'user' ? 'You' : 'Assistant'} • {msg.timestamp}
                        </div>
                      </div>
                    ))}

                    {isGenerating && (
                      <div className="message-wrapper assistant">
                        <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <RefreshCw size={16} className="spinner" />
                          Thinking... Scanning vector store and generating response...
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  <form className="chat-input-area" onSubmit={handleSendChat}>
                    <input
                      type="text"
                      className="chat-textarea"
                      placeholder={`Ask me anything about ${selectedRepo.repo_name}...`}
                      value={currentQuery}
                      onChange={(e) => setCurrentQuery(e.target.value)}
                      disabled={isGenerating}
                    />
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={isGenerating || !currentQuery.trim()}
                    >
                      <Send size={18} />
                    </button>
                  </form>
                </div>
              </div>

              {/* Tab 3: File Viewer */}
              <div className={`tab-panel ${activeTab === 'fileviewer' ? 'active' : ''}`}>
                {selectedFile ? (
                  <div className="file-viewer-container">
                    <div className="file-viewer-header">
                      <div className="file-info">
                        <File size={16} />
                        <span>{selectedFile}</span>
                      </div>
                      {highlightLines && (
                        <div className="status-badge success" style={{ padding: '4px 10px', fontSize: '0.8rem', margin: 0 }}>
                          Showing lines {highlightLines.start} to {highlightLines.end}
                        </div>
                      )}
                    </div>
                    {isLoadingFile ? (
                      <div className="loading-overlay">
                        <div className="spinner"></div>
                        <p>Loading file content...</p>
                      </div>
                    ) : (
                      <div className="code-container">
                        <div className="line-numbers">
                          {fileContent.split('\n').map((_, idx) => (
                            <div key={idx + 1}>{idx + 1}</div>
                          ))}
                        </div>
                        <pre className="code-lines">
                          {fileContent.split('\n').map((line, idx) => {
                            const lineNum = idx + 1;
                            const isHighlighted = highlightLines &&
                              lineNum >= highlightLines.start &&
                              lineNum <= highlightLines.end;
                            return (
                              <span
                                key={lineNum}
                                ref={el => codeLinesRef.current[lineNum] = el}
                                className={`code-line ${isHighlighted ? 'highlighted' : ''}`}
                              >
                                {line || ' '}
                              </span>
                            );
                          })}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="home-placeholder">
                    <FileText size={64} className="placeholder-icon" />
                    <h2 className="placeholder-title">No file open</h2>
                    <p className="placeholder-text">
                      Select a file from the sidebar explorer or click a citation link inside RAG Chat to inspect code context.
                    </p>
                  </div>
                )}
              </div>

            </div>
          </>
        )}
      </main>
    </div>
  );
}

const var_ref = typeof window !== 'undefined' ? window : {};

export default App;