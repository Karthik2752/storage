import { jsPDF } from "jspdf";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [knowledgeStats, setKnowledgeStats] = useState({documents: 0,chunks: 0,});
  const [knowledgeDocuments, setKnowledgeDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const deleteDocument = async (filename) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${filename}"?`);
    if (!confirmed) {
      return;
    }
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/knowledge/documents/${encodeURIComponent(
          filename)}`,
        {
          method: "DELETE",
        });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to delete PDF.");
      }
      await refreshKnowledgeBase();
      setUploadMessage(data.message || "PDF deleted successfully.");
    } catch (error) {
      console.error("Delete PDF error:", error);
      alert(error.message || "Failed to delete PDF.");
    }
  };
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState("");
  const [researchData, setResearchData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeNav, setActiveNav] = useState("Dashboard");
  const [activeAgent, setActiveAgent] = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [stats, setStats] = useState({researchTasks: 0,reportsGenerated: 0,sourcesAnalyzed: 0,});
  const dashboardRef = useRef(null);
  const researchRef = useRef(null);
  const reportRef = useRef(null);
  const knowledgeRef = useRef(null);

  const loadKnowledgeStats = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/knowledge/stats");
      if (!response.ok) {
        throw new Error("Unable to load knowledge statistics");
      }
      const data = await response.json();
      setKnowledgeStats({documents: data.documents || 0,chunks: data.chunks || 0,});
    } catch (error) {
      console.error("Knowledge Base stats error:",error);
    }
  };

  const loadKnowledgeDocuments = async () => {
    setLoadingDocuments(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/knowledge/documents");
      if (!response.ok) {
        throw new Error("Unable to load knowledge documents");
      }
      const data = await response.json();
      setKnowledgeDocuments(data.documents || []);
    } catch (error) {
      console.error("Knowledge Base documents error:",error);
      setKnowledgeDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };
  useEffect(() => {loadKnowledgeStats();
    loadKnowledgeDocuments();}, []);
  const refreshKnowledgeBase = async () => {
    await Promise.all([loadKnowledgeStats(),loadKnowledgeDocuments(),]);
  };
  const uploadPdf = async () => {
    if (!selectedFile) {
      setUploadMessage("Please select a PDF document first.");
      return;
    }
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setUploadMessage("Please select a PDF file only.");
      return;
    }
    const maxSize = 15 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      setUploadMessage("File size must be 15 MB or smaller.");
      return;
    }
    setUploading(true);
    setUploadMessage("");
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const response = await fetch("http://127.0.0.1:8000/api/knowledge/upload",
        {
          method: "POST",
          body: formData,
        }
      );
      const data = await response.json();
      if (!response.ok || data.status === "error") {
        throw new Error(data.message || "PDF upload failed.");
      }
      setUploadMessage(data.message || "PDF uploaded and indexed successfully.");
      setSelectedFile(null);
      await refreshKnowledgeBase();
    } catch (error) {
      console.error("PDF upload error:",error);
      setUploadMessage(error.message || "Unable to upload PDF.");
    } finally {
      setUploading(false);
    }
  };
  const handleNavigation = (section) => {
    setActiveNav(section);
    if (section === "Dashboard") {
      dashboardRef.current?.scrollIntoView({behavior: "smooth",});
    }
    if (section === "Research") {researchRef.current?.scrollIntoView({behavior: "smooth",});
      setTimeout(() => {document.getElementById("research-input") ?.focus();}, 500);
    }
    if (section === "Reports") {
      reportRef.current?.scrollIntoView({behavior: "smooth",});
    }
    if (section === "Knowledge Base") {
      knowledgeRef.current?.scrollIntoView({ behavior: "smooth",});
    }
  };
const downloadReport = () => {
  if (!result) return;

  const doc = new jsPDF({orientation: "portrait",unit: "mm",format: "a4",});
  const pageWidth = 210;
  const pageHeight = 297;
  const margin = 22;
  const contentWidth = pageWidth - margin * 2;
  const footerY = pageHeight - 14;

  let y = 25;
  const colors = {
    navy: [25, 43, 75],blue: [45, 91, 160],
    text: [48, 55, 65],muted: [110, 118, 130],light: [225, 231, 239],
  };

  const cleanedMarkdown = cleanReportContent(result);

  const lines = cleanedMarkdown.split(/\r?\n/).map((line) =>line.replace(/^\s*\\(?=[#*_\-\d.>])/g, "").trimEnd());
  const cleanInline = (text) =>
    text
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, "$1 — $2")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/__(.*?)__/g, "$1")
      .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "$1")
      .replace(/`([^`]+)`/g, "$1").replace(/\\([*_#])/g, "$1").trim();

  const addPageHeader = () => {
    doc.setDrawColor(...colors.light);
    doc.setLineWidth(0.3);
    doc.line(margin, 17, pageWidth - margin, 17);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...colors.muted);

    doc.text("AGENTFLOW  |  RESEARCH REPORT", margin, 13);
  };

  const addPage = () => {
    doc.addPage();y = 27;addPageHeader();
  };

  const ensureSpace = (height) => {
    if (y + height > footerY - 5) {addPage();
    }
  };

  const addParagraph = (text, options = {}) => {
    const {
      fontSize = 10,indent = 0,
      color = colors.text,fontStyle = "normal",gapAfter = 4,
    } = options;

    const content = cleanInline(text);
    if (!content) return;
    doc.setFont("helvetica", fontStyle);
    doc.setFontSize(fontSize);
    doc.setTextColor(...color);

    const availableWidth = contentWidth - indent;
    const wrapped = doc.splitTextToSize(content,availableWidth);
    const lineHeight = fontSize * 0.48;
    ensureSpace(wrapped.length * lineHeight + gapAfter);
    doc.text(wrapped, margin + indent, y);
    y += wrapped.length * lineHeight + gapAfter;
  };

  doc.setFillColor(...colors.navy);
  doc.rect(0, 0, pageWidth, 105, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("A G E N T F L O W", margin, 35);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.text("AUTONOMOUS AI RESEARCH PLATFORM", margin, 45);
  doc.setDrawColor(120, 165, 225);
  doc.setLineWidth(1);
  doc.line(margin, 57, margin + 35, 57);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(27);
  doc.text("RESEARCH", margin, 76);
  doc.text("REPORT", margin, 88);
  doc.setTextColor(...colors.navy);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text("RESEARCH TOPIC", margin, 127);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(13);

  const topicLines = doc.splitTextToSize(question.trim() || "AI Research and Analysis",contentWidth);
  doc.text(topicLines, margin, 138);

  const topicBottom = 138 + topicLines.length * 7;
  doc.setDrawColor(...colors.light);
  doc.line(margin,topicBottom + 7,pageWidth - margin,topicBottom + 7);

  doc.setFontSize(10);
  doc.setTextColor(...colors.muted);
  doc.text("Prepared by AgentFlow Multi-Agent Research System",margin,topicBottom + 20);

  doc.text(
    `Generated: ${new Date().toLocaleDateString("en-IN", {
      day: "2-digit",month: "long",year: "numeric",})}`,
    margin,topicBottom + 28);
  doc.setFontSize(9);
  doc.text("Planner  |  Researcher  |  Data Analyst  |  Critic  |  Writer",margin,270);

  doc.addPage();
  y = 27;
  addPageHeader();

  for (const originalLine of lines) {
    const line = originalLine.trim();

    if (!line) {
      y += 2;
      continue;
    }
    if (/^#\s+research report$/i.test(line)) {
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const title = cleanInline(heading[2]);
      if (level === 1) {
        ensureSpace(15);
        y += 3;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(19);
        doc.setTextColor(...colors.navy);
        const wrapped = doc.splitTextToSize(title,contentWidth);
        doc.text(wrapped, margin, y);
        y += wrapped.length * 9 + 4;

        doc.setDrawColor(...colors.blue);
        doc.setLineWidth(0.8);
        doc.line(margin, y - 1, margin + 28, y - 1);
        y += 5;
      } else if (level === 2) {
        ensureSpace(16);
        y += 3;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.setTextColor(...colors.blue);
        const wrapped = doc.splitTextToSize(title,contentWidth);
        doc.text(wrapped, margin, y);
        y += wrapped.length * 7 + 3;
      } else {
        addParagraph(title, {
          fontSize: 11,fontStyle: "bold",
          color: colors.navy,gapAfter: 3,});
      }
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);

    if (bullet) {
      addParagraph(`• ${cleanInline(bullet[1])}`, {
        indent: 3,fontSize: 9.5,gapAfter: 3,});
      continue;
    }
    const numbered = line.match(/^(\d+)\.\s+(.+)$/);

    if (numbered) {
      addParagraph(`${numbered[1]}. ${cleanInline(numbered[2])}`,
        {indent: 3,fontSize: 9.5,gapAfter: 3,});
      continue;
    }
    addParagraph(line, {
      fontSize: 10,gapAfter: 4,
    });
  }
  const totalPages = doc.getNumberOfPages();
  for (let page = 1; page <= totalPages; page++) {
    doc.setPage(page);
    doc.setDrawColor(...colors.light);
    doc.setLineWidth(0.3);
    doc.line(margin, footerY, pageWidth - margin, footerY);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...colors.muted);
    doc.text("AgentFlow | AI Research Platform", margin, footerY + 6);
    doc.text(`Page ${page} of ${totalPages}`,pageWidth - margin,footerY + 6,{ align: "right" });
  }
  
  doc.save("AgentFlow_Research_Report.pdf");
};
  const getSectionNumber = (title) => {
    const sections = {
      "Executive Summary": "01",
      Introduction: "02",
      "Key Findings": "03",
      "Detailed Analysis": "04",
      "Benefits and Opportunities": "05",
      "Risks and Challenges": "06",
      "Evidence Assessment": "07",
      Conclusion: "08",
      Sources: "09",
      References: "09",
      "Sources & References": "09",
    };
    return sections[title] || "";
  };
  const cleanReportContent = (markdown) => {
    if (!markdown) return markdown;

    let cleaned = markdown
    cleaned = cleaned.replace(
      /(?:\*\*)?WHY THIS SECTION MATTERS(?:\*\*)?\s*(?:\r?\n)+\s*(?:\*\*)?[^\r\n]+(?:\*\*)?/gi,"");
  
    const descriptions = [
      "A concise overview of the research question, major findings, and overall conclusion.",
      "Context and background required to understand the research topic.",
      "The most important findings identified from the available evidence.",
      "Detailed interpretation and synthesis of the collected research evidence.",
      "Potential advantages, applications, and opportunities identified by the research.",
      "Important limitations, risks, uncertainties, and challenges associated with the topic.",
      "Assessment of the quality, coverage, and limitations of the evidence used.",
      "The final interpretation of the research findings.",
      "External web sources used to support the research.",
    ];
    descriptions.forEach((description) => {
      const escapedDescription =description.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");

      cleaned = cleaned.replace(
        new RegExp(escapedDescription,"gi"),"");
    });
    return cleaned;
  };

  const cleanReportSources = (markdown) => {
    if (!markdown) return markdown;

    const lines = markdown.split("\n");

    const sourceHeadingIndex =
      lines.findIndex((line) => {
        const normalized = line.trim().replace(/^#+\s*/, "")
          .replace(/\*\*/g, "").toLowerCase();

        return (
          normalized === "sources" || normalized === "references" || normalized ==="sources & references");
      });

    if (sourceHeadingIndex === -1) {
      return markdown;
    }

    const beforeSources = lines.slice(0,sourceHeadingIndex + 1);
    const sourceLines = lines.slice(sourceHeadingIndex + 1);
    const cleanedSourceLines = [];
    let currentEntry = [];

    const flushEntry = () => {
      if (currentEntry.length === 0) {
        return;
      }

      const entryText = currentEntry.join("\n").toLowerCase();
      const isKnowledgeBaseSource =
        entryText.includes("document://") || entryText.includes("test_document.pdf") ||
        entryText.includes("agentflow_sample_ai_cybersecurity.pdf") ||
        entryText.includes("agentflow_sample_ai_cybersecurity");

      if (!isKnowledgeBaseSource) {
        cleanedSourceLines.push(...currentEntry);
      }
      currentEntry = [];
    };
    sourceLines.forEach((line) => {
      const isNewNumberedEntry =/^\s*(?:\*\*)?\d+(?:\*\*)?\.\s+/.test(line);
      if (isNewNumberedEntry) {
        flushEntry();
        currentEntry.push(line);
      } else {
        currentEntry.push(line);
      }
    });
    flushEntry();
    let sourceNumber = 0;
    const renumberedLines =cleanedSourceLines.map((line) => {
        const match = line.match(/^(\s*)(?:\*\*)?\d+(?:\*\*)?\.\s+(.*)$/);
        if (!match) {
          return line;
        }
        sourceNumber += 1;
        return `${match[1]}${sourceNumber}. ${match[2]}`;
      });
    return [...beforeSources,...renumberedLines,].join("\n");
  };
  const startResearch = async () => {
    if (!question.trim()) {
      setResult("Please enter a research question.");
      return;
    }

    setLoading(true);
    setResult("");
    setResearchData(null);

    setActiveAgent("Planner");
    setCompletedAgents([]);

    try {
      setTimeout(() => {
        setCompletedAgents(["Planner"]);
        setActiveAgent("Researcher");
      }, 1200);

      setTimeout(() => {
        setCompletedAgents(["Planner","Researcher",]);
        setActiveAgent("Data Analyst");}, 3000);

      setTimeout(() => {
        setCompletedAgents(["Planner","Researcher","Data Analyst",]);
        setActiveAgent("Critic");}, 4500);

      setTimeout(() => {
        setCompletedAgents(["Planner","Researcher","Data Analyst","Critic",]);
        setActiveAgent("Writer");
      }, 6000);
      const response = await fetch(
        "http://127.0.0.1:8000/api/research",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            question: question,
          }),
        });
      const data = await response.json();
      if (!response.ok || data.status === "error") {
        throw new Error(data.message || "Research request failed");
      }
      setActiveAgent(null);
      setCompletedAgents(["Planner","Researcher","Data Analyst","Critic","Writer",]);
      setResearchData(data);
      setResult(data.report);
      setStats((previous) => ({
        researchTasks:previous.researchTasks + 1,
        reportsGenerated:previous.reportsGenerated + 1,
        sourcesAnalyzed: data.sources ? data.sources.length: 0,}));
      setTimeout(() => {
        reportRef.current?.scrollIntoView({behavior: "smooth",});
      }, 300);
    } catch (error) {
      console.error("Research error:",error);
      setActiveAgent(null);
      setResult(error.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };
  const getAgentStatus = (agentName) => {
    if (activeAgent === agentName) {
      return "Running";
    }
    if (completedAgents.includes(agentName)) {
      return "Completed";
    }
    return "Waiting";
  };
  const getAgentClass = (agentName) => {
    if (activeAgent === agentName) {
      return "agent-card running";
    }
    if (completedAgents.includes(agentName)){
      return "agent-card completed";
    }
    return "agent-card";
  };

const cleanedResult =cleanReportContent(cleanReportSources(result));
  return (
    <div className="app"ref={dashboardRef}>
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">A</div>
          <div>
            <h2>AgentFlow</h2>
            <span>AI Research Platform</span>
          </div>
        </div>
        <nav>
          <a className={
              activeNav === "Dashboard" ? "active": ""
            }
            onClick={() =>handleNavigation("Dashboard")
            }>Dashboard</a>
          <a className={activeNav === "Research" ? "active" : ""}
            onClick={() => handleNavigation("Research")}>Research</a>
          <a className={
              activeNav === "Reports" ? "active": ""
            }
            onClick={() =>handleNavigation("Reports")
            }>Reports</a>
          <a className={
              activeNav === "Knowledge Base" ? "active": ""
            }onClick={() =>handleNavigation("Knowledge Base")}>Knowledge Base</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot"></span>
            System Online</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>Research Dashboard</h1>
            <p>Autonomous multi-agent research and analysis</p>
          </div>
          <div className="header-right">
            <span className="backend-badge">
              <span className="status-dot"></span>Backend Connected</span>
          </div>
        </header>
        <section
          className="research-card"
          ref={researchRef}>
          <div className="section-label">
            NEW RESEARCH TASK
          </div>
          <h2>What would you like to research?</h2>
          <p className="description">
            AgentFlow will coordinate multiple AI agents to research, analyze,verify, and generate a structuredresearch report.</p>
          <div className="search-box">
            <input id="research-input" type="text" value={question}
              onChange={(event) => setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  startResearch();
                }
              }}
              placeholder="Example: Analyze the impact of AI on cybersecurity..."disabled={loading}/>
            <button
              onClick={startResearch}
              disabled={loading}>
              {loading ? "Researching...": "Start Research"}
              <span>→</span>
            </button>
          </div>
          {result && (
            <div className="result-message" ref={reportRef}>
              <div className="report-header">
                <div className="report-title-area">
                  <div className="report-icon">
                    ✦
                  </div>
                  <div>
                    <h3>Research Report</h3>
                    <span className="result-subtitle">Generated by AgentFlow</span>
                  </div>
                </div>
                <div className="report-actions">
                  <span className="report-status">
                    <span className="status-dot"></span>
                    {loading ? "Researching..." : "Research Complete"}
                  </span>
                  <button type="button"
                    className="download-report-btn"
                    onClick={
                      downloadReport
                    }disabled={loading}>↓ Download Report</button>
                </div>
              </div>
              <div className="report-content">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => (
                      <div className="report-main-title">
                        <div className="report-title-label">
                          AGENTFLOW RESEARCH REPORT</div>
                        <h1>{children}</h1>
                        <div className="report-title-line"></div></div>),
                    h2: ({ children }) => {
                      const title =String(children).replace(/\s+/g, " ").trim();
                      const sectionNumber =getSectionNumber(title);
                      return (
                        <div className="report-section">
                          <div className="report-section-heading">
                            <div className="report-section-number">
                              {sectionNumber}
                            </div>
                            <div className="report-section-title">
                              <span className="report-section-label">
                                SECTION{" "}
                                {sectionNumber}
                              </span>
                              <h2>{children}</h2>
                            </div>
                          </div>
                        </div>
                      );
                    },
                    h3: ({ children }) => (<h3 className="report-subheading">{children}</h3>),
                    p: ({ children }) => (<p className="report-paragraph">{children}</p>),
                    ul: ({ children }) => (<ul className="report-list">{children}</ul>),
                    ol: ({ children }) => (<ol className="report-numbered-list">{children}</ol>),
                    li: ({ children }) => (<li>{children}</li>),
                    strong: ({ children }) => (
                      <strong className="report-highlight">{children}
                      </strong>),
                    a: ({href, children,
                    }) => (<a href={href} target="_blank" rel="noopener noreferrer" className="report-link">{children}</a>),
                    blockquote: ({
                      children,}) => (<blockquote className="report-quote">
                        {children}</blockquote>),
                    code: ({ children }) => (<code className="report-code">{children}</code>),
                  }}>
                  {cleanedResult}
                </ReactMarkdown>
              </div>
            </div>)}
        </section>
        <section className="workflow-section">
          <div className="section-heading">
            <div>
              <h2>Agent Workflow</h2>
              <p>Multi-agent execution pipeline</p>
            </div>
            <span className="waiting-badge">
              {loading ? `Running: ${ activeAgent || "Starting" }` : completedAgents.length === 5 ? "Completed" : "Ready"}</span>
          </div>
          <div className="workflow">
            <div className={getAgentClass("Planner")}>
              <div className="agent-number">01</div>
              <div className="agent-icon">P</div>
              <h3>Planner</h3>
              <p> Breaks the research question into tasks. </p>
              <span className="agent-status">
                {getAgentStatus("Planner")}</span>
            </div>
            <div className="arrow"> → </div>
            <div className={getAgentClass("Researcher")}>
              <div className="agent-number">02</div>
              <div className="agent-icon">R</div>
              <h3>Researcher</h3>
              <p>Collects information from web and documents.</p>
              <span className="agent-status">
                {getAgentStatus("Researcher")}</span>
            </div>
            <div className="arrow">→</div>
            <div className={getAgentClass("Data Analyst")}>
              <div className="agent-number">03</div>
              <div className="agent-icon">D</div>
              <h3>Data Analyst</h3>
              <p>Analyzes data and generates insights.</p>
              <span className="agent-status">
                {getAgentStatus("Data Analyst")}</span>
            </div>
            <div className="arrow">→</div>
            <div className={getAgentClass("Critic")}>
              <div className="agent-number">04</div>
              <div className="agent-icon">C</div>
              <h3>Critic</h3>
              <p>Checks evidence and identifies inconsistencies.</p>
              <span className="agent-status">
                {getAgentStatus("Critic")}</span>
            </div>
            <div className="arrow">→</div>
            <div
              className={getAgentClass("Writer")}>
              <div className="agent-number">05</div>
              <div className="agent-icon">W</div>
              <h3>Writer</h3>
              <p>Creates the final structured research report.</p>
              <span className="agent-status">
                {getAgentStatus("Writer")}</span>
            </div>
          </div>
        </section>
        <section ref={knowledgeRef} className="knowledge-placeholder">
          <div className="section-heading">
            <div>
              <h2>Knowledge Base</h2>
              <p>Upload PDFs for document-grounded research</p>
            </div>
            <button type="button"onClick={refreshKnowledgeBase}
              disabled={uploading ||loadingDocuments}>
              {loadingDocuments ? "Refreshing...": "Refresh"}
            </button>
          </div>
          <div className="knowledge-stats">
            <div className="stat-card">
              <span>Indexed Documents</span>
              <strong>
                {knowledgeStats.documents}
              </strong>
            </div>
            <div className="stat-card">
              <span>Stored Text Chunks</span>
              <strong>{knowledgeStats.chunks}</strong>
            </div>
          </div>
          <div className="pdf-upload-area">
            <label htmlFor="pdf-upload-input">Choose a PDF document</label>
            <input id="pdf-upload-input"type="file"
              accept=".pdf,application/pdf" onChange={(event) =>setSelectedFile(event.target.files?.[0] ||null)
              }disabled={uploading}/>
            {selectedFile && (
              <p>Selected:{" "}{selectedFile.name}</p>)}
            <button type="button" onClick={uploadPdf}
              disabled={ uploading || !selectedFile}>
              {uploading ? "Indexing PDF..." : "Upload and Index PDF"}
            </button>
            {uploadMessage && (<p className="upload-message" role="status">{uploadMessage}</p>)}
            <small>PDF files only · Maximum size: 15 MB</small>
          </div>
          <div className="knowledge-documents">
            <div className="knowledge-documents-header">
              <div>
                <h3>Uploaded Documents</h3>
                <p>PDFs currently indexed in the knowledge base</p>
              </div>
              <button type="button" onClick={
                  loadKnowledgeDocuments
                }
                disabled={loadingDocuments}>
                {loadingDocuments ? "Refreshing..." : "Refresh List"}
              </button>
            </div>
            {loadingDocuments ? (
              <p className="knowledge-empty">
                Loading documents...
              </p>) : knowledgeDocuments.length === 0 ? (
              <p className="knowledge-empty"> No PDF documents uploaded yet. </p>) : (
              <div className="knowledge-document-list">
                {knowledgeDocuments.map((document) => (
                    <div className="knowledge-document" key={document.filename}>
                      <div className="knowledge-document-info">
                        <div className="pdf-icon">PDF</div>
                        <div>
                          <div className="knowledge-document-name">
                            {
                              document.filename
                            }
                          </div>
                          <div className="knowledge-document-chunks">
                            {
                              document.chunks
                            }{" "}
                            {document.chunks === 1? "chunk": "chunks"}</div></div>
                      </div>
                      <button type="button"onClick={() => deleteDocument(document.filename)}>Delete</button>
                    </div>))}</div>)}
          </div>
        </section>

        {/* DYNAMIC STATISTICS */}
        <section className="stats-grid">
          <div className="stat-card">
            <span>Research Tasks</span>
            <strong>
              {stats.researchTasks}
            </strong>
            <small>Total tasks completed</small>
          </div>
          <div className="stat-card">
            <span>Reports Generated</span>
            <strong>
              {stats.reportsGenerated}
            </strong>
            <small>AI-generated reports</small>
          </div>
          <div className="stat-card">
            <span>Sources Analyzed</span>
            <strong>{stats.sourcesAnalyzed}</strong>
            <small>Web + document sources</small>
          </div>
          <div className="stat-card">
            <span>Knowledge Base</span>
            <strong>
              {knowledgeStats.documents}
            </strong><small>Indexed documents</small>
          </div>
        </section>
      </main>
    </div>);
}

export default App;

