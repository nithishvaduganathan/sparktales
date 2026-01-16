import { useState } from "react";
import ChatBot from "../components/ChatBot";


function CourseDetail() {
  const [selectedPdf, setSelectedPdf] = useState(null);

  const resources = [
    { id: 1, name: "Day 01 - Introduction.pdf", file: "/pdfs/day01.pdf" },
    { id: 2, name: "Day 02 - Basics.pdf", file: "/pdfs/day02.pdf" },
    { id: 3, name: "Assignment 01.pdf", file: "/pdfs/assignment01.pdf" },
  ];

  return (
    <div className="course-detail-page">
      {/* ===== HEADER ===== */}
      <div className="course-header">
        <h2>Python</h2>
      </div>

      <div className="course-layout">
        {/* ================= LEFT SIDE (PDF VIEWER) ================= */}
        <div className="pdf-viewer">
          {!selectedPdf ? (
            <p>Select a PDF from the right to view</p>
          ) : (
            <iframe
              src={selectedPdf}
              title="PDF Viewer"
              className="pdf-frame"
            />
          )}
        </div>

        {/* ================= RIGHT SIDE (PROGRESS + RESOURCES) ================= */}
        <div className="course-side">
          <h3>Your Progress</h3>
          <div className="progress-box">70%</div>

          <h3>Resources</h3>
          <ul className="resource-list">
            {resources.map((r) => (
              <li key={r.id} onClick={() => setSelectedPdf(r.file)}>
                📄 {r.name}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ================= AI ASSISTANT (BOTTOM) ================= */}
      <ChatBot/>
    </div>
  );
}

export default CourseDetail;
