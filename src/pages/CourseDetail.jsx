


function CourseDetail() {
  // const { id } = useParams();


  const resources = [
    { id: 1, name: "Day 01 - Introduction.pdf" },
    { id: 2, name: "Day 02 - Basics.pdf" },
    { id: 3, name: "Assignment 01.pdf" },
  ];

  return (
    <div className="course-detail-page">
      <h2>Python Course</h2>

      <div className="course-layout">
        {/* LEFT SIDE */}
        <div className="pdf-viewer">
          <p>Select a PDF to view</p>
        </div>

        {/* RIGHT SIDE */}
        <div className="course-side">
          <h3>Your Progress</h3>
          <div className="progress-box">0%</div>

          <h3>Resources</h3>
          <ul className="resource-list">
            {resources.map(r => (
              <li key={r.id}>📄 {r.name}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default CourseDetail;
