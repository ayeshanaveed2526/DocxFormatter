import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
  FileText, UploadCloud, X, Loader2, CheckCircle,
  Download, FilePenLine, Type, AlignLeft, Layout,
  BookOpen, Hash, ChevronRight
} from 'lucide-react';
import './App.css';

const DEFAULT_RULES = {
  heading:     { size: 16, bold: true },
  subheading:  { size: 14, bold: true },
  paragraph:   { size: 12, bold: false },
  mcq:         { size: 12, bold: false },
  option:      { size: 11, bold: false },
  margins:     { top: 2.54, bottom: 2.54, left: 2.54, right: 2.54 },
  orientation: 'portrait',
  headerText:  '',
  footerText:  '',
  pageNumbers: 'none',
};

const STEPS = ['upload', 'typography', 'layout', 'header-footer', 'review'];
const STEP_LABELS = ['Upload', 'Typography', 'Layout', 'Header & Footer', 'Review'];
const STEP_ICONS  = [UploadCloud, Type, Layout, BookOpen, CheckCircle];

/* ── Reusable inputs ─────────────────────────────────────── */
function NumberStepper({ label, value, onChange, min = 6, max = 72 }) {
  return (
    <div className="stepper-field">
      <span className="stepper-label">{label}</span>
      <div className="stepper-controls">
        <button onClick={() => onChange(Math.max(min, value - 1))}>−</button>
        <span className="stepper-value">{value}<small>pt</small></span>
        <button onClick={() => onChange(Math.min(max, value + 1))}>+</button>
      </div>
    </div>
  );
}

function ToggleSwitch({ label, checked, onChange }) {
  return (
    <label className="toggle-row">
      <span className="toggle-row-label">{label}</span>
      <div className={`pill-toggle ${checked ? 'on' : ''}`} onClick={() => onChange(!checked)}>
        <div className="pill-thumb" />
      </div>
    </label>
  );
}

function TextInput({ label, placeholder, value, onChange }) {
  return (
    <div className="text-field">
      <label>{label}</label>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}

/* ── Step indicator ──────────────────────────────────────── */
function StepBar({ step }) {
  const idx = STEPS.indexOf(step);
  return (
    <div className="step-bar">
      {STEP_LABELS.map((label, i) => {
        const Icon = STEP_ICONS[i];
        const state = i < idx ? 'done' : i === idx ? 'active' : 'idle';
        return (
          <React.Fragment key={label}>
            <div className={`step-dot ${state}`}>
              <Icon size={13} />
            </div>
            {i < STEP_LABELS.length - 1 && <div className={`step-line ${i < idx ? 'done' : ''}`} />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ── Typography card ─────────────────────────────────────── */
function TypographyCard({ badge, badgeClass, typeKey, rules, updateTypography }) {
  return (
    <div className="type-card">
      <div className={`type-badge ${badgeClass}`}>{badge}</div>
      <NumberStepper
        label="Font Size"
        value={rules[typeKey].size}
        onChange={v => updateTypography(typeKey, 'size', v)}
      />
      <ToggleSwitch
        label="Bold"
        checked={rules[typeKey].bold}
        onChange={v => updateTypography(typeKey, 'bold', v)}
      />
    </div>
  );
}

/* ═══════════════════ Main App ═══════════════════════════ */
export default function App() {
  const [file, setFile]   = useState(null);
  const [rules, setRules] = useState(DEFAULT_RULES);
  const [step, setStep]   = useState('upload');
  const [isDrag, setDrag] = useState(false);
  const [loading, setLd]  = useState(false);
  const [dlUrl,   setDl]  = useState('');
  const [error,   setErr] = useState('');
  const fileRef           = useRef(null);

  const updateTypography = (type, field, val) =>
    setRules(r => ({ ...r, [type]: { ...r[type], [field]: val } }));
  const updateMargin = (side, val) =>
    setRules(r => ({ ...r, margins: { ...r.margins, [side]: Number(val) } }));
  const setOrientation = o =>
    setRules(r => ({ ...r, orientation: o }));
  const setPageNumbers = v =>
    setRules(r => ({ ...r, pageNumbers: v }));

  const pickFile = f => {
    if (f?.name.endsWith('.docx')) { setFile(f); setErr(''); setStep('typography'); }
    else setErr('Please upload a .docx file.');
  };

  const handleDrop = e => {
    e.preventDefault(); setDrag(false);
    pickFile(e.dataTransfer.files[0]);
  };

  const handleFormat = async () => {
    if (!file) return;
    setLd(true); setErr('');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('rules', JSON.stringify(rules));
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/format`, fd, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDl(window.URL.createObjectURL(new Blob([res.data])));
      setStep('done');
    } catch (e) {
      setErr('Error connecting to backend on port 5000. Ensure it is running.');
      console.error(e);
    } finally { setLd(false); }
  };

  const reset = () => {
    setFile(null); setRules(DEFAULT_RULES);
    setStep('upload'); setDl(''); setErr('');
    if (fileRef.current) fileRef.current.value = '';
  };

  /* Render helpers */
  const navBtn = (label, to, isPrimary = true) => (
    <button className={`nav-btn ${isPrimary ? 'primary' : 'ghost'}`} onClick={() => setStep(to)}>
      {label} {isPrimary && <ChevronRight size={16} />}
    </button>
  );

  return (
    <div className="page">
      <div className="card">

        {/* ── Brand header ── */}
        <div className="brand">
          <div className="brand-icon"><FilePenLine size={22} /></div>
          <div>
            <h1 className="brand-title">DocFormatter Pro</h1>
            <p className="brand-sub">Professional document standardization</p>
          </div>
        </div>

        {/* ── Step bar ── */}
        {step !== 'done' && <StepBar step={step} />}

        {/* ── Error ── */}
        {error && <div className="alert-error">{error}</div>}

        {/* ══════════ STEP: Upload ══════════ */}
        {step === 'upload' && (
          <div
            className={`dropzone ${isDrag ? 'active' : ''}`}
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            <div className="dropzone-icon"><UploadCloud size={36} /></div>
            <p className="dropzone-title">Drag & drop your .docx file</p>
            <p className="dropzone-hint">or click to browse</p>
            <input type="file" accept=".docx" ref={fileRef} style={{ display: 'none' }}
              onChange={e => pickFile(e.target.files[0])} />
          </div>
        )}

        {/* ══════════ STEP: Typography ══════════ */}
        {step === 'typography' && (
          <div className="step-body">
            <div className="step-heading">
              <Type size={18} className="step-icon" />
              <h2>Typography</h2>
            </div>
            <div className="file-chip">
              <FileText size={18} /> <span>{file?.name}</span>
              <button className="chip-remove" onClick={reset}><X size={14} /></button>
            </div>
            <div className="type-grid">
              <TypographyCard badge="H1 Heading"    badgeClass="badge-h1"  typeKey="heading"    rules={rules} updateTypography={updateTypography} />
              <TypographyCard badge="H2 Subheading" badgeClass="badge-h2"  typeKey="subheading" rules={rules} updateTypography={updateTypography} />
              <TypographyCard badge="Body Text"     badgeClass="badge-p"   typeKey="paragraph"  rules={rules} updateTypography={updateTypography} />
              <TypographyCard badge="MCQ Question"  badgeClass="badge-mcq" typeKey="mcq"        rules={rules} updateTypography={updateTypography} />
              <TypographyCard badge="MCQ Option"    badgeClass="badge-opt" typeKey="option"     rules={rules} updateTypography={updateTypography} />
            </div>
            <div className="nav-row">
              {navBtn('Layout →', 'layout')}
            </div>
          </div>
        )}

        {/* ══════════ STEP: Layout ══════════ */}
        {step === 'layout' && (
          <div className="step-body">
            <div className="step-heading">
              <Layout size={18} className="step-icon" />
              <h2>Page Layout</h2>
            </div>

            <div className="section-block">
              <h3 className="section-label">Orientation</h3>
              <div className="orientation-row">
                {['portrait','landscape'].map(o => (
                  <button key={o} className={`orient-card ${rules.orientation === o ? 'active' : ''}`}
                    onClick={() => setOrientation(o)}>
                    <div className={`orient-preview ${o}`} />
                    <span>{o.charAt(0).toUpperCase() + o.slice(1)}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="section-block">
              <h3 className="section-label">Page Margins <small>(cm)</small></h3>
              <div className="margins-diagram">
                <div className="margin-control top-control">
                  <label>Top</label>
                  <input type="number" min="0" max="10" step="0.1"
                    value={rules.margins.top} onChange={e => updateMargin('top', e.target.value)} />
                </div>
                <div className="margin-middle-row">
                  <div className="margin-control">
                    <label>Left</label>
                    <input type="number" min="0" max="10" step="0.1"
                      value={rules.margins.left} onChange={e => updateMargin('left', e.target.value)} />
                  </div>
                  <div className="page-preview-box">
                    <div className="page-preview-inner">
                      <div className="page-line" /><div className="page-line" />
                      <div className="page-line short" />
                    </div>
                  </div>
                  <div className="margin-control">
                    <label>Right</label>
                    <input type="number" min="0" max="10" step="0.1"
                      value={rules.margins.right} onChange={e => updateMargin('right', e.target.value)} />
                  </div>
                </div>
                <div className="margin-control top-control">
                  <label>Bottom</label>
                  <input type="number" min="0" max="10" step="0.1"
                    value={rules.margins.bottom} onChange={e => updateMargin('bottom', e.target.value)} />
                </div>
              </div>
            </div>

            <div className="nav-row">
              <button className="nav-btn ghost" onClick={() => setStep('typography')}>← Back</button>
              {navBtn('Header & Footer →', 'header-footer')}
            </div>
          </div>
        )}

        {/* ══════════ STEP: Header & Footer ══════════ */}
        {step === 'header-footer' && (
          <div className="step-body">
            <div className="step-heading">
              <BookOpen size={18} className="step-icon" />
              <h2>Header, Footer & Page Numbers</h2>
            </div>

            <div className="section-block">
              <h3 className="section-label">Header Text</h3>
              <TextInput
                label="Appears at the top of every page"
                placeholder="e.g., My Document Title / Company Name"
                value={rules.headerText}
                onChange={v => setRules(r => ({ ...r, headerText: v }))}
              />
            </div>

            <div className="section-block">
              <h3 className="section-label">Footer Text</h3>
              <TextInput
                label="Appears at the bottom of every page"
                placeholder="e.g., Confidential / © 2025"
                value={rules.footerText}
                onChange={v => setRules(r => ({ ...r, footerText: v }))}
              />
            </div>

            <div className="section-block">
              <h3 className="section-label"><Hash size={14} /> Page Numbers</h3>
              <div className="page-num-row">
                {[
                  { value: 'none',   label: 'None' },
                  { value: 'top',    label: 'Top (Header)' },
                  { value: 'bottom', label: 'Bottom (Footer)' },
                ].map(opt => (
                  <button key={opt.value}
                    className={`page-num-btn ${rules.pageNumbers === opt.value ? 'active' : ''}`}
                    onClick={() => setPageNumbers(opt.value)}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="nav-row">
              <button className="nav-btn ghost" onClick={() => setStep('layout')}>← Back</button>
              {navBtn('Review →', 'review')}
            </div>
          </div>
        )}

        {/* ══════════ STEP: Review ══════════ */}
        {step === 'review' && (
          <div className="step-body">
            <div className="step-heading">
              <AlignLeft size={18} className="step-icon" />
              <h2>Review & Format</h2>
            </div>

            <div className="review-grid">
              <div className="review-card">
                <div className="review-card-title">Typography</div>
                {[
                  ['Heading',    rules.heading],
                  ['Subheading', rules.subheading],
                  ['Body Text',  rules.paragraph],
                  ['MCQ Q',      rules.mcq],
                  ['MCQ Opt',    rules.option],
                ].map(([label, r]) => (
                  <div className="review-row" key={label}>
                    <span className="review-key">{label}</span>
                    <span className="review-val">{r.size}pt {r.bold ? '· Bold' : ''}</span>
                  </div>
                ))}
              </div>
              <div className="review-card">
                <div className="review-card-title">Layout</div>
                <div className="review-row"><span className="review-key">Orientation</span><span className="review-val">{rules.orientation}</span></div>
                <div className="review-row"><span className="review-key">Top</span><span className="review-val">{rules.margins.top} cm</span></div>
                <div className="review-row"><span className="review-key">Bottom</span><span className="review-val">{rules.margins.bottom} cm</span></div>
                <div className="review-row"><span className="review-key">Left</span><span className="review-val">{rules.margins.left} cm</span></div>
                <div className="review-row"><span className="review-key">Right</span><span className="review-val">{rules.margins.right} cm</span></div>
              </div>
              <div className="review-card">
                <div className="review-card-title">Header / Footer</div>
                <div className="review-row"><span className="review-key">Header</span><span className="review-val">{rules.headerText || '—'}</span></div>
                <div className="review-row"><span className="review-key">Footer</span><span className="review-val">{rules.footerText || '—'}</span></div>
                <div className="review-row"><span className="review-key">Page #</span><span className="review-val">{rules.pageNumbers}</span></div>
              </div>
            </div>

            <div className="nav-row">
              <button className="nav-btn ghost" onClick={() => setStep('header-footer')}>← Back</button>
              <button className="nav-btn primary" onClick={handleFormat} disabled={loading}>
                {loading ? <><Loader2 size={16} className="spin" /> Formatting…</> : <>Format Document <ChevronRight size={16} /></>}
              </button>
            </div>
          </div>
        )}

        {/* ══════════ STEP: Done ══════════ */}
        {step === 'done' && (
          <div className="done-state">
            <div className="done-circle"><CheckCircle size={40} /></div>
            <h2 className="done-title">Formatted Successfully!</h2>
            <p className="done-hint">Your document is ready to download.</p>
            <div className="done-actions">
              <a href={dlUrl} download={`formatted_${file?.name}`} className="nav-btn primary" style={{ textDecoration: 'none' }}>
                <Download size={16} /> Download
              </a>
              <button className="nav-btn ghost" onClick={reset}>Format Another</button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
