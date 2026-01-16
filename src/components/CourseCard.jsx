import { useNavigate } from "react-router-dom";

function CourseCard({ id, title, description, progress, image }) {
  const navigate = useNavigate();

  return (
    <div className="course-card" onClick={() => navigate(`/course/${id}`)}>
      {/* TOP GRADIENT */}
      <div className={`course-top`}>
        <img src={image} alt={title} className="course-image" />
      </div>

      {/* BODY */}
      <div className="course-body">
        <h3>{title}</h3>
        <p>{description}</p>

        {/* progress bar */}
        <div className="progress-container">
          <div
            className={`progress-line`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        <div className="course-footer">
          <span className="progress-text">Progress</span>
          <span className="progress-percent">{progress}%</span>
        </div>
      </div>
    </div>
  );
}

export default CourseCard;